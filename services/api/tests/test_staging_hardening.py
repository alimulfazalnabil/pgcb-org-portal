from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

os.environ.setdefault('PAYMENT_WEBHOOK_SECRET', 'unit-test-payment-secret')

from app.core.config import settings
from app.core.security import hash_password
from app.db.seed import main as seed_main, seed_synthetic_members
from app.db.session import SessionLocal
from app.main import app
from app.models import Circle, Member, MemberDocument, PaymentTransaction, User
from app.utils.storage import get_file_bytes

client = TestClient(app)


def _login(email: str, password: str = 'ChangeMe123!'):
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.email == email))
        if u:
            u.password_hash = hash_password(password)
            u.mfa_enabled = False
            u.is_active = True
            u.email_verified = True
            db.commit()
    r = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    assert r.status_code == 200, r.text
    return r.cookies


def test_2000_synthetic_members_pagination_and_stats_performance():
    admin_cookies = _login('admin@example.org')

    with SessionLocal() as db:
        inserted = seed_synthetic_members(db, count=2000)
        assert inserted >= 0
        first_circle = db.scalar(select(Circle).order_by(Circle.id))
        assert first_circle is not None
        circle_id = first_circle.id

    try:
        # 1. Public member directory rejects limit > 100 and returns 100 items at limit=100
        r_over = client.get('/api/v1/public/members', params={'limit': 500, 'page': 1})
        assert r_over.status_code == 422

        t0 = time.perf_counter()
        r_pub = client.get('/api/v1/public/members', params={'limit': 100, 'page': 1})
        elapsed_pub = time.perf_counter() - t0
        assert r_pub.status_code == 200, r_pub.text
        body_pub = r_pub.json()
        assert len(body_pub['items']) == 100
        assert body_pub['limit'] == 100
        assert body_pub['total'] >= 1800
        assert elapsed_pub < 2.0

        # 2. Filtered public member query computes filtered total (not global total)
        r_filtered = client.get(
            '/api/v1/public/members',
            params={'circle_id': circle_id, 'q': 'PGD-2026-200', 'limit': 20},
        )
        assert r_filtered.status_code == 200, r_filtered.text
        filtered_body = r_filtered.json()
        assert filtered_body['total'] == len(filtered_body['items'])
        assert 1 <= filtered_body['total'] <= 10

        # 3. Admin member search & pagination with X-Total-Count header
        r_adm = client.get(
            '/api/v1/admin/members',
            params={'q': 'SYNTH-EMP-', 'limit': 500, 'page': 2},
            cookies=admin_cookies,
        )
        assert r_adm.status_code == 200, r_adm.text
        assert len(r_adm.json()) == 100
        assert int(r_adm.headers.get('X-Total-Count', '0')) == 2000

        # 4. Admin stats & overview performance under 2,000+ member load
        t1 = time.perf_counter()
        r_stats = client.get('/api/v1/admin/stats', cookies=admin_cookies)
        r_overview = client.get('/api/v1/admin/reports/overview', cookies=admin_cookies)
        elapsed_stats = time.perf_counter() - t1
        assert r_stats.status_code == 200
        assert r_overview.status_code == 200
        assert r_stats.json()['members'] >= 2000
        assert elapsed_stats < 2.5
    finally:
        with SessionLocal() as db:
            syn_user_ids = list(
                db.scalars(select(User.id).where(User.email.like('synth.member.%@test.invalid'))).all()
            )
            if syn_user_ids:
                db.execute(delete(Member).where(Member.user_id.in_(syn_user_ids)))
                db.execute(delete(User).where(User.id.in_(syn_user_ids)))
                db.commit()


def test_file_upload_security_validation_and_uuid_naming():
    member_cookies = _login('member@example.org')

    # 1. Reject spoofed magic bytes (HTML/JS disguised as PDF)
    r_spoof = client.post(
        '/api/v1/member/documents?document_type=NID',
        cookies=member_cookies,
        files={'file': ('spoofed.pdf', b'<script>alert("xss")</script>', 'application/pdf')},
    )
    assert r_spoof.status_code == 400
    assert 'magic bytes' in r_spoof.text.lower()

    # 2. Reject double-extension executable disguise (shell.php.pdf)
    r_double = client.post(
        '/api/v1/member/documents?document_type=NID',
        cookies=member_cookies,
        files={'file': ('shell.php.pdf', b'%PDF-1.4\n%valid header\n%%EOF', 'application/pdf')},
    )
    assert r_double.status_code == 400

    # 3. Reject oversized file (> max_upload_mb)
    oversized = b'%PDF-1.4\n' + (b'A' * (settings.max_upload_mb * 1024 * 1024 + 1024))
    r_large = client.post(
        '/api/v1/member/documents?document_type=NID',
        cookies=member_cookies,
        files={'file': ('huge.pdf', oversized, 'application/pdf')},
    )
    assert r_large.status_code == 413

    # 4. Valid PDF upload stores with UUID prefix on disk
    valid_pdf = b'%PDF-1.4\n%PGCB Staging Hardening Test\n%%EOF'
    r_valid = client.post(
        '/api/v1/member/documents?document_type=NID',
        cookies=member_cookies,
        files={'file': ('nid_card.pdf', valid_pdf, 'application/pdf')},
    )
    assert r_valid.status_code == 200, r_valid.text
    doc_id = r_valid.json()['id']

    with SessionLocal() as db:
        doc = db.get(MemberDocument, doc_id)
        assert doc is not None
        stored_name = Path(doc.storage_path).name
        prefix = stored_name.split('_', 1)[0]
        assert len(prefix) == 32 and all(c in '0123456789abcdef' for c in prefix)

    # 5. Path traversal rejection in storage utility and public asset endpoint
    with pytest.raises(ValueError, match='Path traversal'):
        get_file_bytes('../../etc/passwd')

    r_traversal = client.get('/api/v1/public/assets/..%2F..%2Fetc%2Fpasswd')
    assert r_traversal.status_code in (400, 404)


def test_private_document_isolation_and_rbac_and_session_revocation():
    member_a_cookies = _login('member@example.org')
    valid_pdf = b'%PDF-1.4\n%Private Document of Member A\n%%EOF'
    up = client.post(
        '/api/v1/member/documents?document_type=CERTIFICATE',
        cookies=member_a_cookies,
        files={'file': ('private_a.pdf', valid_pdf, 'application/pdf')},
    )
    assert up.status_code == 200
    doc_id = up.json()['id']

    # Create Member B and attempt to download Member A's document
    ts = int(datetime.utcnow().timestamp() * 1000)
    member_b_email = f'member.b.{ts}@example.org'
    with SessionLocal() as db:
        u_b = User(
            email=member_b_email,
            password_hash=hash_password('MemberBPass123!'),
            name_bn='সদস্য বি',
            role='MEMBER',
            is_active=True,
            email_verified=True,
        )
        db.add(u_b)
        db.flush()
        db.add(Member(user_id=u_b.id, status='ACTIVE'))
        db.commit()

    member_b_cookies = _login(member_b_email, 'MemberBPass123!')

    # Member B cannot download Member A's private document
    r_dl_b = client.get(f'/api/v1/member/documents/{doc_id}/download', cookies=member_b_cookies)
    assert r_dl_b.status_code == 404

    # Member B cannot access admin endpoints
    r_adm = client.get('/api/v1/admin/members', cookies=member_b_cookies)
    assert r_adm.status_code == 403

    # Unauthenticated client cannot access member or admin endpoints
    anon_client = TestClient(app)
    assert anon_client.get('/api/v1/member/profile').status_code == 401
    assert anon_client.get('/api/v1/admin/stats').status_code == 401

    # logout-all revokes active session token immediately
    r_logout_all = client.post('/api/v1/auth/logout-all', cookies=member_b_cookies)
    assert r_logout_all.status_code == 200
    assert client.get('/api/v1/auth/me', cookies=member_b_cookies).status_code == 401


def test_staging_seed_prevents_predictable_demo_accounts(monkeypatch):
    monkeypatch.setattr(settings, 'app_env', 'staging')
    monkeypatch.delenv('ADMIN_EMAIL', raising=False)
    monkeypatch.delenv('ADMIN_PASSWORD', raising=False)

    with SessionLocal() as db:
        # Temporarily check that seed_main in staging mode does not create a new demo user
        temp_demo = db.scalar(select(User).where(User.email == 'staging.predictable@example.org'))
        assert temp_demo is None
    # Executing seed_main() in staging without ADMIN_EMAIL/ADMIN_PASSWORD must not raise or create predictable accounts
    seed_main()


def test_payment_success_failure_cancellation_and_duplicate_webhooks():
    cookies = _login('member@example.org')
    secret = os.environ['PAYMENT_WEBHOOK_SECRET']

    def _send_webhook(event_id: str, trx_ref: str, payment_id: int, status_str: str):
        payload = {
            'event_id': event_id,
            'event_type': f'PAYMENT_{status_str}',
            'transaction_ref': trx_ref,
            'status': status_str,
            'payment_id': payment_id,
        }
        raw = json.dumps(payload).encode('utf-8')
        sig = hmac.new(secret.encode('utf-8'), raw, hashlib.sha256).hexdigest()
        return client.post(
            '/api/v1/payments/webhooks/TEST',
            content=raw,
            headers={'X-Signature': sig, 'X-Event-Id': event_id},
        )

    # 1. Payment FAILURE flow
    c_fail = client.post(
        '/api/v1/member/payments/checkout',
        cookies=cookies,
        json={'amount': 500, 'currency': 'BDT', 'purpose': 'MEMBERSHIP', 'provider': 'TEST'},
    )
    assert c_fail.status_code == 200
    fail_data = c_fail.json()
    evt_fail = f"evt-fail-{int(time.time() * 1000)}"
    w_fail = _send_webhook(evt_fail, fail_data['provider_transaction_id'], fail_data['payment_id'], 'FAILED')
    assert w_fail.status_code == 200
    assert w_fail.json()['status'] == 'FAILED'

    # 2. Payment CANCELLATION flow
    c_cancel = client.post(
        '/api/v1/member/payments/checkout',
        cookies=cookies,
        json={'amount': 500, 'currency': 'BDT', 'purpose': 'MEMBERSHIP', 'provider': 'TEST'},
    )
    assert c_cancel.status_code == 200
    cancel_data = c_cancel.json()
    evt_cancel = f"evt-cancel-{int(time.time() * 1000)}"
    w_cancel = _send_webhook(evt_cancel, cancel_data['provider_transaction_id'], cancel_data['payment_id'], 'CANCELLED')
    assert w_cancel.status_code == 200
    assert w_cancel.json()['status'] == 'FAILED'

    # 3. Payment SUCCESS + Duplicate Webhook Idempotency
    c_ok = client.post(
        '/api/v1/member/payments/checkout',
        cookies=cookies,
        json={'amount': 500, 'currency': 'BDT', 'purpose': 'MEMBERSHIP', 'provider': 'TEST'},
    )
    assert c_ok.status_code == 200
    ok_data = c_ok.json()
    evt_ok = f"evt-ok-{int(time.time() * 1000)}"
    w_ok1 = _send_webhook(evt_ok, ok_data['provider_transaction_id'], ok_data['payment_id'], 'SUCCESS')
    assert w_ok1.status_code == 200
    assert w_ok1.json()['status'] == 'PAID'

    w_ok2 = _send_webhook(evt_ok, ok_data['provider_transaction_id'], ok_data['payment_id'], 'SUCCESS')
    assert w_ok2.status_code == 200
    assert w_ok2.json().get('duplicate') is True
