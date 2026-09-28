from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.deps import current_user

ADMIN_BASE = {'admin.stats'}
ROLE_PERMISSIONS = {
    'SUPER_ADMIN': {'*'},
    'CENTRAL_ADMIN': ADMIN_BASE | {
        'member.read', 'member.write', 'member.review', 'member.import',
        'document.read', 'document.write', 'document.review',
        'circle.read', 'circle.write',
        'content.read', 'content.write', 'content.review', 'content.publish',
        'news.read', 'news.write', 'news.publish',
        'events.read', 'events.write',
        'notice.read', 'notice.write',
        'journal.read', 'journal.write',
        'media.read', 'media.write',
        'certificate.write', 'notification.write',
        'analytics.read', 'audit.read', 'finance.read',
    },
    'CONTENT_EDITOR': ADMIN_BASE | {
        'content.read', 'content.write',
        'news.read', 'news.write',
        'media.read', 'media.write', 'events.read', 'events.write', 'certificate.write',
        'journal.read', 'journal.write', 'circle.read', 'circle.write',
        'notice.read', 'notice.write', 'document.read', 'document.write',
    },
    'CONTENT_REVIEWER': ADMIN_BASE | {
        'content.read', 'content.review',
        'news.read', 'notice.read', 'document.read',
        'events.read', 'media.read', 'journal.read',
    },
    'CONTENT_PUBLISHER': ADMIN_BASE | {
        'content.read', 'content.write', 'content.review', 'content.publish',
        'news.read', 'news.write', 'news.publish',
        'notice.read', 'notice.write',
        'document.read', 'document.write',
        'events.read', 'events.write',
        'media.read', 'media.write', 'journal.read', 'journal.write',
        'circle.read', 'circle.write', 'certificate.write',
    },
    'MEMBERSHIP_OFFICER': ADMIN_BASE | {
        'member.read', 'member.review', 'document.review', 'member.write', 'member.import',
        'circle.read', 'notification.write', 'certificate.write',
        'document.read', 'document.write', 'analytics.read',
    },
    'CIRCLE_ADMIN': ADMIN_BASE | {
        'circle.read', 'circle.write', 'member.read', 'member.review', 'document.review',
        'events.read', 'notice.read',
    },
    'FINANCE_OFFICER': ADMIN_BASE | {'finance.read', 'finance.write', 'analytics.read'},
    'CERTIFICATE_ADMIN': ADMIN_BASE | {'certificate.write', 'member.read', 'events.read'},
    'AUDITOR': ADMIN_BASE | {'audit.read', 'member.read', 'content.read', 'analytics.read'},
    'MEMBER': {'member.self', 'notification.self'},
}

# Aliases for frontend and organizational role conventions
ROLE_ALIASES = {
    'ADMIN': 'SUPER_ADMIN',
    'EDITOR': 'CONTENT_EDITOR',
    'CONTENT_ADMIN': 'CONTENT_PUBLISHER',
    'STAFF': 'MEMBERSHIP_OFFICER',
    'MEMBERSHIP_ADMIN': 'MEMBERSHIP_OFFICER',
    'FINANCE_ADMIN': 'FINANCE_OFFICER',
    'REVIEWER': 'CONTENT_REVIEWER',
    'PUBLISHER': 'CONTENT_PUBLISHER',
    'USER': 'MEMBER',
}


def canonical_role(role: str) -> str:
    return ROLE_ALIASES.get(role, role)


def has_permission(role: str, permission: str) -> bool:
    c_role = canonical_role(role)
    permissions = ROLE_PERMISSIONS.get(c_role, set())
    return '*' in permissions or permission in permissions


def get_admin_circle_scope(user, db: Session) -> int | None:
    """Return the assigned circle_id if the user is a CIRCLE_ADMIN, else None (unrestricted)."""
    if canonical_role(getattr(user, 'role', '')) != 'CIRCLE_ADMIN':
        return None
    from app.models import Member, SiteSetting
    m = db.scalar(select(Member).where(Member.user_id == user.id))
    if m and m.circle_id:
        return m.circle_id
    setting = db.scalar(select(SiteSetting).where(SiteSetting.key == f'circle_admin_user_{user.id}'))
    if setting and setting.value and str(setting.value).isdigit():
        return int(setting.value)
    return -1  # Unassigned CIRCLE_ADMIN has no circle access


def require_permission(permission: str):
    def dependency(user=Depends(current_user)):
        if not has_permission(user.role, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient permissions')
        return user
    return dependency

