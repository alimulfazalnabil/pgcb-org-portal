"""
Institutional Notification Service & Delivery Orchestration for PGCB Organization Portal.
Supports multi-channel notifications (In-App, Email, SMS), actionable deep-links, preference filtering,
and automated reminder schedules for events and membership validity.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import json
import logging
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Event,
    EventRegistration,
    Member,
    MembershipReminder,
    Notification,
    NotificationDelivery,
    NotificationPreference,
    SiteSetting,
    User,
)
from app.domain.notifications import queue_delivery

logger = logging.getLogger('pgcb.notifications')

DEFAULT_PREFERENCES = {
    'MEMBERSHIP': {'in_app': True, 'email': True, 'sms': True},
    'EVENTS': {'in_app': True, 'email': True, 'sms': False},
    'PAYMENTS': {'in_app': True, 'email': True, 'sms': True},
    'SYSTEM': {'in_app': True, 'email': True, 'sms': False},
    'ANNOUNCEMENTS': {'in_app': True, 'email': False, 'sms': False},
}


class NotificationService:
    @staticmethod
    def get_user_preferences(db: Session, user_id: int) -> dict[str, dict[str, bool]]:
        """Retrieve preference matrix for all standard categories for a given user."""
        prefs = {cat: dict(vals) for cat, vals in DEFAULT_PREFERENCES.items()}
        rows = db.scalars(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        ).all()
        for r in rows:
            cat = r.category.upper()
            if cat in prefs:
                prefs[cat] = {
                    'in_app': bool(r.in_app),
                    'email': bool(r.email),
                    'sms': bool(r.sms),
                }
            else:
                prefs[cat] = {
                    'in_app': bool(r.in_app),
                    'email': bool(r.email),
                    'sms': bool(r.sms),
                }
        return prefs

    @staticmethod
    def update_user_preferences(
        db: Session,
        user_id: int,
        updates: dict[str, dict[str, bool]] | list[dict],
    ) -> dict[str, dict[str, bool]]:
        """Update or insert category preference rows for user."""
        if isinstance(updates, list):
            dict_updates = {}
            for item in updates:
                c = item.get('category')
                if c:
                    dict_updates[c.upper()] = {
                        'in_app': bool(item.get('in_app', True)),
                        'email': bool(item.get('email', True)),
                        'sms': bool(item.get('sms', False)),
                    }
            updates = dict_updates

        for category, channels in updates.items():
            cat = category.strip().upper()
            row = db.scalar(
                select(NotificationPreference).where(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.category == cat,
                )
            )
            if not row:
                row = NotificationPreference(
                    user_id=user_id,
                    category=cat,
                    in_app=bool(channels.get('in_app', True)),
                    email=bool(channels.get('email', True)),
                    sms=bool(channels.get('sms', False)),
                )
                db.add(row)
            else:
                if 'in_app' in channels:
                    row.in_app = bool(channels['in_app'])
                if 'email' in channels:
                    row.email = bool(channels['email'])
                if 'sms' in channels:
                    row.sms = bool(channels['sms'])
        db.commit()
        return NotificationService.get_user_preferences(db, user_id)

    @staticmethod
    def send_notification(
        db: Session,
        user_id: int,
        title_bn: str,
        body_bn: str,
        notification_type: str = 'GENERAL',
        title_en: str | None = None,
        body_en: str | None = None,
        action_route: str | None = None,
        action_label: str | None = None,
        action_label_bn: str | None = None,
        priority: str = 'NORMAL',
        expires_at: datetime | None = None,
        entity_type: str | None = None,
        entity_id: str | int | None = None,
        extra_data: dict | None = None,
    ) -> Notification | None:
        """
        Dispatches multi-channel notification based on user preferences.
        Returns the created in-app Notification object if in_app is enabled, else None.
        """
        user = db.get(User, user_id)
        if not user or not user.is_active:
            return None

        # Resolve category mapping for preferences
        norm_type = notification_type.upper()
        pref_category = 'GENERAL'
        if norm_type in ('MEMBERSHIP', 'APPLICATION', 'RENEWAL'):
            pref_category = 'MEMBERSHIP'
        elif norm_type in ('EVENT', 'EVENTS', 'REGISTRATION'):
            pref_category = 'EVENTS'
        elif norm_type in ('PAYMENT', 'RECEIPT', 'INVOICE'):
            pref_category = 'PAYMENTS'
        elif norm_type in ('SECURITY', 'SYSTEM', 'PASSWORD'):
            pref_category = 'SYSTEM'
        elif norm_type in ('ANNOUNCEMENT', 'CIRCULAR', 'NOTICE'):
            pref_category = 'ANNOUNCEMENTS'
        else:
            pref_category = 'SYSTEM'

        prefs = NotificationService.get_user_preferences(db, user_id)
        cat_prefs = prefs.get(pref_category, {'in_app': True, 'email': True, 'sms': False})

        # Format actionable payload
        data_json = extra_data.copy() if extra_data else {}
        if action_route:
            data_json['action'] = {
                'route': action_route,
                'label': action_label or 'View Details',
                'label_bn': action_label_bn or 'বিস্তারিত দেখুন',
            }
        if entity_type:
            data_json['entity_type'] = entity_type
        if entity_id is not None:
            data_json['entity_id'] = str(entity_id)

        in_app_notif: Notification | None = None
        if cat_prefs.get('in_app', True):
            in_app_notif = Notification(
                user_id=user_id,
                title_bn=title_bn,
                title_en=title_en or title_bn,
                body_bn=body_bn,
                body_en=body_en or body_bn,
                notification_type=notification_type,
                data_json=data_json if data_json else None,
                priority=priority,
                expires_at=expires_at,
                created_at=datetime.utcnow(),
            )
            db.add(in_app_notif)
            db.flush()

        # Queue Email if opted in and email available
        if cat_prefs.get('email', True) and user.email:
            try:
                queue_delivery(
                    db=db,
                    notification_id=in_app_notif.id if in_app_notif else None,
                    channel='EMAIL',
                    recipient=user.email,
                )
            except Exception as exc:
                logger.warning(f"Failed to queue email notification: {exc}")

        # Queue SMS if opted in and phone available
        if cat_prefs.get('sms', False) and user.phone:
            try:
                queue_delivery(
                    db=db,
                    notification_id=in_app_notif.id if in_app_notif else None,
                    channel='SMS',
                    recipient=user.phone,
                )
            except Exception as exc:
                logger.warning(f"Failed to queue SMS notification: {exc}")

        db.commit()
        if in_app_notif:
            db.refresh(in_app_notif)
        return in_app_notif

    @staticmethod
    def run_event_reminders(db: Session) -> dict[str, int]:
        """
        Background scheduler task: checks upcoming events and sends 7d, 3d, 1d, and 1h reminders
        to confirmed registered members.
        """
        now = datetime.utcnow()
        sent_counts = {'7d': 0, '3d': 0, '1d': 0, '1h': 0}

        windows = [
            ('7d', timedelta(days=6, hours=12), timedelta(days=7, hours=12), '৭ দিন বাকি', '7 days remaining'),
            ('3d', timedelta(days=2, hours=12), timedelta(days=3, hours=12), '৩ দিন বাকি', '3 days remaining'),
            ('1d', timedelta(hours=20), timedelta(hours=28), 'আগামীকাল অনুষ্ঠিত হবে', 'Tomorrow'),
            ('1h', timedelta(minutes=45), timedelta(minutes=75), '১ ঘণ্টা পর শুরু হবে', 'Starting in 1 hour'),
        ]

        for interval_key, delta_min, delta_max, tag_bn, tag_en in windows:
            target_start = now + delta_min
            target_end = now + delta_max

            events = db.scalars(
                select(Event).where(
                    Event.is_published == True,
                    Event.status.in_(['PUBLISHED', 'REGISTRATION_OPEN', 'REGISTRATION_CLOSED']),
                    Event.event_date >= target_start,
                    Event.event_date <= target_end,
                )
            ).all()

            for evt in events:
                registrations = db.scalars(
                    select(EventRegistration).where(
                        EventRegistration.event_id == evt.id,
                        EventRegistration.registration_status == 'CONFIRMED',
                    )
                ).all()

                for reg in registrations:
                    if not reg.user_id:
                        continue
                    # Check idempotency so member only receives 1 reminder for this interval
                    reminder_tag = f"EVENT_REMINDER_{evt.id}_{interval_key}"
                    already_sent = db.scalar(
                        select(Notification).where(
                            Notification.user_id == reg.user_id,
                            Notification.notification_type == 'EVENT_REMINDER',
                            Notification.data_json.is_not(None),
                        )
                    )
                    # Use specific marker in data_json
                    has_reminded = False
                    if already_sent and already_sent.data_json:
                        if already_sent.data_json.get('reminder_tag') == reminder_tag:
                            has_reminded = True

                    if not has_reminded:
                        evt_title = evt.title_bn
                        venue_str = evt.venue or evt.location_bn or 'নির্ধারিত ভেন্যু'
                        NotificationService.send_notification(
                            db=db,
                            user_id=reg.user_id,
                            title_bn=f"ইভেন্ট স্মরণিকা: {evt_title} ({tag_bn})",
                            title_en=f"Event Reminder: {evt.title_en or evt_title} ({tag_en})",
                            body_bn=f"আসন্ন ইভেন্ট '{evt_title}' {tag_bn}। ভেন্যু: {venue_str}। আপনার ডিজিটাল টিকিট সংরক্ষিত রাখুন।",
                            body_en=f"Upcoming event '{evt.title_en or evt_title}' is {tag_en}. Venue: {evt.venue or evt.location_en or venue_str}. Keep your event pass ready.",
                            notification_type='EVENT_REMINDER',
                            action_route=f"/member/events/{evt.id}/pass",
                            action_label="View Event Pass",
                            action_label_bn="ইভেন্ট পাস দেখুন",
                            priority='HIGH' if interval_key in ('1d', '1h') else 'NORMAL',
                            entity_type='EVENT',
                            entity_id=evt.id,
                            extra_data={'reminder_tag': reminder_tag, 'event_id': evt.id, 'ticket_code': reg.ticket_code},
                        )
                        sent_counts[interval_key] += 1

        return sent_counts

    @staticmethod
    def run_membership_renewal_reminders(db: Session) -> dict[str, int]:
        """
        Background scheduler task: checks members expiring in 60d, 30d, 7d, 1d
        and sends official renewal notifications.
        """
        now = datetime.utcnow()
        sent_counts = {'60d': 0, '30d': 0, '7d': 0, '1d': 0}

        windows = [
            ('60d', 60, '৬০ দিন বাকি', '60 days remaining'),
            ('30d', 30, '৩০ দিন বাকি', '30 days remaining'),
            ('7d', 7, '৭ দিন বাকি', '7 days remaining'),
            ('1d', 1, 'আগামীকাল মেয়াদ শেষ হবে', 'Expires tomorrow'),
        ]

        for interval_key, days, tag_bn, tag_en in windows:
            target_date = now.date() + timedelta(days=days)
            members = db.scalars(
                select(Member).where(
                    Member.status == 'ACTIVE',
                    Member.validity_date.is_not(None),
                    func.date(Member.validity_date) == target_date,
                )
            ).all()

            for m in members:
                if not m.user_id:
                    continue
                # Check MembershipReminder model
                existing = db.scalar(
                    select(MembershipReminder).where(
                        MembershipReminder.member_id == m.id,
                        MembershipReminder.reminder_type == interval_key,
                        func.date(MembershipReminder.validity_date) == target_date,
                    )
                )
                if not existing:
                    db.add(
                        MembershipReminder(
                            member_id=m.id,
                            validity_date=m.validity_date,
                            reminder_type=interval_key,
                            sent_at=now,
                        )
                    )
                    NotificationService.send_notification(
                        db=db,
                        user_id=m.user_id,
                        title_bn=f"সদস্যপদ নবায়ন স্মরণিকা ({tag_bn})",
                        title_en=f"Membership Renewal Reminder ({tag_en})",
                        body_bn=f"আপনার সদস্যপদ আইডি {m.membership_id}-এর মেয়াদ শেষ হতে {tag_bn}। নিরবচ্ছিন্ন সুবিধার জন্য এখনই অনলাইনে নবায়ন সম্পন্ন করুন।",
                        body_en=f"Your membership ID {m.membership_id} will expire in {tag_en}. Renew your membership online today to retain full member benefits.",
                        notification_type='MEMBERSHIP',
                        action_route="/member/membership",
                        action_label="Renew Membership",
                        action_label_bn="সদস্যপদ নবায়ন করুন",
                        priority='HIGH' if interval_key in ('7d', '1d') else 'NORMAL',
                        entity_type='MEMBER',
                        entity_id=m.id,
                    )
                    sent_counts[interval_key] += 1
            db.commit()

        return sent_counts
