from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Member, MembershipRenewal, MembershipReminder, Notification

RENEWAL_DAYS = 365
REMINDER_OFFSETS = ((30, '30_DAY'), (7, '7_DAY'), (1, '1_DAY'))


def renew_membership(db: Session, member: Member, payment_id: int | None, amount: int, currency: str = 'BDT') -> MembershipRenewal:
    now = datetime.utcnow()
    previous = member.validity_date
    base = previous if previous and previous > now else now
    new_validity = base + timedelta(days=RENEWAL_DAYS)
    member.status = 'ACTIVE'
    member.issue_date = member.issue_date or now
    member.validity_date = new_validity
    renewal = MembershipRenewal(
        member_id=member.id,
        payment_id=payment_id,
        previous_validity_date=previous,
        new_validity_date=new_validity,
        amount=amount,
        currency=currency,
        status='COMPLETED',
    )
    db.add(renewal)
    db.flush()
    return renewal


def queue_membership_reminders(db: Session, now: datetime | None = None) -> int:
    now = now or datetime.utcnow()
    count = 0
    rows = db.scalars(select(Member).where(Member.validity_date.is_not(None), Member.status == 'ACTIVE')).all()
    for member in rows:
        if not member.validity_date:
            continue
        for days, reminder_type in REMINDER_OFFSETS:
            target = member.validity_date - timedelta(days=days)
            if target.date() != now.date():
                continue
            existing = db.scalar(
                select(MembershipReminder).where(
                    MembershipReminder.member_id == member.id,
                    MembershipReminder.validity_date == member.validity_date,
                    MembershipReminder.reminder_type == reminder_type,
                )
            )
            if existing:
                continue
            db.add(MembershipReminder(member_id=member.id, validity_date=member.validity_date, reminder_type=reminder_type))
            db.add(Notification(
                user_id=member.user_id,
                title_bn='সদস্যতার মেয়াদ শেষ হওয়ার স্মরণিকা',
                body_bn=f'আপনার সদস্যতার মেয়াদ {days} দিনের মধ্যে শেষ হবে। অনুগ্রহ করে নবায়ন করুন।',
                notification_type='MEMBERSHIP_EXPIRY',
            ))
            count += 1

    expired = db.scalars(select(Member).where(Member.validity_date.is_not(None), Member.validity_date < now, Member.status == 'ACTIVE')).all()
    for member in expired:
        member.status = 'EXPIRED'
        db.add(Notification(
            user_id=member.user_id,
            title_bn='সদস্যতার মেয়াদ শেষ হয়েছে',
            body_bn='আপনার সদস্যতার মেয়াদ শেষ হয়েছে। নবায়ন সম্পন্ন করে পুনরায় সক্রিয় করুন।',
            notification_type='MEMBERSHIP_EXPIRED',
        ))
        count += 1
    return count
