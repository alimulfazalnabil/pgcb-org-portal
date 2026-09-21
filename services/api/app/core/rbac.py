from fastapi import Depends, HTTPException, status
from app.core.deps import current_user

ADMIN_BASE = {'admin.stats'}
ROLE_PERMISSIONS = {
    'SUPER_ADMIN': {'*'},
    'CONTENT_EDITOR': ADMIN_BASE | {
        'content.read', 'content.write', 'content.publish',
        'media.read', 'media.write', 'events.read', 'events.write', 'certificate.write',
        'journal.read', 'journal.write', 'circle.read', 'circle.write',
    },
    'MEMBERSHIP_OFFICER': ADMIN_BASE | {
        'member.read', 'member.review', 'document.review', 'member.write',
        'circle.read', 'notification.write', 'certificate.write',
    },
    'CIRCLE_ADMIN': ADMIN_BASE | {'circle.read', 'circle.write', 'member.read'},
    'FINANCE_OFFICER': ADMIN_BASE | {'finance.read', 'finance.write'},
    'AUDITOR': ADMIN_BASE | {'audit.read', 'member.read', 'content.read'},
    'MEMBER': {'member.self', 'notification.self'},
}


def has_permission(role: str, permission: str) -> bool:
    permissions = ROLE_PERMISSIONS.get(role, set())
    return '*' in permissions or permission in permissions


def require_permission(permission: str):
    def dependency(user=Depends(current_user)):
        if not has_permission(user.role, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient permissions')
        return user
    return dependency
