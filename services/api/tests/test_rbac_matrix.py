"""
Automated RBAC Permission Matrix Test Suite.
Validates object-level authorization across all 6 administrative roles and regular members.
"""

from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.models import User, Circle, Member
from app.core.config import settings
from app.core.security import hash_password, create_token
from app.db.session import SessionLocal

client = TestClient(app)

ROLES = [
    'SUPER_ADMIN',
    'CONTENT_EDITOR',
    'MEMBERSHIP_OFFICER',
    'CIRCLE_ADMIN',
    'FINANCE_OFFICER',
    'AUDITOR',
    'MEMBER',
]


def _get_auth_for_role(role: str) -> dict:
    with SessionLocal() as db:
        email = f"rbac_{role.lower()}@example.org"
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                email=email,
                password_hash=hash_password("Pass123!"),
                name_bn=f"রোল {role}",
                name_en=f"Role {role}",
                role=role,
                is_active=True,
                email_verified=True,
            )
            db.add(user)
            db.flush()
            if role == 'MEMBER':
                circle = db.scalar(select(Circle))
                db.add(Member(user_id=user.id, membership_id=f"PGD-RBAC-{user.id}", status='ACTIVE', circle_id=circle.id if circle else None))
            db.commit()
            db.refresh(user)
        token, _ = create_token(user.id, roles=[role])
        return {
            'cookies': {settings.cookie_name: token, 'access_token': token},
            'headers': {'Authorization': f'Bearer {token}'},
        }


def test_member_blocked_from_all_admin_routes():
    auth = _get_auth_for_role('MEMBER')

    # All admin routes must return 403 Forbidden for regular members
    assert client.get('/api/v1/admin/stats', **auth).status_code == 403
    assert client.get('/api/v1/admin/members', **auth).status_code == 403
    assert client.get('/api/v1/admin/users', **auth).status_code == 403
    assert client.get('/api/v1/admin/audit', **auth).status_code == 403
    assert client.get('/api/v1/admin/payments', **auth).status_code == 403


def test_content_editor_permissions():
    auth = _get_auth_for_role('CONTENT_EDITOR')

    # Allowed: notices, circulars, stats
    assert client.get('/api/v1/admin/stats', **auth).status_code == 200
    assert client.get('/api/v1/admin/circulars', **auth).status_code == 200

    # Blocked: users, finance, member review
    assert client.get('/api/v1/admin/users', **auth).status_code == 403
    assert client.get('/api/v1/admin/payments', **auth).status_code == 403
    assert client.post('/api/v1/admin/members/999/review?action=APPROVE', **auth).status_code == 403


def test_membership_officer_permissions():
    auth = _get_auth_for_role('MEMBERSHIP_OFFICER')

    # Allowed: stats, member read
    assert client.get('/api/v1/admin/stats', **auth).status_code == 200
    assert client.get('/api/v1/admin/members', **auth).status_code == 200

    # Blocked: users, finance
    assert client.get('/api/v1/admin/users', **auth).status_code == 403
    assert client.get('/api/v1/admin/payments', **auth).status_code == 403


def test_finance_officer_permissions():
    auth = _get_auth_for_role('FINANCE_OFFICER')

    # Allowed: stats, finance
    assert client.get('/api/v1/admin/stats', **auth).status_code == 200
    assert client.get('/api/v1/admin/payments', **auth).status_code == 200

    # Blocked: users, content modification
    assert client.get('/api/v1/admin/users', **auth).status_code == 403
    assert client.post('/api/v1/admin/circulars', json={'title_bn': 'Test'}, **auth).status_code == 403


def test_auditor_permissions():
    auth = _get_auth_for_role('AUDITOR')

    # Allowed: stats, audit logs, member read
    assert client.get('/api/v1/admin/stats', **auth).status_code == 200
    assert client.get('/api/v1/admin/audit', **auth).status_code == 200
    assert client.get('/api/v1/admin/members', **auth).status_code == 200

    # Blocked: mutations (users write, content write)
    assert client.get('/api/v1/admin/users', **auth).status_code == 403
    assert client.post('/api/v1/admin/circulars', json={'title_bn': 'Test'}, **auth).status_code == 403


def test_super_admin_unrestricted_access():
    auth = _get_auth_for_role('SUPER_ADMIN')

    # Allowed: everything
    assert client.get('/api/v1/admin/stats', **auth).status_code == 200
    assert client.get('/api/v1/admin/members', **auth).status_code == 200
    assert client.get('/api/v1/admin/users', **auth).status_code == 200
    assert client.get('/api/v1/admin/audit', **auth).status_code == 200
    assert client.get('/api/v1/admin/payments', **auth).status_code == 200
