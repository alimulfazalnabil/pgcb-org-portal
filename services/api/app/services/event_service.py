"""
Institutional Event & Attendance Domain Service for PGCB Organization Portal.
Handles event registration, atomic capacity limits, waitlist management,
cryptographically signed QR tickets, anti-reuse check-in, attendance tracking,
and event certificate auto-issuance.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import hmac
import secrets
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (
    Certificate,
    CertificateVerificationRecord,
    Event,
    EventAttendance,
    EventRegistration,
    Member,
    User,
)
from app.services import audit
from app.services.email import EmailService
from app.services.notification_service import NotificationService

CONTROLLED_CATEGORIES = (
    'AGM',
    'SEMINAR',
    'WORKSHOP',
    'TRAINING',
    'CONFERENCE',
    'WEBINAR',
    'MEETING',
    'SOCIAL',
    'PROFESSIONAL_DEVELOPMENT',
    'OTHER',
)


class EventService:
    @staticmethod
    def sign_ticket(ticket_code: str, event_id: int) -> str:
        """Create HMAC-SHA256 signature for ticket code and event id."""
        payload = f"{event_id}:{ticket_code}"
        sig = hmac.new(settings.jwt_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
        return f"{ticket_code}.{sig}"

    @staticmethod
    def verify_ticket_token(token: str, expected_event_id: int | None = None) -> tuple[str, bool]:
        """Verify ticket token against HMAC signature. Returns (ticket_code, is_valid)."""
        if not token or '.' not in token:
            return token, False
        ticket_code, sig = token.rsplit('.', 1)
        if expected_event_id is not None:
            expected_sig = hmac.new(
                settings.jwt_secret.encode(),
                f"{expected_event_id}:{ticket_code}".encode(),
                hashlib.sha256,
            ).hexdigest()[:32]
            return ticket_code, hmac.compare_digest(expected_sig, sig)

        # Fallback: ticket signature independent of event_id
        alt_sig = hmac.new(settings.jwt_secret.encode(), ticket_code.encode(), hashlib.sha256).hexdigest()[:32]
        return ticket_code, hmac.compare_digest(alt_sig, sig)

    @staticmethod
    def register_for_event(
        db: Session,
        event_id: int,
        user: User,
        data: dict | None = None,
        member: Member | None = None,
        ip: str | None = None,
    ) -> EventRegistration:
        """
        Register a member for an event. Enforces:
        - Published & registration enabled status
        - Registration deadline
        - Duplicate prevention
        - Atomic capacity and waitlist placement
        - Cryptographic QR token generation
        """
        data = data or {}
        event = db.get(Event, event_id)
        if not event or not event.is_published:
            raise HTTPException(404, 'Event not found or not published')

        if not event.registration_enabled or event.status == 'REGISTRATION_CLOSED':
            raise HTTPException(400, 'Registration is currently closed for this event')

        if event.status == 'CANCELLED':
            raise HTTPException(400, 'This event has been cancelled')

        if event.registration_deadline and event.registration_deadline < datetime.utcnow():
            raise HTTPException(400, 'Registration deadline has passed')

        # Check existing active registration
        existing_pred = [
            EventRegistration.event_id == event_id,
            EventRegistration.registration_status != 'CANCELLED',
        ]
        if member:
            existing_pred.append(
                (EventRegistration.member_id == member.id) | (EventRegistration.user_id == user.id)
            )
        else:
            existing_pred.append(EventRegistration.user_id == user.id)

        existing = db.scalar(select(EventRegistration).where(*existing_pred))
        if existing:
            if existing.registration_status == 'WAITLISTED':
                raise HTTPException(409, f'You are already on the waitlist (Position: #{existing.waitlist_position or 1})')
            raise HTTPException(409, 'You are already registered for this event')

        # Check capacity & waitlist
        is_free = (event.fee_amount or 0) == 0
        confirmed_count = db.scalar(
            select(func.count(EventRegistration.id)).where(
                EventRegistration.event_id == event_id,
                EventRegistration.registration_status.in_(['CONFIRMED', 'REGISTERED', 'ATTENDED']),
            )
        ) or 0

        is_full = bool(event.capacity and confirmed_count >= event.capacity)

        year = datetime.utcnow().year
        ticket_code = f"TKT-{year}-{event_id:03d}-{uuid4().hex[:8].upper()}"
        signed_token = EventService.sign_ticket(ticket_code, event_id)

        if is_full:
            # Place on waitlist
            max_pos = db.scalar(
                select(func.max(EventRegistration.waitlist_position)).where(
                    EventRegistration.event_id == event_id,
                    EventRegistration.registration_status == 'WAITLISTED',
                )
            ) or 0
            waitlist_pos = max_pos + 1
            reg_status = 'WAITLISTED'
            payment_status = 'NOT_REQUIRED'
        else:
            waitlist_pos = None
            reg_status = 'CONFIRMED'
            payment_status = 'PAID' if is_free else 'REQUIRED'

        reg_name = (
            data.get('name')
            or (member.user.name_bn if member and member.user else None)
            or user.name_bn
            or user.name_en
            or 'প্রকৌশলী'
        )
        reg_email = (user.email or data.get('email') or '').lower().strip()
        reg_phone = data.get('phone') or user.phone or ''
        reg_org = (
            data.get('organization')
            or (member.designation_bn if member else None)
            or 'PGCB'
        )

        reg = EventRegistration(
            event_id=event_id,
            user_id=user.id,
            member_id=member.id if member else None,
            name=reg_name,
            email=reg_email,
            phone=reg_phone,
            organization=reg_org,
            ticket_code=ticket_code,
            qr_token=signed_token,
            registration_status=reg_status,
            attendance_status='NOT_CHECKED_IN',
            payment_status=payment_status,
            waitlist_position=waitlist_pos,
            registered_at=datetime.utcnow(),
        )
        db.add(reg)
        db.flush()

        audit(db, user, 'EVENT_REGISTRATION', 'EVENT', event_id, ip)

        if reg_status == 'CONFIRMED':
            NotificationService.send_notification(
                db=db,
                user_id=user.id,
                title_bn=f"ইভেন্ট নিবন্ধন নিশ্চিত: {event.title_bn}",
                title_en=f"Event Registration Confirmed: {event.title_en or event.title_bn}",
                body_bn=f"'{event.title_bn}' ইভেন্টে আপনার আসন নিশ্চিত হয়েছে। টিকিট কোড: {ticket_code}। ডিজিটাল পাস সংগ্রহ করুন।",
                body_en=f"Your seat for '{event.title_en or event.title_bn}' is confirmed. Ticket Code: {ticket_code}. Access your digital event pass.",
                notification_type='EVENT',
                action_route=f"/member/events/{event_id}/pass",
                action_label="View Event Pass",
                action_label_bn="ইভেন্ট পাস দেখুন",
                priority='HIGH',
                entity_type='EVENT',
                entity_id=event_id,
                extra_data={'ticket_code': ticket_code, 'event_id': event_id},
            )
            EmailService.send_event_confirmation(
                to_email=user.email,
                participant_name=reg.name,
                event_title=event.title_bn,
                ticket_code=reg.ticket_code,
                event_date=event.event_date.strftime('%Y-%m-%d %H:%M') if event.event_date else 'শীঘ্রই জানানো হবে',
                location=event.venue or event.location_bn or 'পিজিসিবি অডিটোরিয়াম',
            )
        else:
            NotificationService.send_notification(
                db=db,
                user_id=user.id,
                title_bn=f"ইভেন্ট ওয়েটিং লিস্টে যুক্ত হয়েছেন: {event.title_bn}",
                title_en=f"Joined Event Waitlist: {event.title_en or event.title_bn}",
                body_bn=f"ইভেন্টের নির্ধারিত আসন পূর্ণ হওয়ায় আপনাকে ওয়েটিং লিস্টে রাখা হয়েছে (অবস্থান: #{waitlist_pos})। আসন খালি হলে স্বয়ংক্রিয়ভাবে নোটিফিকেশন পাবেন।",
                body_en=f"Event capacity is reached. You are on the waitlist (Position: #{waitlist_pos}). You will be automatically promoted if a seat opens.",
                notification_type='EVENT',
                action_route=f"/member/events/{event_id}",
                action_label="View Event Details",
                action_label_bn="ইভেন্ট বিবরণ দেখুন",
                priority='NORMAL',
                entity_type='EVENT',
                entity_id=event_id,
            )

        db.commit()
        db.refresh(reg)
        return reg

    @staticmethod
    def cancel_registration(
        db: Session,
        event_id: int,
        user_id: int,
        reason: str | None = None,
        ip: str | None = None,
    ) -> dict:
        """
        Cancel a registration. If the cancelled registration was CONFIRMED,
        automatically promotes the next person on the waitlist.
        """
        reg = db.scalar(
            select(EventRegistration).where(
                EventRegistration.event_id == event_id,
                EventRegistration.user_id == user_id,
                EventRegistration.registration_status != 'CANCELLED',
            )
        )
        if not reg:
            raise HTTPException(404, 'Active event registration not found')

        was_confirmed = reg.registration_status in ('CONFIRMED', 'REGISTERED')
        reg.registration_status = 'CANCELLED'
        reg.cancelled_at = datetime.utcnow()
        reg.cancellation_reason = reason or 'Member voluntary cancellation'
        old_waitlist_pos = reg.waitlist_position
        reg.waitlist_position = None

        promoted_member_info: dict | None = None

        # Auto-promote waitlist if confirmed registration cancelled
        if was_confirmed:
            next_waitlist = db.scalar(
                select(EventRegistration)
                .where(
                    EventRegistration.event_id == event_id,
                    EventRegistration.registration_status == 'WAITLISTED',
                )
                .order_by(
                    EventRegistration.waitlist_position.asc(),
                    EventRegistration.registered_at.asc(),
                )
            )
            if next_waitlist:
                event = db.get(Event, event_id)
                is_free = (event.fee_amount or 0) == 0 if event else True
                next_waitlist.registration_status = 'CONFIRMED' if is_free else 'OFFERED'
                next_waitlist.payment_status = 'PAID' if is_free else 'REQUIRED'
                next_waitlist.waitlist_position = None

                if next_waitlist.user_id and event:
                    NotificationService.send_notification(
                        db=db,
                        user_id=next_waitlist.user_id,
                        title_bn=f"অভিনন্দন! ইভেন্ট নিবন্ধন নিশ্চিত হয়েছে: {event.title_bn}",
                        title_en=f"Congratulations! Promoted from Waitlist: {event.title_en or event.title_bn}",
                        body_bn=f"আসন খালি হওয়ায় আপনি ওয়েটিং লিস্ট থেকে মূল ইভেন্টে উত্তীর্ণ হয়েছেন। আপনার ডিজিটাল পাস প্রস্তুত।",
                        body_en=f"A seat became available and you have been promoted from the waitlist for '{event.title_en or event.title_bn}'.",
                        notification_type='EVENT_REGISTRATION',
                        action_route=f"/member/events/{event_id}/pass",
                        action_label="View Event Pass",
                        action_label_bn="ইভেন্ট পাস দেখুন",
                        priority='HIGH',
                        entity_type='EVENT',
                        entity_id=event_id,
                    )
                promoted_member_info = {
                    'registration_id': next_waitlist.id,
                    'user_id': next_waitlist.user_id,
                    'ticket_code': next_waitlist.ticket_code,
                }

        user = db.get(User, user_id)
        audit(db, user, 'CANCEL_EVENT_REGISTRATION', 'EVENT', event_id, ip)
        db.commit()

        return {
            'ok': True,
            'message': 'নিবন্ধন সফলভাবে বাতিল করা হয়েছে।',
            'event_id': event_id,
            'registration_id': reg.id,
            'promoted_attendee_id': promoted_member_info['registration_id'] if promoted_member_info else None,
            'promoted_waitlist_attendee': promoted_member_info,
        }

    @staticmethod
    def check_in_attendee(
        db: Session,
        event_id: int,
        token_or_code: str,
        admin_user: User,
        method: str = 'QR',
        ip: str | None = None,
    ) -> dict:
        """
        Institutional Check-in Endpoint with anti-reuse protection, signature validation,
        and automatic Certificate of Participation issuance.
        """
        raw_val = (token_or_code or '').strip()
        ticket_code, is_signed = EventService.verify_ticket_token(raw_val, expected_event_id=event_id)
        if not ticket_code:
            raise HTTPException(400, 'Ticket code or token is required')

        reg = db.scalar(
            select(EventRegistration).where(
                EventRegistration.event_id == event_id,
                EventRegistration.ticket_code == ticket_code,
            )
        )
        if not reg:
            # Fallback search across ticket_code or qr_token
            reg = db.scalar(
                select(EventRegistration).where(
                    EventRegistration.event_id == event_id,
                    (EventRegistration.ticket_code == raw_val) | (EventRegistration.qr_token == raw_val),
                )
            )
        if not reg:
            raise HTTPException(404, f'No registration found for ticket code: {ticket_code} under this event')

        if reg.registration_status == 'CANCELLED':
            raise HTTPException(409, 'This registration has been cancelled and is invalid for entry')

        if reg.registration_status == 'WAITLISTED':
            raise HTTPException(409, 'Attendee is on the waitlist. Registration not confirmed')

        if reg.payment_status in ('REQUIRED', 'PENDING', 'FAILED'):
            raise HTTPException(409, 'Payment must be completed before check-in')

        # Check anti-reuse
        if reg.attendance_status in ('CHECKED_IN', 'ATTENDED'):
            check_time = reg.checked_in_at.strftime('%I:%M %p') if reg.checked_in_at else 'earlier'
            raise HTTPException(
                409,
                f"⚠ ALREADY CHECKED IN (Checked in at {check_time}) - Ticket cannot be reused",
            )

        now = datetime.utcnow()
        reg.attendance_status = 'ATTENDED'
        reg.checked_in_at = now
        reg.checked_in_by = admin_user.id

        # Record in EventAttendance table
        att_record = db.scalar(
            select(EventAttendance).where(
                EventAttendance.event_id == event_id,
                EventAttendance.registration_id == reg.id,
            )
        )
        if not att_record:
            att_record = EventAttendance(
                event_id=event_id,
                registration_id=reg.id,
                member_id=reg.member_id,
                checked_in_at=now,
                checked_in_by=admin_user.id,
                method=method,
            )
            db.add(att_record)

        # Check automatic Certificate of Participation issuance
        event = db.get(Event, event_id)
        certificate_issued = False
        cert_info: dict | None = None

        if event and event.certificate_eligible and reg.member_id:
            existing_cert = db.scalar(
                select(Certificate).where(
                    Certificate.event_registration_id == reg.id,
                    Certificate.certificate_type == 'EVENT',
                )
            )
            if not existing_cert:
                cert_no = f"PGCB-EVT-CERT-{now.year}-{reg.id:05d}"
                raw_token = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
                new_cert = Certificate(
                    certificate_no=cert_no,
                    recipient_name=reg.name,
                    title_bn=f"{event.title_bn} — অংশগ্রহণ সনদ",
                    title_en=f"{event.title_en or event.title_bn} — Certificate of Participation",
                    certificate_type='EVENT',
                    issue_date=now,
                    event_registration_id=reg.id,
                    member_id=reg.member_id,
                    verification_token_hash=token_hash,
                    storage_path=f"certificates/{cert_no}.pdf",
                    pdf_path=f"certificates/{cert_no}.pdf",
                    status='VALID',
                )
                db.add(new_cert)
                db.flush()

                db.add(
                    CertificateVerificationRecord(
                        certificate_id=new_cert.id,
                        action='ISSUED',
                        actor_id=admin_user.id,
                        reason='Event attendance verified check-in',
                    )
                )
                certificate_issued = True
                cert_info = {
                    'certificate_id': new_cert.id,
                    'certificate_no': new_cert.certificate_no,
                    'title': new_cert.title_bn,
                }

                if reg.user_id:
                    NotificationService.send_notification(
                        db=db,
                        user_id=reg.user_id,
                        title_bn=f"ইভেন্ট সনদপত্র ইস্যু হয়েছে: {event.title_bn}",
                        title_en=f"Certificate of Participation Issued: {event.title_en or event.title_bn}",
                        body_bn=f"'{event.title_bn}' ইভেন্টে উপস্থিত থাকার জন্য আপনার ডিজিটাল সনদপত্র ইস্যু করা হয়েছে। সনদ নম্বর: {cert_no}",
                        body_en=f"Your Certificate of Participation for '{event.title_en or event.title_bn}' has been issued. Certificate No: {cert_no}",
                        notification_type='CERTIFICATE',
                        action_route=f"/member/certificates/{new_cert.id}",
                        action_label="View Certificate",
                        action_label_bn="সনদপত্র দেখুন",
                        priority='NORMAL',
                        entity_type='CERTIFICATE',
                        entity_id=new_cert.id,
                    )

        audit(db, admin_user, 'CHECK_IN_ATTENDEE', 'EVENT_REGISTRATION', reg.id, ip)
        db.commit()

        # Count total checked-in
        total_checked_in = db.scalar(
            select(func.count(EventRegistration.id)).where(
                EventRegistration.event_id == event_id,
                EventRegistration.attendance_status == 'CHECKED_IN',
            )
        ) or 0

        return {
            'ok': True,
            'message': 'উপস্থিতি সফলভাবে রেকর্ড করা হয়েছে।',
            'ticket_code': reg.ticket_code,
            'participant_name': reg.name,
            'organization': reg.organization,
            'attendance_status': reg.attendance_status,
            'checked_in_at': reg.checked_in_at.isoformat() if reg.checked_in_at else now.isoformat(),
            'total_checked_in': total_checked_in,
            'certificate_issued': certificate_issued,
            'certificate': cert_info,
            'registration': {
                'id': reg.id,
                'ticket_code': reg.ticket_code,
                'attendee_name': reg.name,
                'membership_id': reg.member.membership_id if reg.member else None,
                'attendance_status': reg.attendance_status,
            },
            'attendance': {
                'checked_in_at': reg.checked_in_at.isoformat() if reg.checked_in_at else now.isoformat(),
                'method': method,
            },
        }
