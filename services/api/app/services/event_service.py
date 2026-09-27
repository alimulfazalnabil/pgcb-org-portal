"""
Institutional Event & Attendance Domain Service for PGCB Organization Portal.
Handles event registration, capacity limits, QR ticket verification, anti-reuse check-in, and attendance tracking.
"""

from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Event, EventRegistration, User
from app.services import audit, notify
from app.services.email import EmailService


class EventService:
    @staticmethod
    def register_for_event(
        db: Session,
        event_id: int,
        user: User,
        data: dict,
        ip: str | None = None,
    ) -> EventRegistration:
        event = db.get(Event, event_id)
        if not event or not event.is_published:
            raise HTTPException(404, 'Event not found or not published')

        if not event.registration_enabled:
            raise HTTPException(400, 'Registration is currently disabled for this event')

        if event.registration_deadline and event.registration_deadline < datetime.utcnow():
            raise HTTPException(400, 'Registration deadline has passed')

        # Check existing registration
        existing = db.scalar(
            select(EventRegistration).where(
                EventRegistration.event_id == event_id,
                EventRegistration.user_id == user.id,
                EventRegistration.registration_status != 'CANCELLED',
            )
        )
        if existing:
            raise HTTPException(409, 'You are already registered for this event')

        # Check capacity
        if event.capacity:
            current_count = db.scalar(
                select(func.count(EventRegistration.id)).where(
                    EventRegistration.event_id == event_id,
                    EventRegistration.registration_status != 'CANCELLED',
                )
            ) or 0
            if current_count >= event.capacity:
                raise HTTPException(400, 'Event capacity has been reached')

        ticket_count = data.get('ticket_count', 1)
        is_free = (event.fee_amount or 0) == 0
        payment_status = 'PAID' if is_free else 'REQUIRED'

        from uuid import uuid4
        year = datetime.utcnow().year
        ticket_code = f"TKT-{year}-{event_id:03d}-{uuid4().hex[:8].upper()}"

        reg = EventRegistration(
            event_id=event_id,
            user_id=user.id,
            name=user.name_bn or user.name_en or 'প্রকৌশলী',
            email=user.email,
            phone=user.phone or '',
            organization=data.get('organization'),
            ticket_code=ticket_code,
            registration_status='CONFIRMED',
            payment_status=payment_status,
            attendance_status='NOT_CHECKED_IN',
            registered_at=datetime.utcnow(),
        )
        db.add(reg)
        db.flush()

        audit(db, user, 'EVENT_REGISTRATION', 'EVENT', event_id, ip)

        notify(
            db,
            user.id,
            'ইভেন্ট নিবন্ধন নিশ্চিত হয়েছে',
            f'{event.title_bn} ইভেন্টে আপনার নিবন্ধন নিশ্চিত হয়েছে। টিকিট কোড: {reg.ticket_code}',
            'EVENT',
        )

        EmailService.send_event_confirmation(
            to_email=user.email,
            participant_name=reg.name,
            event_title=event.title_bn,
            ticket_code=reg.ticket_code,
            event_date=event.event_date.strftime('%Y-%m-%d %H:%M') if event.event_date else 'শীঘ্রই জানানো হবে',
            location=event.location_bn or 'পিজিসিবি অডিটোরিয়াম',
        )

        db.commit()
        db.refresh(reg)
        return reg

    @staticmethod
    def check_in_ticket(
        db: Session,
        ticket_code: str,
        admin_user: User,
        ip: str | None = None,
    ) -> dict:
        reg = db.scalar(
            select(EventRegistration).where(EventRegistration.ticket_code == ticket_code.strip())
        )
        if not reg:
            raise HTTPException(404, f'Invalid ticket code: {ticket_code}')

        if reg.registration_status == 'CANCELLED':
            raise HTTPException(409, 'This registration has been cancelled')

        if reg.payment_status in ('REQUIRED', 'PENDING', 'FAILED'):
            raise HTTPException(409, 'Payment must be completed before check-in')

        already_checked_in = reg.attendance_status == 'CHECKED_IN'
        if already_checked_in:
            raise HTTPException(
                409,
                f"টিকিটটি ইতিমধ্যে ব্যবহৃত হয়েছে (Checked in at {reg.checked_in_at.strftime('%H:%M:%S') if reg.checked_in_at else 'earlier'})"
            )

        reg.attendance_status = 'CHECKED_IN'
        reg.checked_in_at = datetime.utcnow()
        reg.checked_in_by = admin_user.id

        audit(db, admin_user, 'CHECK_IN_TICKET', 'EVENT_REGISTRATION', reg.id, ip)
        db.commit()

        return {
            'ok': True,
            'message': 'উপস্থিতি সফলভাবে রেকর্ড করা হয়েছে।',
            'ticket_code': reg.ticket_code,
            'participant_name': reg.name,
            'attendance_status': reg.attendance_status,
            'checked_in_at': reg.checked_in_at.isoformat(),
        }
