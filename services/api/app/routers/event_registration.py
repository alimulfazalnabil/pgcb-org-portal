from datetime import datetime
import hashlib
import hmac
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import current_user
from app.core.rate_limit import client_key, limiter
from app.db.session import get_db
from app.models import Event, EventRegistration, User
from app.integrations.notifications import create_in_app, deliver_email, record_delivery
from app.domain.notifications import queue_delivery
from app.schemas.events import EventRegistrationCreate, EventRegistrationResponse

router = APIRouter(prefix='/events', tags=['events'])


def ticket_signature(ticket_code: str) -> str:
    return hmac.new(settings.jwt_secret.encode(), ticket_code.encode(), hashlib.sha256).hexdigest()[:32]


def _rate_limit(request: Request) -> None:
    if settings.rate_limit_enabled:
        limiter.check(client_key(request, 'event-registration'), 12, 600)


def _token(registration: EventRegistration) -> str:
    return f'{registration.ticket_code}.{ticket_signature(registration.ticket_code)}'


def _response(item: EventRegistration) -> EventRegistrationResponse:
    return EventRegistrationResponse(id=item.id, event_id=item.event_id, name=item.name, email=item.email, phone=item.phone, organization=item.organization, ticket_code=item.ticket_code, ticket_token=_token(item), registration_status=item.registration_status, attendance_status=item.attendance_status, payment_status=item.payment_status, registered_at=item.registered_at)


def _register(event: Event, payload: EventRegistrationCreate, db: Session, user_id: int | None = None) -> EventRegistration:
    now = datetime.utcnow()
    if event.registration_deadline and event.registration_deadline < now:
        raise HTTPException(409, 'Registration deadline has passed')
    email = payload.email.lower().strip()
    existing = db.scalar(select(EventRegistration).where(EventRegistration.event_id == event.id, EventRegistration.email == email))
    if existing and existing.registration_status not in {'CANCELLED'}:
        raise HTTPException(409, 'This email is already registered for the event')
    if event.capacity:
        active_count = db.scalar(select(func.count(EventRegistration.id)).where(EventRegistration.event_id == event.id, EventRegistration.registration_status.in_(['REGISTERED', 'CONFIRMED']))) or 0
        status = 'WAITLISTED' if active_count >= event.capacity else 'REGISTERED'
    else:
        status = 'REGISTERED'
    payment_status = 'REQUIRED' if event.fee_amount else 'NOT_REQUIRED'
    if existing:
        item = existing
        item.name = payload.name; item.phone = payload.phone; item.organization = payload.organization; item.registration_status = status; item.payment_status = payment_status; item.user_id = user_id or item.user_id; item.ticket_code = secrets.token_urlsafe(12)
    else:
        item = EventRegistration(event_id=event.id, user_id=user_id, name=payload.name, email=email, phone=payload.phone, organization=payload.organization, ticket_code=secrets.token_urlsafe(12), registration_status=status, payment_status=payment_status)
        db.add(item)
    db.commit(); db.refresh(item)
    return item


@router.post('/{event_id}/registrations', response_model=EventRegistrationResponse)
def register_event(event_id: int, payload: EventRegistrationCreate, request: Request, db: Session = Depends(get_db)):
    _rate_limit(request)
    event = db.scalar(select(Event).where(Event.id == event_id, Event.is_published == True))
    if not event: raise HTTPException(404, 'Event not found')
    if not event.registration_enabled: raise HTTPException(409, 'Registration is closed for this event')
    item = _register(event, payload, db)
    queue_delivery(db, None, 'EMAIL', item.email)
    db.commit()
    return _response(item)

@router.post('/{event_id}/registrations/member', response_model=EventRegistrationResponse)
def register_event_member(event_id: int, payload: EventRegistrationCreate, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _rate_limit(request)
    event = db.scalar(select(Event).where(Event.id == event_id, Event.is_published == True))
    if not event: raise HTTPException(404, 'Event not found')
    if not event.registration_enabled: raise HTTPException(409, 'Registration is closed for this event')
    payload.email = user.email
    payload.name = user.name_bn
    payload.phone = payload.phone or user.phone
    item = _register(event, payload, db, user.id)
    notification = create_in_app(db, user, 'ইভেন্ট নিবন্ধন সফল', f'{event.title_bn} — Ticket: {item.ticket_code}', 'EVENT')
    queue_delivery(db, notification.id, 'EMAIL', item.email)
    db.commit()
    return _response(item)


@router.get('/registrations/{ticket_token}')
def verify_ticket(ticket_token: str, db: Session = Depends(get_db)):
    try:
        ticket_code, signature = ticket_token.rsplit('.', 1)
    except ValueError:
        raise HTTPException(400, 'Invalid ticket token')
    if not hmac.compare_digest(ticket_signature(ticket_code), signature):
        raise HTTPException(400, 'Invalid ticket token')
    item = db.scalar(select(EventRegistration).where(EventRegistration.ticket_code == ticket_code))
    if not item:
        raise HTTPException(404, 'Ticket not found')
    event = db.get(Event, item.event_id)
    return {'valid': True, 'ticket_code': item.ticket_code, 'name': item.name, 'organization': item.organization, 'registration_status': item.registration_status, 'attendance_status': item.attendance_status, 'payment_status': item.payment_status, 'event': {'id': event.id, 'title_bn': event.title_bn, 'event_date': event.event_date, 'location_bn': event.location_bn} if event else None}


@router.get('/registrations/me')
def my_event_registrations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(EventRegistration).where(EventRegistration.user_id == user.id, EventRegistration.registration_status != 'CANCELLED').order_by(EventRegistration.registered_at.desc())).all()
    return [{'id': r.id, 'event_id': r.event_id, 'name': r.name, 'email': r.email, 'ticket_code': r.ticket_code, 'ticket_token': _token(r), 'registration_status': r.registration_status, 'attendance_status': r.attendance_status, 'payment_status': r.payment_status, 'registered_at': r.registered_at} for r in rows]

@router.get('/registrations/{ticket_token}/qr')
def ticket_qr(ticket_token: str, db: Session = Depends(get_db)):
    # Validate before generating an image from a ticket token.
    verify_ticket(ticket_token, db)
    try:
        import io
        import qrcode
        from fastapi.responses import StreamingResponse
        image = qrcode.make(ticket_token)
        buf = io.BytesIO()
        image.save(buf, format='PNG')
        buf.seek(0)
        return StreamingResponse(buf, media_type='image/png', headers={'Cache-Control': 'no-store'})
    except Exception as exc:
        raise HTTPException(503, 'QR generation unavailable') from exc
