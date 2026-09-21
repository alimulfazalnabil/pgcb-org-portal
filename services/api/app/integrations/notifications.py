from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.models import Notification, NotificationDelivery, User

@dataclass
class DeliveryResult:
    status: str
    provider: str
    provider_message_id: str | None = None
    error: str | None = None


def create_in_app(db: Session, user: User, title_bn: str, body_bn: str, notification_type: str = 'GENERAL') -> Notification:
    item = Notification(user_id=user.id, title_bn=title_bn, body_bn=body_bn, notification_type=notification_type)
    db.add(item)
    db.flush()
    return item


def deliver_email(recipient: str, subject: str, body: str) -> DeliveryResult:
    host = os.getenv('SMTP_HOST')
    if not host:
        return DeliveryResult('SKIPPED', 'NONE', error='SMTP_HOST not configured')
    try:
        msg = EmailMessage()
        msg['From'] = os.getenv('SMTP_FROM', 'noreply@example.org')
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.set_content(body)
        port = int(os.getenv('SMTP_PORT', '587'))
        username = os.getenv('SMTP_USERNAME')
        password = os.getenv('SMTP_PASSWORD')
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(msg)
        return DeliveryResult('SENT', 'SMTP')
    except Exception as exc:
        return DeliveryResult('FAILED', 'SMTP', error=str(exc)[:500])


def deliver_sms(recipient: str, body: str) -> DeliveryResult:
    if not os.getenv('SMS_PROVIDER_URL'):
        return DeliveryResult('SKIPPED', 'NONE', error='SMS_PROVIDER_URL not configured')
    return DeliveryResult('QUEUED', os.getenv('SMS_PROVIDER_NAME', 'CUSTOM_HTTP'))


def record_delivery(db: Session, notification_id: int | None, channel: str, recipient: str, result: DeliveryResult) -> NotificationDelivery:
    item = NotificationDelivery(notification_id=notification_id, channel=channel, recipient=recipient, status=result.status, provider=result.provider, provider_message_id=result.provider_message_id, error_message=result.error, sent_at=datetime.utcnow() if result.status == 'SENT' else None)
    db.add(item)
    return item
