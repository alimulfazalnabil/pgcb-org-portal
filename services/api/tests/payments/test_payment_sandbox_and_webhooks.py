from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.db.session import SessionLocal
from app.models import User

client = TestClient(app)


def test_sandbox_payment_and_idempotent_webhook_simulation():
    ts = int(datetime.utcnow().timestamp() * 1000)
    email = f'pay_sandbox_{ts}@pgcb.gov.bd'
    password = 'SandboxPayPass123!'
    reg = client.post(
        '/api/v1/auth/register',
        json={
            'name_bn': 'স্যান্ডবক্স পেমেন্ট সদস্য',
            'name_en': 'Sandbox Payment Member',
            'email': email,
            'phone': f'018{ts % 100000000:08d}',
            'password': password,
            'designation_bn': 'সহকারী প্রকৌশলী',
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

    # 1. Server-authoritative payment creation
    pay = client.post(
        '/api/v1/member/payments',
        headers=headers,
        json={
            'purpose': 'MEMBERSHIP',
            'membership_plan_id': 'ANNUAL_STANDARD',
            'provider': 'BKASH',
        },
    )
    assert pay.status_code == 200
    payment_id = pay.json()['id']
    assert pay.json()['amount'] == 1000
    assert pay.json()['status'] == 'PENDING'

    # 2. Sandbox webhook simulation -> PAID + Receipt + Membership Activation
    sim = client.post(
        '/api/v1/payments/sandbox/simulate',
        headers=headers,
        json={'payment_id': payment_id},
    )
    assert sim.status_code == 200
    sim_data = sim.json()
    assert sim_data['status'] == 'success'
    assert sim_data['payment_status'] == 'PAID'
    assert sim_data['receipt_no'].startswith('PGCB-RCP-')

    # 3. Replay protection
    replay = client.post(
        '/api/v1/payments/sandbox/simulate',
        headers=headers,
        json={'payment_id': payment_id},
    )
    assert replay.status_code == 200
    assert replay.json()['idempotent_replay'] is True
