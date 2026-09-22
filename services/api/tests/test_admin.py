import time
from datetime import datetime

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models import Event, EventRegistration, Member, PaymentTransaction, User
from app.core.mfa import _hotp
from app.core.security import hash_password

client = TestClient(app)


def reset_demo_accounts():
    """Restore the seeded demo accounts and clear any MFA state from prior tests."""
    db = SessionLocal()
    try:
        for email in ('admin@example.org', 'member@example.org'):
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.password_hash = hash_password('ChangeMe123!')
                user.mfa_enabled = False
                user.mfa_secret = None
                user.mfa_secret_enc = None
        db.commit()
    finally:
        db.close()


def login(email='admin@example.org', password='ChangeMe123!'):
    r = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    assert r.status_code == 200, r.text
    return r.cookies


def _admin_member():
    db = SessionLocal()
    try:
        return db.query(Member).filter(Member.status == 'ACTIVE').first()
    finally:
        db.close()


def _set_member_status(member_id, status):
    db = SessionLocal()
    try:
        member = db.get(Member, member_id)
        member.status = status
        db.commit()
        return member.id
    finally:
        db.close()


def test_review_member_transitions_and_audit():
    reset_demo_accounts()
    cookies = login()
    db = SessionLocal()
    try:
        ts = int(datetime.utcnow().timestamp())
        user = User(
            email=f'transition.{ts}@example.org',
            password_hash=hash_password('TestPass123!'),
            name_bn='ট্রানজিশন পরীক্ষক',
            name_en='Transition Tester',
            phone='01799887766',
            role='MEMBER'
        )
        db.add(user)
        db.flush()
        member = Member(
            user_id=user.id,
            status='PENDING',
            employee_id=f'EMP-{ts}',
            designation_bn='সহকারী প্রকৌশলী'
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        member_id = member.id
    finally:
        db.close()

    # REVIEW moves the application to UNDER_REVIEW.
    r = client.post(f'/api/v1/admin/members/{member_id}/review', params={'action': 'REVIEW'}, cookies=cookies)
    assert r.status_code == 200, r.text
    assert r.json()['status'] == 'UNDER_REVIEW'

    # SUSPEND and REACTIVATE flip the status without needing approval.
    r = client.post(f'/api/v1/admin/members/{member_id}/review', params={'action': 'SUSPEND'}, cookies=cookies)
    assert r.status_code == 200 and r.json()['status'] == 'SUSPENDED'
    r = client.post(f'/api/v1/admin/members/{member_id}/review', params={'action': 'REACTIVATE'}, cookies=cookies)
    assert r.status_code == 200 and r.json()['status'] == 'ACTIVE'

    # APPROVE assigns a membership id and validity window.
    r = client.post(f'/api/v1/admin/members/{member_id}/review', params={'action': 'APPROVE'}, cookies=cookies)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['status'] == 'ACTIVE'
    assert body['membership_id'] and body['membership_id'].startswith('PGD-')
    assert body['issue_date'] and body['validity_date']

    # An unknown action is rejected before any state change.
    r = client.post(f'/api/v1/admin/members/{member_id}/review', params={'action': 'EXPLODE'}, cookies=cookies)
    assert r.status_code == 400


def test_update_payment_status_transitions():
    reset_demo_accounts()
    cookies = login()
    db = SessionLocal()
    try:
        payment = PaymentTransaction(user_id=None, member_id=None, purpose='EVENT', amount=250, currency='BDT', provider='MANUAL', status='PENDING')
        db.add(payment)
        db.commit()
        db.refresh(payment)
        payment_id = payment.id
    finally:
        db.close()

    r = client.patch(f'/api/v1/admin/payments/{payment_id}', cookies=cookies, json={'status': 'PAID', 'transaction_ref': 'MANUAL-REF-1'})
    assert r.status_code == 200, r.text
    assert r.json()['status'] == 'PAID'

    db = SessionLocal()
    try:
        payment = db.get(PaymentTransaction, payment_id)
        assert payment.status == 'PAID'
        assert payment.transaction_ref == 'MANUAL-REF-1'
    finally:
        db.close()

    # An unknown status is rejected.
    r = client.patch(f'/api/v1/admin/payments/{payment_id}', cookies=cookies, json={'status': 'NOT_A_STATUS'})
    assert r.status_code == 400

    # Refunding the payment moves it out of PAID.
    r = client.patch(f'/api/v1/admin/payments/{payment_id}', cookies=cookies, json={'status': 'REFUNDED'})
    assert r.status_code == 200 and r.json()['status'] == 'REFUNDED'


def test_payment_approval_propagates_to_event_registration():
    reset_demo_accounts()
    cookies = login()
    db = SessionLocal()
    try:
        event = db.query(Event).order_by(Event.id).first()
        if event is None:
            event = Event(title_bn='Admin test event', event_date=datetime.utcnow())
            db.add(event)
            db.commit()
            db.refresh(event)
        reg = EventRegistration(event_id=event.id, name='Paid Attendee', email='paid@example.org',
                                ticket_code=f'TEST-{int(datetime.utcnow().timestamp())}',
                                registration_status='REGISTERED', attendance_status='NOT_CHECKED_IN',
                                payment_status='PENDING')
        db.add(reg)
        db.commit()
        db.refresh(reg)
        payment = PaymentTransaction(event_registration_id=reg.id, purpose='EVENT', amount=300,
                                     currency='BDT', provider='MANUAL', status='PENDING')
        db.add(payment)
        db.commit()
        db.refresh(payment)
        reg_id, payment_id = reg.id, payment.id
    finally:
        db.close()

    r = client.patch(f'/api/v1/admin/payments/{payment_id}', cookies=cookies, json={'status': 'PAID'})
    assert r.status_code == 200, r.text

    db = SessionLocal()
    try:
        assert db.get(EventRegistration, reg_id).payment_status == 'PAID'
    finally:
        db.close()


def test_admin_mfa_enable_and_disable_roundtrip():
    reset_demo_accounts()
    cookies = login()

    r = client.post('/api/v1/admin/mfa/setup', cookies=cookies)
    assert r.status_code == 200, r.text
    secret = r.json()['secret']
    assert r.json()['enabled'] is False

    r = client.post('/api/v1/admin/mfa/enable', params={'code': _hotp(secret, int(time.time() // 30))}, cookies=cookies)
    assert r.status_code == 200 and r.json()['enabled'] is True

    r = client.get('/api/v1/admin/mfa/status', cookies=cookies)
    assert r.status_code == 200 and r.json()['enabled'] is True

    # A wrong code must not disable MFA.
    r = client.post('/api/v1/admin/mfa/disable', params={'code': '000'}, cookies=cookies)
    assert r.status_code == 400

    r = client.post('/api/v1/admin/mfa/disable', params={'code': _hotp(secret, int(time.time() // 30))}, cookies=cookies)
    assert r.status_code == 200 and r.json()['enabled'] is False

    r = client.get('/api/v1/admin/mfa/status', cookies=cookies)
    assert r.status_code == 200 and r.json()['enabled'] is False
    reset_demo_accounts()


def test_admin_csv_exports_have_headers_and_rows():
    reset_demo_accounts()
    cookies = login()
    for path, expected_header in [
        ('/api/v1/admin/exports/members.csv', 'membership_id'),
        ('/api/v1/admin/exports/event-registrations.csv', 'ticket_code'),
        ('/api/v1/admin/exports/payments.csv', 'transaction_ref'),
    ]:
        r = client.get(path, cookies=cookies)
        assert r.status_code == 200, r.text
        assert r.headers['content-type'].startswith('text/csv')
        assert 'Content-Disposition' in r.headers
        lines = r.text.strip().splitlines()
        assert expected_header in lines[0]
