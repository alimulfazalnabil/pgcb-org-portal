from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models import Circular, ContentWorkflow, User
from app.core.security import hash_password

client = TestClient(app)


def _login(email='admin@example.org', password='ChangeMe123!'):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.password_hash = hash_password(password)
            user.mfa_enabled = False
            db.commit()
    finally:
        db.close()
    r = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    assert r.status_code == 200, r.text
    return r.cookies


def test_admin_overview_report_has_operational_series():
    cookies = _login()
    r = client.get('/api/v1/admin/reports/overview', cookies=cookies)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['members']['total'] >= 1
    assert len(body['members']['series']) == 6
    assert len(body['events']['series']) == 6
    assert 'content' in body and 'messages' in body and 'system' in body


def test_workflow_rejects_invalid_reverse_transition():
    cookies = _login()
    r = client.post('/api/v1/admin/circulars', cookies=cookies, json={'title_bn': 'v0.9 transition test', 'category': 'GENERAL'})
    assert r.status_code == 200, r.text
    cid = r.json()['id']

    r = client.post(f'/api/v1/admin/workflows/CIRCULAR/{cid}/transition', cookies=cookies, json={'status': 'PUBLISHED'})
    assert r.status_code == 200, r.text
    r = client.post(f'/api/v1/admin/workflows/CIRCULAR/{cid}/transition', cookies=cookies, json={'status': 'IN_REVIEW'})
    assert r.status_code == 409, r.text


def test_schedule_requires_future_timestamp_and_draft_can_be_scheduled_after_approval():
    cookies = _login()
    r = client.post('/api/v1/admin/circulars', cookies=cookies, json={'title_bn': 'v0.9 schedule test', 'category': 'GENERAL'})
    assert r.status_code == 200, r.text
    cid = r.json()['id']
    r = client.post(f'/api/v1/admin/workflows/CIRCULAR/{cid}/transition', cookies=cookies, json={'status': 'SCHEDULED', 'scheduled_at': datetime.utcnow().isoformat()})
    assert r.status_code == 409, r.text
    r = client.post(f'/api/v1/admin/workflows/CIRCULAR/{cid}/transition', cookies=cookies, json={'status': 'IN_REVIEW'})
    assert r.status_code == 200, r.text
    r = client.post(f'/api/v1/admin/workflows/CIRCULAR/{cid}/transition', cookies=cookies, json={'status': 'APPROVED'})
    assert r.status_code == 200, r.text
    future = (datetime.utcnow().replace(microsecond=0)).isoformat()
    from datetime import timedelta
    future = (datetime.utcnow() + timedelta(days=1)).isoformat()
    r = client.post(f'/api/v1/admin/workflows/CIRCULAR/{cid}/transition', cookies=cookies, json={'status': 'SCHEDULED', 'scheduled_at': future})
    assert r.status_code == 200, r.text


def test_ticket_checkin_blocks_cancelled_and_unpaid_registrations():
    cookies = _login()
    event = client.post('/api/v1/admin/events', cookies=cookies, json={'title_bn': 'v0.9 Checkin Event', 'event_date': datetime.utcnow().isoformat(), 'registration_enabled': True, 'is_published': True, 'fee_amount': 250})
    assert event.status_code == 200
    event_id = event.json()['id']
    reg = client.post(f'/api/v1/events/{event_id}/registrations', json={'name': 'Unpaid Guest', 'email': 'unpaid-v09@example.org'})
    assert reg.status_code == 200
    reg_data = reg.json()
    r = client.post('/api/v1/admin/event-registrations/check-in-by-ticket', cookies=cookies, json={'ticket_code': reg_data['ticket_code']})
    assert r.status_code == 409

    free_event = client.post('/api/v1/admin/events', cookies=cookies, json={'title_bn': 'v0.9 Free Checkin Event', 'event_date': datetime.utcnow().isoformat(), 'registration_enabled': True, 'is_published': True})
    assert free_event.status_code == 200
    reg2 = client.post(f"/api/v1/events/{free_event.json()['id']}/registrations", json={'name': 'Cancelled Guest', 'email': 'cancelled-v09@example.org'})
    assert reg2.status_code == 200
    reg_id = reg2.json()['id']
    r = client.patch(f'/api/v1/admin/event-registrations/{reg_id}', cookies=cookies, json={'status': 'CANCELLED'})
    assert r.status_code == 200
    r = client.post('/api/v1/admin/event-registrations/check-in-by-ticket', cookies=cookies, json={'ticket_code': reg2.json()['ticket_code']})
    assert r.status_code == 409
