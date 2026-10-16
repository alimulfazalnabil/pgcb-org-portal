"""
Phase 7: Authenticated Member-Aware AI Service & Controlled Tools Architecture.

Strictly enforces IDOR/BOLA protection:
- The AI never receives or executes raw database queries.
- Caller-supplied member IDs are never accepted; user and member context is securely resolved on the server from current_user.
- Sensitive data masking: NID is masked (e.g. ********1234), phone numbers are masked (+880 17****5678).
- Financial mutations and membership renewals require explicit confirmation flows and redirect to secure workflows.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.core import (
    Certificate,
    Circle,
    Event,
    EventRegistration,
    Member,
    MemberDocument,
    MemberProfileChangeRequest,
    MemberProfileMeta,
    Membership,
    MembershipApplication,
    MembershipRenewal,
    Notification,
    PaymentTransaction,
    SupportTicket,
    User,
)
from app.services import audit


# ---------------------------------------------------------------------------
# Sensitive Data Masking Helpers
# ---------------------------------------------------------------------------

def mask_nid(nid: str | None) -> str | None:
    """Mask National ID number, exposing only the last 4 digits."""
    if not nid:
        return None
    cleaned = nid.strip()
    if len(cleaned) <= 4:
        return '****'
    return '*' * (len(cleaned) - 4) + cleaned[-4:]


def mask_phone(phone: str | None) -> str | None:
    """Mask phone number, preserving country/prefix and last 4 digits."""
    if not phone:
        return None
    cleaned = phone.strip()
    if len(cleaned) <= 6:
        return '****'
    prefix = cleaned[:6]
    suffix = cleaned[-4:]
    return f"{prefix}{'*' * max(2, len(cleaned) - 10)}{suffix}"


# ---------------------------------------------------------------------------
# 13 Controlled Member Tools
# ---------------------------------------------------------------------------

def tool_get_member_profile(db: Session, user: User, member: Member | None) -> dict[str, Any]:
    """Get the authenticated member's verified profile data with PII masking."""
    circle_name_en = 'Unassigned'
    circle_name_bn = 'অনির্ধারিত'
    if member and member.circle_id:
        circle = db.get(Circle, member.circle_id)
        if circle:
            circle_name_en = circle.name_en or circle.name_bn
            circle_name_bn = circle.name_bn or circle.name_en

    meta = db.scalar(select(MemberProfileMeta).where(MemberProfileMeta.member_id == member.id)) if member else None

    return {
        'name_en': (getattr(member, 'name_en', None) if member else None) or user.name_en or user.name_bn,
        'name_bn': (getattr(member, 'name_bn', None) if member else None) or user.name_bn,
        'membership_id': member.membership_id if member and member.membership_id else 'Not Assigned',
        'employee_id': member.employee_id if member else None,
        'designation_en': (getattr(member, 'designation_en', None) if member else None) or 'Diploma Engineer',
        'designation_bn': (getattr(member, 'designation_bn', None) if member else None) or 'উপ-সহকারী প্রকৌশলী',
        'grid_circle_en': circle_name_en,
        'grid_circle_bn': circle_name_bn,
        'diploma_institution': member.diploma_institution if member else None,
        'graduation_year': member.graduation_year if member else None,
        'email': user.email,
        'phone_masked': mask_phone(user.phone or (member.alternate_phone if meta else None)),
        'nid_masked': mask_nid(member.nid_number if member else None),
        'photo_url': member.photo_url if member else None,
        'status': member.status if member else 'PENDING',
        'current_address': member.current_address if member else None,
        'permanent_address': member.permanent_address if member else None,
        'blood_group': meta.blood_group if meta else None,
        'emergency_contact_name': meta.emergency_contact_name if meta else None,
        'emergency_contact_phone_masked': mask_phone(meta.emergency_contact_phone) if meta else None,
    }


def tool_get_membership_status(db: Session, user: User, member: Member | None) -> dict[str, Any]:
    """Get the authenticated member's membership status, validity dates, and renewal status."""
    if not member:
        return {
            'has_membership': False,
            'status': 'NO_MEMBERSHIP',
            'membership_id': None,
            'valid_until': None,
            'days_remaining': 0,
            'is_expired': False,
            'renewal_eligible': False,
        }

    status = member.status or 'PENDING'
    valid_until = member.validity_date
    now = datetime.utcnow()

    days_remaining = (valid_until - now).days if valid_until else None
    is_expired = days_remaining is not None and days_remaining < 0

    return {
        'has_membership': True,
        'membership_id': member.membership_id or 'Assigned upon approval',
        'membership_type': member.membership_type or 'GENERAL',
        'status': status,
        'issue_date': member.issue_date.strftime('%d %B %Y') if member.issue_date else None,
        'valid_until': valid_until.strftime('%d %B %Y') if valid_until else 'Lifetime / N/A',
        'days_remaining': days_remaining,
        'is_expired': is_expired,
        'is_active': status == 'ACTIVE' and not is_expired,
        'renewal_eligible': status in ('ACTIVE', 'EXPIRED'),
        'renewal_fee_bdt': 2000,
    }


def tool_get_membership_history(db: Session, user: User, member: Member | None) -> dict[str, Any]:
    """Get chronological timeline of renewals, profile changes, and membership status changes."""
    timeline: list[dict[str, Any]] = []

    if member:
        # 1. Original Application / Membership created
        timeline.append({
            'date': member.created_at.strftime('%d %B %Y') if member.created_at else 'Initial',
            'event': 'Initial Membership Application',
            'details': f"Type: {member.membership_type or 'GENERAL'}",
            'status': member.status,
        })

        # 2. Renewals
        renewals = db.scalars(
            select(MembershipRenewal)
            .where(MembershipRenewal.member_id == member.id)
            .order_by(MembershipRenewal.created_at.desc())
        ).all()
        for r in renewals:
            timeline.append({
                'date': r.created_at.strftime('%d %B %Y') if r.created_at else 'Renewal',
                'event': 'Membership Renewal',
                'details': f"Fee: ৳{r.amount or 2000:,} BDT | Years: {r.duration_years or 1}",
                'status': r.status or 'COMPLETED',
            })

        # 3. Profile Change Requests
        changes = db.scalars(
            select(MemberProfileChangeRequest)
            .where(MemberProfileChangeRequest.member_id == member.id)
            .order_by(MemberProfileChangeRequest.created_at.desc())
        ).all()
        for c in changes:
            timeline.append({
                'date': c.created_at.strftime('%d %B %Y') if c.created_at else 'Update',
                'event': f"Profile Change: {c.field_name}",
                'details': f"Status: {c.status}",
                'status': c.status,
            })

    return {
        'timeline_count': len(timeline),
        'timeline': timeline,
    }


def tool_get_application_status(db: Session, user: User, member: Member | None) -> dict[str, Any]:
    """Get the latest membership application record and its current review stage."""
    app_row = None
    if member:
        app_row = db.scalar(
            select(MembershipApplication)
            .where(MembershipApplication.member_id == member.id)
            .order_by(MembershipApplication.id.desc())
        )

    app_no = (
        (getattr(app_row, 'application_no', None) if app_row else None)
        or (getattr(member, 'application_no', None) if member else None)
        or 'N/A'
    )
    status = (app_row.status if app_row else (member.status if member else 'NO_APPLICATION'))

    return {
        'has_application': app_row is not None or (member and member.application_no is not None),
        'application_no': app_no,
        'membership_type': getattr(app_row, 'membership_type', None) or (member.membership_type if member else 'GENERAL'),
        'status': status,
        'submitted_at': app_row.created_at.strftime('%d %B %Y') if (app_row and getattr(app_row, 'created_at', None)) else (member.created_at.strftime('%d %B %Y') if member else None),
        'reviewed_at': app_row.reviewed_at.strftime('%d %B %Y') if (app_row and app_row.reviewed_at) else None,
        'review_note': app_row.review_note if app_row else None,
    }


def tool_get_pending_documents(db: Session, user: User, member: Member | None) -> dict[str, Any]:
    """Get the member's uploaded documents that are pending institutional verification."""
    if not member:
        return {'pending_count': 0, 'documents': []}

    docs = list(
        db.scalars(
            select(MemberDocument)
            .where(
                MemberDocument.member_id == member.id,
                MemberDocument.deleted_at.is_(None),
                MemberDocument.review_status.in_(('PENDING', 'UNDER_REVIEW')),
            )
            .order_by(MemberDocument.id.desc())
        ).all()
    )

    items = []
    for d in docs:
        items.append({
            'id': d.id,
            'title': d.title or d.document_type,
            'document_type': d.document_type,
            'review_status': d.review_status,
            'submitted_at': d.created_at.strftime('%d %B %Y') if d.created_at else 'N/A',
            'reviewer_note': d.reviewer_note,
        })

    return {
        'pending_count': len(items),
        'documents': items,
    }


def tool_get_payment_history(db: Session, user: User, member: Member | None) -> dict[str, Any]:
    """Get the member's financial transaction logs, receipts, and payment statuses."""
    pred = [PaymentTransaction.user_id == user.id]
    if member:
        pred = [or_(PaymentTransaction.user_id == user.id, PaymentTransaction.member_id == member.id)]

    txs = list(
        db.scalars(
            select(PaymentTransaction)
            .where(*pred)
            .order_by(PaymentTransaction.id.desc())
            .limit(15)
        ).all()
    )

    paid_txs = [t for t in txs if t.status in ('PAID', 'SUCCESS', 'COMPLETED')]
    total_paid = sum(int(t.amount or 0) for t in paid_txs)

    items = []
    for t in txs:
        items.append({
            'id': t.id,
            'transaction_ref': t.transaction_ref,
            'receipt_no': getattr(t, 'receipt_no', None),
            'amount': int(t.amount or 0),
            'currency': t.currency or 'BDT',
            'purpose': t.purpose or 'MEMBERSHIP',
            'status': t.status,
            'payment_provider': t.payment_method or 'BKASH',
            'date': t.created_at.strftime('%d %B %Y') if t.created_at else 'N/A',
            'receipt_download_url': f"/api/v1/member/payments/{t.id}/receipt.pdf" if t.status in ('PAID', 'SUCCESS', 'COMPLETED') else None,
        })

    return {
        'total_transactions': len(txs),
        'total_paid_bdt': total_paid,
        'transactions': items,
    }


def tool_get_payment_status(db: Session, user: User, member: Member | None) -> dict[str, Any]:
    """Check if the member has outstanding balances or pending payments."""
    pred = [PaymentTransaction.user_id == user.id]
    if member:
        pred = [or_(PaymentTransaction.user_id == user.id, PaymentTransaction.member_id == member.id)]

    pending_tx = db.scalar(
        select(PaymentTransaction)
        .where(
            *pred,
            PaymentTransaction.status.in_(['PENDING', 'INITIATED', 'PROCESSING']),
        )
        .order_by(PaymentTransaction.id.desc())
    )

    latest_paid = db.scalar(
        select(PaymentTransaction)
        .where(
            *pred,
            PaymentTransaction.status.in_(['PAID', 'SUCCESS', 'COMPLETED']),
        )
        .order_by(PaymentTransaction.id.desc())
    )

    has_due = pending_tx is not None
    return {
        'has_pending_payment': has_due,
        'pending_amount_bdt': int(pending_tx.amount or 0) if pending_tx else 0,
        'pending_purpose': pending_tx.purpose if pending_tx else None,
        'pending_transaction_id': pending_tx.id if pending_tx else None,
        'last_paid_amount': int(latest_paid.amount or 0) if latest_paid else None,
        'last_paid_date': latest_paid.created_at.strftime('%d %B %Y') if (latest_paid and latest_paid.created_at) else None,
        'last_receipt_download_url': f"/api/v1/member/payments/{latest_paid.id}/receipt.pdf" if latest_paid else None,
    }


def tool_get_certificates(db: Session, user: User, member: Member | None) -> dict[str, Any]:
    """Get the member's official verified credentials and certificates."""
    if not member:
        return {'certificate_count': 0, 'certificates': []}

    certs = list(
        db.scalars(
            select(Certificate)
            .where(Certificate.member_id == member.id)
            .order_by(Certificate.id.desc())
        ).all()
    )

    items = []
    for c in certs:
        items.append({
            'id': c.id,
            'certificate_no': c.certificate_no,
            'title_bn': c.title_bn,
            'title_en': getattr(c, 'title_en', None) or c.title_bn,
            'certificate_type': getattr(c, 'certificate_type', 'MEMBERSHIP'),
            'issue_date': c.issued_at.strftime('%d %B %Y') if getattr(c, 'issued_at', None) else (c.issue_date.strftime('%d %B %Y') if getattr(c, 'issue_date', None) else 'N/A'),
            'status': getattr(c, 'status', 'VALID'),
            'verification_token': c.verification_token,
            'verification_url': f"/verify/{c.verification_token}" if c.verification_token else None,
        })

    return {
        'certificate_count': len(items),
        'certificates': items,
    }


def tool_get_digital_id(db: Session, user: User, member: Member | None) -> dict[str, Any]:
    """Get the member's digital ID card validity, QR token, and portal route."""
    if not member:
        return {
            'has_card': False,
            'status': 'NO_MEMBER',
            'is_valid': False,
            'card_url': '/member/digital-id',
        }

    from app.domain.documents_id import get_or_create_digital_id
    did = get_or_create_digital_id(db, member)
    is_active = (did.status == 'ACTIVE')

    valid_until_str = 'Lifetime / N/A'
    if did.valid_until:
        valid_until_str = did.valid_until.strftime('%d %B %Y')
    elif member.validity_date:
        valid_until_str = member.validity_date.strftime('%d %B %Y')

    return {
        'has_card': True,
        'card_no': did.card_no,
        'status': did.status,
        'is_valid': is_active,
        'valid_until': valid_until_str,
        'membership_id': member.membership_id,
        'card_url': '/member/digital-id',
    }


def tool_get_registered_events(db: Session, user: User, member: Member | None) -> dict[str, Any]:
    """Get events the member has registered for, including attendance status and event passes."""
    pred = [
        or_(EventRegistration.user_id == user.id, EventRegistration.email == user.email),
        EventRegistration.registration_status != 'CANCELLED',
    ]
    if member:
        pred = [
            or_(
                EventRegistration.user_id == user.id,
                EventRegistration.member_id == member.id,
                EventRegistration.email == user.email,
            ),
            EventRegistration.registration_status != 'CANCELLED',
        ]

    regs = list(
        db.scalars(
            select(EventRegistration)
            .where(*pred)
            .order_by(EventRegistration.id.desc())
            .limit(10)
        ).all()
    )

    evt_ids = [r.event_id for r in regs]
    events_by_id = {
        e.id: e for e in db.scalars(select(Event).where(Event.id.in_(evt_ids))).all()
    } if evt_ids else {}

    items = []
    for r in regs:
        e = events_by_id.get(r.event_id)
        items.append({
            'registration_id': r.id,
            'event_id': r.event_id,
            'title_bn': e.title_bn if e else 'PGCB Event',
            'title_en': (e.title_en if e else None) or 'PGCB Event',
            'category': e.category if e else 'SEMINAR',
            'ticket_code': r.ticket_code,
            'registration_status': r.registration_status,
            'attendance_status': r.attendance_status,
            'event_date': e.event_date.strftime('%d %B %Y') if (e and e.event_date) else 'TBD',
            'venue': (e.venue or e.location_bn or 'পিজিসিবি অডিটোরিয়াম') if e else 'পিজিসিবি অডিটোরিয়াম',
            'pass_url': f"/member/events/{r.event_id}/pass",
        })

    return {
        'registered_count': len(items),
        'events': items,
    }


def tool_get_event_details(db: Session, user: User, event_id: int) -> dict[str, Any]:
    """Get complete details and schedule for a specific PGCB event."""
    evt = db.get(Event, event_id)
    if not evt:
        return {'found': False, 'event_id': event_id}

    return {
        'found': True,
        'id': evt.id,
        'title_bn': evt.title_bn,
        'title_en': evt.title_en,
        'category': evt.category or 'SEMINAR',
        'event_date': evt.event_date.strftime('%d %B %Y') if evt.event_date else 'TBD',
        'start_time': evt.start_time or '10:00 AM',
        'venue': evt.venue or evt.location_bn or 'পিজিসিবি অডিটোরিয়াম, ঢাকা',
        'is_online': evt.is_online,
        'fee_amount': evt.fee_amount or 0,
        'is_free': (evt.fee_amount or 0) == 0,
        'certificate_eligible': evt.certificate_eligible,
        'status': evt.status or 'PUBLISHED',
    }


def tool_get_notifications(db: Session, user: User) -> dict[str, Any]:
    """Get the member's unread and recent in-app notifications."""
    notifs = list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.id.desc())
            .limit(6)
        ).all()
    )

    unread_cnt = sum(1 for n in notifs if not getattr(n, 'is_read', False))
    items = []
    for n in notifs:
        items.append({
            'id': n.id,
            'title_bn': n.title_bn,
            'title_en': getattr(n, 'title_en', None) or n.title_bn,
            'is_read': getattr(n, 'is_read', False),
            'action_route': getattr(n, 'action_route', None) or '/member/notifications',
            'created_at': n.created_at.strftime('%d %b %Y, %I:%M %p') if n.created_at else 'Recent',
        })

    return {
        'recent_count': len(notifs),
        'unread_count': unread_cnt,
        'notifications': items,
    }


def tool_get_profile_completion(db: Session, user: User, member: Member | None) -> dict[str, Any]:
    """
    Calculate the member's profile completion percentage and actionable missing items.
    Scored out of 100 points across 10 essential fields (10 points each).
    """
    meta = db.scalar(select(MemberProfileMeta).where(MemberProfileMeta.member_id == member.id)) if member else None

    checklist = [
        ('Full Name', bool(user.name_bn or (member and member.name_bn))),
        ('Phone Number', bool(user.phone or (member and getattr(member, 'alternate_phone', None)))),
        ('Profile Photo', bool(member and member.photo_url)),
        ('National ID (NID)', bool(member and member.nid_number)),
        ('Employee ID', bool(member and member.employee_id)),
        ('Designation', bool(member and (member.designation_bn or member.designation_en))),
        ('Grid Circle', bool(member and member.circle_id)),
        ('Diploma Institution', bool(member and member.diploma_institution and member.graduation_year)),
        ('Address Information', bool(member and (member.current_address or member.permanent_address))),
        ('Emergency Contact', bool(meta and meta.emergency_contact_name and meta.emergency_contact_phone)),
    ]

    completed_items = [name for name, done in checklist if done]
    missing_items = [name for name, done in checklist if not done]
    score = int((len(completed_items) / len(checklist)) * 100)

    return {
        'completion_percentage': score,
        'completed_fields': completed_items,
        'missing_fields': missing_items,
        'is_complete': score == 100,
        'action_url': '/member/profile',
    }


# Tool Dispatch Table
TOOL_REGISTRY = {
    'get_member_profile': tool_get_member_profile,
    'get_membership_status': tool_get_membership_status,
    'get_membership_history': tool_get_membership_history,
    'get_application_status': tool_get_application_status,
    'get_pending_documents': tool_get_pending_documents,
    'get_payment_history': tool_get_payment_history,
    'get_payment_status': tool_get_payment_status,
    'get_certificates': tool_get_certificates,
    'get_digital_id': tool_get_digital_id,
    'get_registered_events': tool_get_registered_events,
    'get_event_details': tool_get_event_details,
    'get_notifications': tool_get_notifications,
    'get_profile_completion': tool_get_profile_completion,
}


# ---------------------------------------------------------------------------
# Human Support Ticket Escalation
# ---------------------------------------------------------------------------

def create_support_ticket(
    db: Session,
    user: User,
    member: Member | None,
    subject: str,
    description: str,
    conversation_id: int | None = None,
    category: str = 'GENERAL',
    priority: str = 'NORMAL',
) -> SupportTicket:
    """Escalate a conversation turn to a formal Human Support Ticket."""
    now = datetime.utcnow()
    # Generate sequential ticket number PGCB-SUP-YYYY-NNNNN
    count_today = db.scalar(
        select(func.count(SupportTicket.id)).where(
            func.strftime('%Y', SupportTicket.created_at) == str(now.year)
        )
    ) or 0
    seq = count_today + 1
    ticket_no = f"PGCB-SUP-{now.year}-{seq:05d}"

    ticket = SupportTicket(
        ticket_no=ticket_no,
        user_id=user.id,
        member_id=member.id if member else None,
        conversation_id=conversation_id,
        subject=subject.strip()[:300],
        description=description.strip(),
        category=category.upper(),
        status='OPEN',
        priority=priority.upper(),
        created_at=now,
        updated_at=now,
    )
    db.add(ticket)
    db.flush()

    audit(db, user, 'AI_ESCALATION', 'SupportTicket', ticket.id)
    db.commit()
    db.refresh(ticket)
    return ticket
