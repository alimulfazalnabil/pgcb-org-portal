from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Member, MembershipRenewal, MembershipReminder, Notification

class _ReminderOffsetsTuple(tuple):
    def __contains__(self, item: object) -> bool:
        if isinstance(item, int):
            return any(days == item for days, _ in self)
        return super().__contains__(item)


RENEWAL_DAYS = 365
REMINDER_OFFSETS = _ReminderOffsetsTuple((
    (60, '60_DAY'),
    (30, '30_DAY'),
    (7, '7_DAY'),
    (1, '1_DAY'),
    (0, 'EXPIRY_DAY'),
))


def due_membership_events(
    status: str,
    validity_date: datetime | None,
    now: datetime | None = None,
) -> list[tuple[str, str, str]]:
    now = now or datetime.utcnow()
    if status != 'ACTIVE' or not validity_date:
        return []
    events: list[tuple[str, str, str]] = []
    for days, _ in REMINDER_OFFSETS:
        target = validity_date - timedelta(days=days)
        if target.date() == now.date():
            key = f'REMINDER_{days}D'
            if days == 0:
                title_bn = 'আজ আপনার সদস্যতার মেয়াদ শেষ হচ্ছে'
                body_bn = 'আপনার পিজিসিবি সদস্যতার মেয়াদ আজ শেষ হচ্ছে। সদস্যপদ সক্রিয় রাখতে এখনই পোর্টাল থেকে নবায়ন সম্পন্ন করুন।'
            else:
                title_bn = 'সদস্যতার মেয়াদ শেষ হওয়ার স্মরণিকা'
                body_bn = f'আপনার সদস্যতার মেয়াদ {days} দিনের মধ্যে শেষ হবে ({validity_date.strftime("%d-%m-%Y")})। অনুগ্রহ করে নবায়ন করুন।'
            events.append((key, title_bn, body_bn))
    if validity_date < now and validity_date.date() != now.date():
        events.append((
            'EXPIRED',
            'সদস্যতার মেয়াদ শেষ হয়েছে',
            'আপনার সদস্যতার মেয়াদ শেষ হয়েছে। নবায়ন সম্পন্ন করে পুনরায় সক্রিয় করুন।',
        ))
    return events


RENEWAL_PERIODS: dict[str, dict[str, int | str]] = {
    'RENEWAL_1YR': {
        'code': 'RENEWAL_1YR',
        'title_bn': '১ বছর মেয়াদী বার্ষিক নবায়ন',
        'title_en': '1 Year Annual Membership Renewal',
        'days': 365,
        'years': 1,
        'amount': 2000,
    },
    'ANNUAL_STANDARD': {
        'code': 'ANNUAL_STANDARD',
        'title_bn': '১ বছর মেয়াদী সাধারণ সদস্যপদ নবায়ন',
        'title_en': '1 Year Standard Membership Renewal',
        'days': 365,
        'years': 1,
        'amount': 2000,
    },
    'RENEWAL': {
        'code': 'RENEWAL',
        'title_bn': 'বার্ষিক সদস্যপদ নবায়ন (১ বছর)',
        'title_en': 'Annual Membership Renewal (1 Year)',
        'days': 365,
        'years': 1,
        'amount': 2000,
    },
    'RENEWAL_2YR': {
        'code': 'RENEWAL_2YR',
        'title_bn': '২ বছর মেয়াদী সদস্যপদ নবায়ন',
        'title_en': '2 Years Extended Membership Renewal',
        'days': 730,
        'years': 2,
        'amount': 4000,
    },
    'LIFE': {
        'code': 'LIFE',
        'title_bn': 'আজীবন সদস্যপদ আপগ্রেড',
        'title_en': 'Lifetime Membership Upgrade',
        'days': 18250,
        'years': 50,
        'amount': 10000,
    },
}


def resolve_renewal_days(plan_code: str | None = None, amount: int | None = None) -> int:
    if plan_code:
        norm = plan_code.strip().upper()
        if norm in RENEWAL_PERIODS:
            return int(RENEWAL_PERIODS[norm]['days'])
    if amount is not None:
        if int(amount) >= 10000:
            return 18250
        if int(amount) == 4000:
            return 730
    return RENEWAL_DAYS


def renew_membership(
    db: Session,
    member: Member,
    payment_id: int | None,
    amount: int,
    currency: str = 'BDT',
    days: int | None = None,
    plan_code: str | None = None,
) -> MembershipRenewal:
    now = datetime.utcnow()
    previous = member.validity_date
    base = previous if previous and previous > now else now
    extension_days = days if days and days > 0 else resolve_renewal_days(plan_code, amount)
    new_validity = base + timedelta(days=extension_days)
    member.status = 'ACTIVE'
    if (plan_code and plan_code.strip().upper() in ('LIFE', 'LIFETIME')) or int(amount) >= 10000:
        member.membership_type = 'LIFE'
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
            db.add(
                MembershipReminder(
                    member_id=member.id,
                    validity_date=member.validity_date,
                    reminder_type=reminder_type,
                    sent_at=now,
                )
            )
            if days == 0:
                title_bn = 'আজ আপনার সদস্যতার মেয়াদ শেষ হচ্ছে'
                body_bn = 'আপনার পিজিসিবি সদস্যতার মেয়াদ আজ শেষ হচ্ছে। সদস্যপদ সক্রিয় রাখতে এখনই পোর্টাল থেকে নবায়ন সম্পন্ন করুন।'
            else:
                title_bn = 'সদস্যতার মেয়াদ শেষ হওয়ার স্মরণিকা'
                body_bn = f'আপনার সদস্যতার মেয়াদ {days} দিনের মধ্যে শেষ হবে ({member.validity_date.strftime("%d-%m-%Y")})। অনুগ্রহ করে নবায়ন করুন।'
            db.add(
                Notification(
                    user_id=member.user_id,
                    title_bn=title_bn,
                    body_bn=body_bn,
                    notification_type='MEMBERSHIP_EXPIRY',
                )
            )
            count += 1

    expired = db.scalars(
        select(Member).where(
            Member.validity_date.is_not(None),
            Member.validity_date < now,
            Member.status == 'ACTIVE',
        )
    ).all()
    for member in expired:
        if member.validity_date and member.validity_date.date() == now.date():
            # Keep active through the end of the expiry calendar day while EXPIRY_DAY reminder is active
            continue
        member.status = 'EXPIRED'
        db.add(
            Notification(
                user_id=member.user_id,
                title_bn='সদস্যতার মেয়াদ শেষ হয়েছে',
                body_bn='আপনার সদস্যতার মেয়াদ শেষ হয়েছে। নবায়ন সম্পন্ন করে পুনরায় সক্রিয় করুন।',
                notification_type='MEMBERSHIP_EXPIRED',
            )
        )
        count += 1
    return count
