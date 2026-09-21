from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.notifications import DeliveryResult, deliver_email, deliver_sms
from app.models import Notification, NotificationDelivery

MAX_ATTEMPTS = 5
RETRY_DELAYS = (1, 5, 15, 60, 180)


def queue_delivery(db: Session, notification_id: int | None, channel: str, recipient: str) -> NotificationDelivery:
    key = f'{notification_id or 0}:{channel}:{recipient}:{datetime.utcnow().strftime("%Y%m%d%H%M%S%f")}'
    item = NotificationDelivery(notification_id=notification_id, channel=channel, recipient=recipient, status='QUEUED', idempotency_key=key)
    db.add(item)
    db.flush()
    return item


def process_due_deliveries(db: Session, limit: int = 50) -> int:
    now = datetime.utcnow()
    rows = db.scalars(
        select(NotificationDelivery)
        .where(NotificationDelivery.status.in_(['QUEUED', 'RETRYING']))
        .where((NotificationDelivery.next_attempt_at.is_(None)) | (NotificationDelivery.next_attempt_at <= now))
        .order_by(NotificationDelivery.created_at)
        .limit(limit)
    ).all()
    processed = 0
    for delivery in rows:
        notification = db.get(Notification, delivery.notification_id) if delivery.notification_id else None
        body = notification.body_bn if notification else ''
        subject = notification.title_bn if notification else 'PGCB Portal Notification'
        delivery.status = 'PROCESSING'
        delivery.attempts += 1
        delivery.last_attempt_at = now
        db.flush()
        if delivery.channel == 'EMAIL':
            result = deliver_email(delivery.recipient, subject, body)
        elif delivery.channel == 'SMS':
            result = deliver_sms(delivery.recipient, body)
        else:
            result = DeliveryResult('SENT', 'IN_APP')
        delivery.provider = result.provider
        delivery.provider_message_id = result.provider_message_id
        delivery.error_message = result.error
        if result.status in {'SENT', 'SKIPPED'}:
            delivery.status = result.status
            delivery.next_attempt_at = None
            delivery.sent_at = now if result.status == 'SENT' else None
        elif delivery.attempts >= MAX_ATTEMPTS:
            delivery.status = 'FAILED'
            delivery.next_attempt_at = None
        else:
            delay_minutes = RETRY_DELAYS[min(delivery.attempts - 1, len(RETRY_DELAYS) - 1)]
            delivery.status = 'RETRYING'
            delivery.next_attempt_at = now + timedelta(minutes=delay_minutes)
        processed += 1
    db.commit()
    return processed
