import time
from datetime import datetime

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models import AuditLog, Event, EventRegistration, Member, PaymentTransaction, User
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

    # Refunding through generic update is blocked to prevent refund workflow bypass (HTTP 400)
    r = client.patch(f'/api/v1/admin/payments/{payment_id}', cookies=cookies, json={'status': 'REFUNDED'})
    assert r.status_code == 400
    assert "Refunds cannot be processed via generic status update" in r.text


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

    r = client.patch(f'/api/v1/admin/payments/{payment_id}', cookies=cookies, json={'status': 'PAID', 'transaction_ref': 'EVT-MANUAL-REF-1'})
    assert r.status_code == 200, r.text

    db = SessionLocal()
    try:
        reg_item = db.get(EventRegistration, reg_id)
        assert reg_item.payment_status == 'PAID'
        assert reg_item.registration_status == 'CONFIRMED'
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


def test_admin_payment_status_invalid_terminal_transitions():
    """1. Enforce payment state transitions: reject invalid transitions from PAID to FAILED/CANCELLED."""
    reset_demo_accounts()
    cookies = login()
    db = SessionLocal()
    try:
        payment = PaymentTransaction(
            user_id=None,
            member_id=None,
            purpose='EVENT',
            amount=500,
            currency='BDT',
            provider='MANUAL',
            status='PAID',
            transaction_ref='TRX-INITIAL-PAID-01',
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        payment_id = payment.id
    finally:
        db.close()

    # Attempt transition from PAID to FAILED
    r_fail = client.patch(
        f'/api/v1/admin/payments/{payment_id}',
        cookies=cookies,
        json={'status': 'FAILED'},
    )
    assert r_fail.status_code == 409, r_fail.text
    assert "Illegal payment state transition: PAID -> FAILED" in r_fail.text

    # Attempt transition from PAID to CANCELLED
    r_cancel = client.patch(
        f'/api/v1/admin/payments/{payment_id}',
        cookies=cookies,
        json={'status': 'CANCELLED'},
    )
    assert r_cancel.status_code == 409, r_cancel.text
    assert "Illegal payment state transition: PAID -> CANCELLED" in r_cancel.text

    # Verify status unchanged in database
    db = SessionLocal()
    try:
        persisted = db.get(PaymentTransaction, payment_id)
        assert persisted.status == 'PAID'
    finally:
        db.close()


def test_admin_payment_status_refund_bypass_rejected():
    """2. Prevent refund-workflow bypass: reject REFUNDED and direct to dedicated endpoint."""
    reset_demo_accounts()
    cookies = login()
    db = SessionLocal()
    try:
        payment = PaymentTransaction(
            user_id=None,
            member_id=None,
            purpose='EVENT',
            amount=350,
            currency='BDT',
            provider='MANUAL',
            status='PAID',
            transaction_ref='TRX-REFUND-ATTEMPT-01',
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        payment_id = payment.id
    finally:
        db.close()

    # Generic patch endpoint rejects REFUNDED
    r = client.patch(
        f'/api/v1/admin/payments/{payment_id}',
        cookies=cookies,
        json={'status': 'REFUNDED'},
    )
    assert r.status_code == 400, r.text
    assert "Refunds cannot be processed via generic status update" in r.text
    assert "/refund" in r.text

    # Database record preserved
    db = SessionLocal()
    try:
        persisted = db.get(PaymentTransaction, payment_id)
        assert persisted.status == 'PAID'
    finally:
        db.close()


def test_admin_payment_status_missing_reconciliation_evidence_rejected():
    """3. Protect manual payment reconciliation: reject PAID without transaction reference/evidence."""
    reset_demo_accounts()
    cookies = login()
    db = SessionLocal()
    try:
        payment = PaymentTransaction(
            user_id=None,
            member_id=None,
            purpose='EVENT',
            amount=600,
            currency='BDT',
            provider='MANUAL',
            status='PENDING',
            transaction_ref=None,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        payment_id = payment.id
    finally:
        db.close()

    # No reference supplied
    r_none = client.patch(
        f'/api/v1/admin/payments/{payment_id}',
        cookies=cookies,
        json={'status': 'PAID'},
    )
    assert r_none.status_code == 400, r_none.text
    assert "adequate transaction-reference or reconciliation evidence" in r_none.text

    # Whitespace reference supplied
    r_ws = client.patch(
        f'/api/v1/admin/payments/{payment_id}',
        cookies=cookies,
        json={'status': 'PAID', 'transaction_ref': '    '},
    )
    assert r_ws.status_code == 400, r_ws.text
    assert "adequate transaction-reference or reconciliation evidence" in r_ws.text

    # Database status remains PENDING
    db = SessionLocal()
    try:
        persisted = db.get(PaymentTransaction, payment_id)
        assert persisted.status == 'PENDING'
    finally:
        db.close()


def test_admin_payment_status_valid_permitted_updates():
    """4. Valid permitted transitions: PENDING -> FAILED and PENDING -> PAID with evidence."""
    reset_demo_accounts()
    cookies = login()
    db = SessionLocal()
    try:
        # A: PENDING -> FAILED
        p_fail = PaymentTransaction(
            user_id=None,
            member_id=None,
            purpose='EVENT',
            amount=200,
            currency='BDT',
            provider='MANUAL',
            status='PENDING',
        )
        # B: PENDING -> PAID
        p_paid = PaymentTransaction(
            user_id=None,
            member_id=None,
            purpose='EVENT',
            amount=450,
            currency='BDT',
            provider='MANUAL',
            status='PENDING',
        )
        db.add_all([p_fail, p_paid])
        db.commit()
        db.refresh(p_fail)
        db.refresh(p_paid)
        fail_id, paid_id = p_fail.id, p_paid.id
    finally:
        db.close()

    # Valid PENDING -> FAILED
    r_fail = client.patch(
        f'/api/v1/admin/payments/{fail_id}',
        cookies=cookies,
        json={'status': 'FAILED'},
    )
    assert r_fail.status_code == 200, r_fail.text
    assert r_fail.json()['status'] == 'FAILED'

    # Valid PENDING -> PAID with reconciliation reference
    r_paid = client.patch(
        f'/api/v1/admin/payments/{paid_id}',
        cookies=cookies,
        json={'status': 'PAID', 'transaction_ref': 'BANK-CHALLAN-VALID-01'},
    )
    assert r_paid.status_code == 200, r_paid.text
    assert r_paid.json()['status'] == 'PAID'
    assert r_paid.json()['receipt_no'] is not None

    db = SessionLocal()
    try:
        p_fail_db = db.get(PaymentTransaction, fail_id)
        assert p_fail_db.status == 'FAILED'

        p_paid_db = db.get(PaymentTransaction, paid_id)
        assert p_paid_db.status == 'PAID'
        assert p_paid_db.transaction_ref == 'BANK-CHALLAN-VALID-01'
        assert p_paid_db.provider_payload is not None
        assert p_paid_db.provider_payload.get('reconciled_by') is not None
        assert p_paid_db.provider_payload.get('reconciled_at') is not None
    finally:
        db.close()


def test_admin_payment_status_rollback_and_related_record_consistency():
    """5. Transaction rollback and related-record consistency: rejected update does not alter records."""
    reset_demo_accounts()
    cookies = login()
    db = SessionLocal()
    try:
        event = db.query(Event).order_by(Event.id).first()
        if not event:
            event = Event(title_bn='Consistency event', event_date=datetime.utcnow())
            db.add(event)
            db.commit()
            db.refresh(event)

        reg = EventRegistration(
            event_id=event.id,
            name='Rollback Attendee',
            email='rollback@example.org',
            ticket_code=f'TKT-RB-{int(datetime.utcnow().timestamp())}',
            registration_status='CONFIRMED',
            attendance_status='NOT_CHECKED_IN',
            payment_status='PAID',
        )
        db.add(reg)
        db.commit()
        db.refresh(reg)

        payment = PaymentTransaction(
            event_registration_id=reg.id,
            purpose='EVENT',
            amount=800,
            currency='BDT',
            provider='MANUAL',
            status='PAID',
            transaction_ref='TRX-CONFIRMED-800',
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        reg_id, p_id = reg.id, payment.id
    finally:
        db.close()

    # Attempt illegal transition PAID -> FAILED
    r = client.patch(
        f'/api/v1/admin/payments/{p_id}',
        cookies=cookies,
        json={'status': 'FAILED'},
    )
    assert r.status_code == 409

    # Verify atomic rollback: both payment and registration remain unchanged
    db = SessionLocal()
    try:
        persisted_p = db.get(PaymentTransaction, p_id)
        assert persisted_p.status == 'PAID'

        persisted_reg = db.get(EventRegistration, reg_id)
        assert persisted_reg.payment_status == 'PAID'
        assert persisted_reg.registration_status == 'CONFIRMED'
    finally:
        db.close()


def test_admin_payment_status_authorization_and_audit():
    """6. Authorization and audit behavior: enforce RBAC permissions and record AuditLog."""
    reset_demo_accounts()
    db = SessionLocal()
    try:
        payment = PaymentTransaction(
            user_id=None,
            member_id=None,
            purpose='EVENT',
            amount=300,
            currency='BDT',
            provider='MANUAL',
            status='PENDING',
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        payment_id = payment.id
    finally:
        db.close()

    # Unauthenticated request -> 401
    unauth_client = TestClient(app)
    r_unauth = unauth_client.patch(
        f'/api/v1/admin/payments/{payment_id}',
        json={'status': 'FAILED'},
    )
    assert r_unauth.status_code == 401

    # Member user without finance.write -> 403
    member_client = TestClient(app)
    r_mem_login = member_client.post('/api/v1/auth/login', json={'email': 'member@example.org', 'password': 'ChangeMe123!'})
    assert r_mem_login.status_code == 200
    r_member = member_client.patch(
        f'/api/v1/admin/payments/{payment_id}',
        json={'status': 'FAILED'},
    )
    assert r_member.status_code == 403

    # Authorized admin request -> 200 & AuditLog entry
    admin_client = TestClient(app)
    r_adm_login = admin_client.post('/api/v1/auth/login', json={'email': 'admin@example.org', 'password': 'ChangeMe123!'})
    assert r_adm_login.status_code == 200
    r_admin = admin_client.patch(
        f'/api/v1/admin/payments/{payment_id}',
        json={'status': 'FAILED'},
    )
    assert r_admin.status_code == 200

    db = SessionLocal()
    try:
        audit_entry = db.query(AuditLog).filter(
            AuditLog.entity == 'PAYMENT',
            AuditLog.entity_id == str(payment_id),
            AuditLog.action == 'UPDATE_PAYMENT',
        ).first()
        assert audit_entry is not None
        assert audit_entry.user_id is not None
    finally:
        db.close()
