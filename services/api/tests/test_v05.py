from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models import Event, User

client = TestClient(app)


def login(email='admin@example.org', password='ChangeMe123!'):
    r = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    assert r.status_code == 200, r.text
    return r.cookies


def test_readiness_and_security_headers():
    r = client.get('/ready')
    assert r.status_code == 200 and r.json()['database'] == 'ok'
    assert r.headers['x-content-type-options'] == 'nosniff'
    assert 'content-security-policy' in {k.lower() for k in r.headers.keys()}


def test_event_registration_ticket_and_qr():
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.is_published.is_(True)).first()
        assert event is not None
        event.registration_enabled = True
        db.commit()
        event_id = event.id
    finally:
        db.close()

    email = f'v05-{datetime.utcnow().timestamp()}@example.org'
    r = client.post(f'/api/v1/events/{event_id}/registrations', json={'name': 'টেস্ট অংশগ্রহণকারী', 'email': email, 'phone': '01700000000', 'organization': 'Test Organization'})
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload['ticket_code']

    r = client.get(f"/api/v1/events/registrations/{payload['ticket_code']}.{__import__('app.routers.event_registration', fromlist=['ticket_signature']).ticket_signature(payload['ticket_code'])}")
    assert r.status_code == 200 and r.json()['valid'] is True
    token = r.json()['ticket_code'] + '.' + __import__('app.routers.event_registration', fromlist=['ticket_signature']).ticket_signature(r.json()['ticket_code'])
    r = client.get(f'/api/v1/events/registrations/{token}/qr')
    assert r.status_code == 200 and r.headers['content-type'].startswith('image/png')


def test_session_revocation_and_payment_ledger():
    cookies = login()
    r = client.get('/api/v1/auth/sessions', cookies=cookies)
    assert r.status_code == 200 and r.json()
    session_id = r.json()[0]['id']
    r = client.post(f'/api/v1/auth/sessions/{session_id}/revoke', cookies=cookies)
    assert r.status_code == 200
    r = client.get('/api/v1/auth/me', cookies=cookies)
    assert r.status_code == 401

    # Member creates payment; finance-capable admin reviews it.
    member_cookies = login('member@example.org', 'NewPassword123!')
    r = client.post('/api/v1/member/payments', cookies=member_cookies, json={'amount': 2500, 'currency': 'BDT', 'purpose': 'MEMBERSHIP', 'provider': 'MANUAL', 'transaction_ref': 'TEST-V05-001'})
    assert r.status_code == 200, r.text
    payment_id = r.json()['id']
    admin_cookies = login()
    r = client.get('/api/v1/admin/payments', cookies=admin_cookies)
    assert r.status_code == 200 and any(p['id'] == payment_id for p in r.json())
    r = client.patch(f'/api/v1/admin/payments/{payment_id}', cookies=admin_cookies, json={'status': 'PAID', 'transaction_ref': 'TEST-V05-001'})
    assert r.status_code == 200 and r.json()['status'] == 'PAID'


def test_notification_broadcast_records_in_app_delivery():
    cookies = login()
    r = client.post('/api/v1/admin/notifications/broadcast', cookies=cookies, json={'title_bn': 'টেস্ট নোটিফিকেশন', 'body_bn': 'v0.5 notification test', 'notification_type': 'SYSTEM', 'role': 'MEMBER', 'channel': 'IN_APP'})
    assert r.status_code == 200, r.text
    assert r.json()['recipients'] >= 1
    r = client.get('/api/v1/admin/notification-deliveries', cookies=cookies)
    assert r.status_code == 200
    assert any(d['channel'] == 'IN_APP' and d['status'] == 'SENT' for d in r.json())
