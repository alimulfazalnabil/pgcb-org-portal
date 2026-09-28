from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.core.rbac import has_permission
from app.db.session import SessionLocal
from app.models import User

client = TestClient(app)


def test_6_role_rbac_permission_matrix():
    # 1. Member
    assert has_permission('MEMBER', 'member.self') is True
    assert has_permission('MEMBER', 'admin.stats') is False
    assert has_permission('MEMBER', 'finance.write') is False

    # 2. Circle Admin
    assert has_permission('CIRCLE_ADMIN', 'circle.write') is True
    assert has_permission('CIRCLE_ADMIN', 'member.review') is True
    assert has_permission('CIRCLE_ADMIN', 'finance.write') is False

    # 2b. Membership Admin
    assert has_permission('MEMBERSHIP_ADMIN', 'member.read') is True
    assert has_permission('MEMBERSHIP_ADMIN', 'member.review') is True
    assert has_permission('MEMBERSHIP_ADMIN', 'document.review') is True
    assert has_permission('MEMBERSHIP_ADMIN', 'finance.write') is False

    # 3. Finance Admin
    assert has_permission('FINANCE_ADMIN', 'finance.read') is True
    assert has_permission('FINANCE_ADMIN', 'finance.write') is True
    assert has_permission('FINANCE_ADMIN', 'content.publish') is False

    # 4. Content Admin
    assert has_permission('CONTENT_ADMIN', 'content.publish') is True
    assert has_permission('CONTENT_ADMIN', 'news.publish') is True
    assert has_permission('CONTENT_ADMIN', 'finance.write') is False

    # 5. Central Admin
    assert has_permission('CENTRAL_ADMIN', 'member.review') is True
    assert has_permission('CENTRAL_ADMIN', 'content.publish') is True
    assert has_permission('CENTRAL_ADMIN', 'audit.read') is True

    # 6. Super Admin
    assert has_permission('SUPER_ADMIN', 'finance.write') is True
    assert has_permission('SUPER_ADMIN', 'any.custom.permission') is True


def test_member_cannot_access_admin_endpoints():
    ts = int(datetime.utcnow().timestamp() * 1000)
    email = f'rbac_member_{ts}@pgcb.gov.bd'
    password = 'RbacUserPass123!'
    reg = client.post(
        '/api/v1/auth/register',
        json={
            'name_bn': 'আরবিএসি সদস্য',
            'name_en': 'RBAC Member',
            'email': email,
            'phone': f'017{ts % 100000000:08d}',
            'password': password,
            'designation_bn': 'উপ-সহকারী প্রকৌশলী',
        },
    )
    assert reg.status_code in (200, 201)
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.email == email))
        u.email_verified = True
        db.commit()

    login = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    assert login.status_code == 200
    token = login.cookies.get('pgcb_access_token') or login.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}

    for admin_endpoint in ('/api/v1/admin/stats', '/api/v1/admin/members', '/api/v1/admin/payments'):
        res = client.get(admin_endpoint, headers=headers)
        assert res.status_code == 403, f'Expected 403 on {admin_endpoint}, got {res.status_code}'
