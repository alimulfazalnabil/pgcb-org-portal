import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta

os.environ['PAYMENT_WEBHOOK_SECRET'] = 'unit-test-payment-secret'

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base, engine, SessionLocal
from app.db.seed import main as seed_main
from app.models import Event, EventRegistration, Member, MembershipRenewal, PaymentTransaction, User
from app.core.security import hash_password

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
seed_main()
client = TestClient(app)

def reset_demo_accounts():
    db = SessionLocal()
    try:
        for email, password in [('admin@example.org', 'ChangeMe123!'), ('member@example.org', 'ChangeMe123!')]:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.password_hash = hash_password(password)
                user.mfa_enabled = False
                user.mfa_secret = None
                user.mfa_secret_enc = None
        db.commit()
    finally:
        db.close()


def login(email='member@example.org', password='ChangeMe123!'):
    r = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    assert r.status_code == 200, r.text
    return r.cookies


def test_checkout_and_signed_webhook_renew_membership():
    reset_demo_accounts()
    cookies = login()
    checkout = client.post('/api/v1/member/payments/checkout', cookies=cookies, json={'amount': 500, 'currency': 'BDT', 'purpose': 'MEMBERSHIP', 'provider': 'TEST'})
    assert checkout.status_code == 200, checkout.text
    data = checkout.json()
    ref = data['provider_transaction_id']
    payload = {'event_id': 'evt-v07-1', 'event_type': 'PAYMENT_SUCCESS', 'transaction_ref': ref, 'status': 'SUCCESS', 'payment_id': data['payment_id']}
    raw = json.dumps(payload).encode()
    signature = hmac.new(os.environ['PAYMENT_WEBHOOK_SECRET'].encode(), raw, hashlib.sha256).hexdigest()
    webhook = client.post('/api/v1/payments/webhooks/TEST', content=raw, headers={'X-Signature': signature, 'X-Event-Id': 'evt-v07-1'})
    assert webhook.status_code == 200, webhook.text
    assert webhook.json()['status'] == 'PAID'
    duplicate = client.post('/api/v1/payments/webhooks/TEST', content=raw, headers={'X-Signature': signature, 'X-Event-Id': 'evt-v07-1'})
    assert duplicate.status_code == 200 and duplicate.json()['duplicate'] is True
    db = SessionLocal()
    try:
        p = db.get(PaymentTransaction, data['payment_id'])
        assert p.status == 'PAID'
        assert db.scalar(__import__('sqlalchemy', fromlist=['select']).select(MembershipRenewal).where(MembershipRenewal.payment_id == p.id)) is not None
        member = db.get(Member, p.member_id)
        assert member.status == 'ACTIVE'
    finally:
        db.close()


def test_workflow_transition_and_certificate_generation():
    reset_demo_accounts()
    cookies = login('admin@example.org')
    # Create a draft event with registration enabled, then register and check-in.
    event = client.post('/api/v1/admin/events', cookies=cookies, json={'title_bn': 'v0.7 Certificate Event', 'event_date': datetime.utcnow().isoformat(), 'registration_enabled': True, 'is_published': True})
    assert event.status_code == 200, event.text
    event_id = event.json()['id']
    reg = client.post(f'/api/v1/events/{event_id}/registrations', json={'name': 'Certificate Participant', 'email': 'certificate@example.org'})
    assert reg.status_code == 200, reg.text
    reg_id = reg.json()['id']
    check = client.post(f'/api/v1/admin/event-registrations/{reg_id}/check-in', cookies=cookies)
    assert check.status_code == 200
    cert = client.post(f'/api/v1/certificates/event-registrations/{reg_id}', cookies=cookies)
    assert cert.status_code == 200, cert.text
    cert_data = cert.json()
    assert cert_data['certificate_no'].startswith('PGCB-CERT-')
    verify = client.get(f"/api/v1/certificates/verify/{cert_data['verification_token']}")
    assert verify.status_code == 200 and verify.json()['verified'] is True

    circular = client.post('/api/v1/admin/circulars', cookies=cookies, json={'title_bn':'Workflow test circular','category':'GENERAL','is_published':False})
    assert circular.status_code == 200
    cid = circular.json()['id']
    workflow = client.post(f'/api/v1/admin/workflows/CIRCULAR/{cid}/transition', cookies=cookies, json={'status':'PUBLISHED'})
    assert workflow.status_code == 200, workflow.text
    assert workflow.json()['is_published'] is True


def test_membership_reminder_worker_marks_expiry_notice():
    reset_demo_accounts()
    db = SessionLocal()
    try:
        member = db.query(Member).filter(Member.membership_id == 'PGD-2026-1001').first()
        member.validity_date = datetime.utcnow() + timedelta(days=30)
        member.status = 'ACTIVE'
        db.commit()
    finally:
        db.close()
    from app.worker import run_once
    result = run_once()
    assert result['membership_events'] >= 1
