from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models import AuditLog, Member, Notification, User
from app.core.config import settings

try:
    BASE_STORAGE = Path(settings.storage_root).resolve()
    BASE_STORAGE.mkdir(parents=True, exist_ok=True)
except Exception:
    BASE_STORAGE = Path(__file__).resolve().parents[1] / 'storage'
    BASE_STORAGE.mkdir(parents=True, exist_ok=True)

ALLOWED_DOC_TYPES = {'NID', 'CERTIFICATE', 'PHOTO', 'OTHER'}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {'application/pdf', 'image/jpeg', 'image/png', 'image/webp'}

def audit(db: Session, user: User | None, action: str, entity: str, entity_id: str | int | None = None, ip: str | None = None):
    db.add(AuditLog(user_id=user.id if user else None, action=action, entity=entity, entity_id=str(entity_id) if entity_id is not None else None, ip_address=ip))

def notify(db: Session, user_id: int, title_bn: str, body_bn: str, notification_type: str = 'GENERAL'):
    db.add(Notification(user_id=user_id, title_bn=title_bn, body_bn=body_bn, notification_type=notification_type))

def next_membership_id(db: Session) -> str:
    # Return the next sequential membership id for the current year.
    # Derives the sequence from the highest existing suffix rather than a row
    # count, so deletions or gaps cannot make the generated id collide with an
    # existing one (membership_id is uniquely constrained).
    year = datetime.utcnow().year
    prefix = f'PGD-{year}-'
    latest = db.scalar(
        select(func.max(Member.membership_id)).where(Member.membership_id.like(prefix + '%'))
    )
    sequence = 0
    if latest:
        try:
            sequence = int(latest.rsplit('-', 1)[1])
        except (IndexError, ValueError):
            sequence = 0
    return f'{prefix}{sequence + 1:04d}'

def membership_dates():
    now = datetime.utcnow()
    return now, now + timedelta(days=365)
