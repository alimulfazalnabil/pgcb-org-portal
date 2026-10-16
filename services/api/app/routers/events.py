"""
Member Events Center Router for PGCB Organization Portal.
Supports discovery, multi-tab filtering, atomic capacity registration, waitlist handling,
voluntary cancellation with auto-promotion, and cryptographic Digital Event Pass generation.
"""

from __future__ import annotations

import base64
from datetime import datetime
import io
import qrcode
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import current_user
from app.db.session import get_db
from app.models import Event, EventRegistration, Member, User
from app.services.event_service import CONTROLLED_CATEGORIES, EventService

router = APIRouter(prefix='/member/events', tags=['member-events'])


def _get_current_member(user: User, db: Session) -> Member | None:
    return db.scalar(select(Member).where(Member.user_id == user.id))


@router.get('')
@router.get('/')
def list_member_events(
    tab: str = Query('all', regex='^(all|upcoming|registered|past)$'),
    category: str | None = None,
    search: str | None = None,
    location: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    List events for member with tab filtering:
    - all: all published events
    - upcoming: future events
    - registered: events member has registered for
    - past: past completed events
    """
    member = _get_current_member(user, db)
    now = datetime.utcnow()

    # User's registrations lookup
    user_reg_pred = [
        EventRegistration.registration_status != 'CANCELLED',
    ]
    if member:
        user_reg_pred.append((EventRegistration.member_id == member.id) | (EventRegistration.user_id == user.id))
    else:
        user_reg_pred.append(EventRegistration.user_id == user.id)

    user_regs = db.scalars(select(EventRegistration).where(*user_reg_pred)).all()
    user_reg_map = {r.event_id: r for r in user_regs}
    registered_event_ids = list(user_reg_map.keys())

    # Build queries
    base_filter = [Event.is_published == True]

    if category and category.upper() in CONTROLLED_CATEGORIES:
        base_filter.append(Event.category == category.upper())

    if search:
        s = f"%{search.strip()}%"
        base_filter.append(
            or_(
                Event.title_bn.like(s),
                Event.title_en.like(s),
                Event.description_bn.like(s),
                Event.venue.like(s),
                Event.location_bn.like(s),
            )
        )

    if location:
        loc_str = f"%{location.strip()}%"
        base_filter.append(or_(Event.location_bn.like(loc_str), Event.venue.like(loc_str)))

    # Tab specific conditions
    stmt = select(Event).where(*base_filter)
    if tab == 'upcoming':
        stmt = stmt.where(or_(Event.event_date >= now, Event.start_date >= now))
    elif tab == 'past':
        stmt = stmt.where(or_(Event.event_date < now, Event.end_date < now))
    elif tab == 'registered':
        if not registered_event_ids:
            stmt = stmt.where(Event.id == -1)  # Empty result
        else:
            stmt = stmt.where(Event.id.in_(registered_event_ids))

    events = db.scalars(
        stmt.order_by(Event.event_date.asc() if tab != 'past' else Event.event_date.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    # Calculate global counts for tabs
    total_all = db.scalar(select(func.count(Event.id)).where(Event.is_published == True)) or 0
    total_upcoming = db.scalar(
        select(func.count(Event.id)).where(Event.is_published == True, Event.event_date >= now)
    ) or 0
    total_past = db.scalar(
        select(func.count(Event.id)).where(Event.is_published == True, Event.event_date < now)
    ) or 0
    total_registered = len(registered_event_ids)

    # Format events
    items = []
    for evt in events:
        reg = user_reg_map.get(evt.id)
        # Compute confirmed counts for capacity indicator
        confirmed_count = db.scalar(
            select(func.count(EventRegistration.id)).where(
                EventRegistration.event_id == evt.id,
                EventRegistration.registration_status.in_(['CONFIRMED', 'REGISTERED', 'ATTENDED']),
            )
        ) or 0
        waitlist_count = db.scalar(
            select(func.count(EventRegistration.id)).where(
                EventRegistration.event_id == evt.id,
                EventRegistration.registration_status == 'WAITLISTED',
            )
        ) or 0

        seats_available = max(0, evt.capacity - confirmed_count) if evt.capacity else None

        items.append({
            'id': evt.id,
            'category': evt.category or 'SEMINAR',
            'title_bn': evt.title_bn,
            'title_en': evt.title_en,
            'description_bn': evt.description_bn,
            'description_en': evt.description_en,
            'event_date': evt.event_date.isoformat() if evt.event_date else None,
            'start_date': evt.start_date.isoformat() if evt.start_date else None,
            'end_date': evt.end_date.isoformat() if evt.end_date else None,
            'start_time': evt.start_time,
            'end_time': evt.end_time,
            'venue': evt.venue or evt.location_bn or 'পিজিসিবি হেড অফিস অডিটোরিয়াম',
            'location_bn': evt.location_bn,
            'location_en': evt.location_en,
            'is_online': evt.is_online,
            'meeting_link': evt.meeting_link,
            'capacity': evt.capacity,
            'confirmed_count': confirmed_count,
            'waitlist_count': waitlist_count,
            'seats_available': seats_available,
            'fee_amount': evt.fee_amount or 0,
            'fee_currency': evt.fee_currency or 'BDT',
            'is_free': (evt.fee_amount or 0) == 0,
            'status': evt.status or 'PUBLISHED',
            'certificate_eligible': evt.certificate_eligible,
            'eligibility_criteria': evt.eligibility_criteria,
            'is_registered': reg is not None,
            'my_registration': {
                'id': reg.id,
                'registration_status': reg.registration_status,
                'attendance_status': reg.attendance_status,
                'payment_status': reg.payment_status,
                'ticket_code': reg.ticket_code,
                'waitlist_position': reg.waitlist_position,
                'registered_at': reg.registered_at.isoformat() if reg.registered_at else None,
            } if reg else None,
        })

    return {
        'items': items,
        'counts': {
            'all': total_all,
            'upcoming': total_upcoming,
            'registered': total_registered,
            'past': total_past,
        },
        'categories': list(CONTROLLED_CATEGORIES),
    }


@router.get('/{event_id}')
def get_member_event_details(
    event_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Retrieve detailed event view for member including capacity metrics and registration status."""
    evt = db.get(Event, event_id)
    if not evt or not evt.is_published:
        raise HTTPException(404, 'Event not found or not published')

    member = _get_current_member(user, db)
    user_reg_pred = [
        EventRegistration.event_id == event_id,
        EventRegistration.registration_status != 'CANCELLED',
    ]
    if member:
        user_reg_pred.append((EventRegistration.member_id == member.id) | (EventRegistration.user_id == user.id))
    else:
        user_reg_pred.append(EventRegistration.user_id == user.id)

    reg = db.scalar(select(EventRegistration).where(*user_reg_pred))

    confirmed_count = db.scalar(
        select(func.count(EventRegistration.id)).where(
            EventRegistration.event_id == evt.id,
            EventRegistration.registration_status.in_(['CONFIRMED', 'REGISTERED', 'ATTENDED']),
        )
    ) or 0
    waitlist_count = db.scalar(
        select(func.count(EventRegistration.id)).where(
            EventRegistration.event_id == evt.id,
            EventRegistration.registration_status == 'WAITLISTED',
        )
    ) or 0

    seats_available = max(0, evt.capacity - confirmed_count) if evt.capacity else None
    is_full = bool(evt.capacity and confirmed_count >= evt.capacity)

    return {
        'id': evt.id,
        'category': evt.category or 'SEMINAR',
        'title_bn': evt.title_bn,
        'title_en': evt.title_en,
        'description_bn': evt.description_bn,
        'description_en': evt.description_en,
        'event_date': evt.event_date.isoformat() if evt.event_date else None,
        'start_date': evt.start_date.isoformat() if evt.start_date else None,
        'end_date': evt.end_date.isoformat() if evt.end_date else None,
        'start_time': evt.start_time,
        'end_time': evt.end_time,
        'venue': evt.venue or evt.location_bn or 'পিজিসিবি হেড অফিস অডিটোরিয়াম',
        'location_bn': evt.location_bn,
        'location_en': evt.location_en,
        'is_online': evt.is_online,
        'meeting_link': evt.meeting_link,
        'capacity': evt.capacity,
        'confirmed_count': confirmed_count,
        'waitlist_count': waitlist_count,
        'seats_available': seats_available,
        'is_full': is_full,
        'fee_amount': evt.fee_amount or 0,
        'fee_currency': evt.fee_currency or 'BDT',
        'is_free': (evt.fee_amount or 0) == 0,
        'status': evt.status or 'PUBLISHED',
        'registration_enabled': evt.registration_enabled and evt.status != 'REGISTRATION_CLOSED',
        'certificate_eligible': evt.certificate_eligible,
        'eligibility_criteria': evt.eligibility_criteria,
        'is_registered': reg is not None,
        'my_registration': {
            'id': reg.id,
            'registration_status': reg.registration_status,
            'attendance_status': reg.attendance_status,
            'payment_status': reg.payment_status,
            'ticket_code': reg.ticket_code,
            'waitlist_position': reg.waitlist_position,
            'registered_at': reg.registered_at.isoformat() if reg.registered_at else None,
        } if reg else None,
    }


@router.post('/{event_id}/register')
def register_member_for_event(
    event_id: int,
    payload: dict | None = None,
    request: Request = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Member Event Registration:
    - Atomically checks capacity
    - If free & capacity available -> CONFIRMED
    - If paid -> prompts payment route
    - If full -> placed on WAITLIST with position
    """
    member = _get_current_member(user, db)
    client_ip = request.client.host if request and request.client else None
    reg = EventService.register_for_event(
        db=db,
        event_id=event_id,
        user=user,
        data=payload or {},
        member=member,
        ip=client_ip,
    )
    return {
        'ok': True,
        'message': (
            'ইভেন্ট নিবন্ধন নিশ্চিত হয়েছে।'
            if reg.registration_status == 'CONFIRMED'
            else f'আপনাকে ওয়েটিং লিস্টে রাখা হয়েছে (অবস্থান #{reg.waitlist_position or 1})।'
        ),
        'registration': {
            'id': reg.id,
            'event_id': reg.event_id,
            'registration_status': reg.registration_status,
            'attendance_status': reg.attendance_status,
            'payment_status': reg.payment_status,
            'ticket_code': reg.ticket_code,
            'waitlist_position': reg.waitlist_position,
            'registered_at': reg.registered_at.isoformat() if reg.registered_at else None,
        },
    }


@router.delete('/{event_id}/registration')
@router.post('/{event_id}/cancel')
def cancel_member_event_registration(
    event_id: int,
    payload: dict | None = None,
    request: Request = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Cancel event registration and automatically promote next waitlisted attendee."""
    client_ip = request.client.host if request and request.client else None
    reason = (payload or {}).get('reason') if payload else None
    return EventService.cancel_registration(
        db=db,
        event_id=event_id,
        user_id=user.id,
        reason=reason,
        ip=client_ip,
    )


@router.get('/{event_id}/pass')
def get_member_event_pass(
    event_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Digital Event Pass Endpoint:
    Returns event pass details, attendee identity, ticket code,
    and cryptographically signed QR code with tamper-proof verification.
    """
    evt = db.get(Event, event_id)
    if not evt:
        raise HTTPException(404, 'Event not found')

    member = _get_current_member(user, db)
    user_reg_pred = [
        EventRegistration.event_id == event_id,
        EventRegistration.registration_status != 'CANCELLED',
    ]
    if member:
        user_reg_pred.append((EventRegistration.member_id == member.id) | (EventRegistration.user_id == user.id))
    else:
        user_reg_pred.append(EventRegistration.user_id == user.id)

    reg = db.scalar(select(EventRegistration).where(*user_reg_pred))
    if not reg:
        raise HTTPException(404, 'No registration found for this event. Please register first.')

    if reg.registration_status == 'WAITLISTED':
        raise HTTPException(
            400,
            f'You are currently on the waitlist (#{reg.waitlist_position or 1}). Pass will be generated once confirmed.',
        )

    # Ensure token is signed
    qr_token = reg.qr_token or EventService.sign_ticket(reg.ticket_code, evt.id)
    if not reg.qr_token:
        reg.qr_token = qr_token
        db.commit()

    # Generate QR Code PNG and base64 encode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(qr_token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0A2540", back_color="#FFFFFF")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64_qr = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"

    event_info = {
        'id': evt.id,
        'category': evt.category or 'SEMINAR',
        'title_bn': evt.title_bn,
        'title_en': evt.title_en,
        'event_date': evt.event_date.isoformat() if evt.event_date else None,
        'start_date': evt.start_date.isoformat() if evt.start_date else None,
        'end_date': evt.end_date.isoformat() if evt.end_date else None,
        'start_time': evt.start_time or '10:00 AM',
        'end_time': evt.end_time or '05:00 PM',
        'venue': evt.venue or evt.location_bn or 'পিজিসিবি অডিটোরিয়াম, ঢাকা',
        'location_bn': evt.location_bn,
        'location_en': evt.location_en,
        'is_online': evt.is_online,
        'meeting_link': evt.meeting_link,
    }

    attendee_info = {
        'name': reg.name,
        'email': reg.email,
        'phone': reg.phone,
        'organization': reg.organization,
        'membership_id': member.membership_id if member else None,
        'employee_id': member.employee_id if member else None,
        'designation_bn': member.designation_bn if member else None,
        'circle_name': member.circle.name_bn if member and member.circle else None,
    }

    return {
        'ok': True,
        'pass': {
            'registration_id': reg.id,
            'ticket_code': reg.ticket_code,
            'qr_token': qr_token,
            'qr_image_data_url': b64_qr,
            'registration_status': reg.registration_status,
            'attendance_status': reg.attendance_status,
            'payment_status': reg.payment_status,
            'registered_at': reg.registered_at.isoformat() if reg.registered_at else None,
            'checked_in_at': reg.checked_in_at.isoformat() if reg.checked_in_at else None,
            'event': event_info,
            'attendee': attendee_info,
        },
        'event': event_info,
        'attendee': attendee_info,
    }


@router.get('/{event_id}/qr')
def stream_event_qr_image(
    event_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Direct PNG stream of member's signed QR code pass."""
    evt = db.get(Event, event_id)
    if not evt:
        raise HTTPException(404, 'Event not found')

    member = _get_current_member(user, db)
    user_reg_pred = [
        EventRegistration.event_id == event_id,
        EventRegistration.registration_status != 'CANCELLED',
    ]
    if member:
        user_reg_pred.append((EventRegistration.member_id == member.id) | (EventRegistration.user_id == user.id))
    else:
        user_reg_pred.append(EventRegistration.user_id == user.id)

    reg = db.scalar(select(EventRegistration).where(*user_reg_pred))
    if not reg:
        raise HTTPException(404, 'Registration not found')

    qr_token = reg.qr_token or EventService.sign_ticket(reg.ticket_code, evt.id)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(qr_token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0A2540", back_color="#FFFFFF")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png", headers={"Cache-Control": "no-store"})
