from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models import User

client = TestClient(app)

def test_email_verification_and_resend():
    email = f"v06-{datetime.utcnow().timestamp()}@example.org"
    r = client.post('/api/v1/auth/register', json={'email': email, 'password': 'ChangeMe123!', 'name_bn': 'v06 পরীক্ষার্থী'})
    assert r.status_code == 200, r.text
    token = r.json().get('verification_token')
    assert token
    r = client.post('/api/v1/auth/verify-email', json={'token': token})
    assert r.status_code == 200
    db=SessionLocal()
    try:
        u=db.query(User).filter(User.email==email).first()
        assert u and u.email_verified is True
    finally: db.close()
    r = client.post('/api/v1/auth/resend-verification', json={'email': email})
    assert r.status_code == 200
    db=SessionLocal()
    try:
        u=db.query(User).filter(User.email==email).first()
        if u: db.delete(u); db.commit()
    finally: db.close()


def test_admin_exports_are_csv():
    login = client.post('/api/v1/auth/login', json={'email':'admin@example.org','password':'ChangeMe123!'})
    assert login.status_code == 200
    cookies = login.cookies
    for path in ['/api/v1/admin/exports/members.csv','/api/v1/admin/exports/event-registrations.csv','/api/v1/admin/exports/payments.csv']:
        r=client.get(path,cookies=cookies)
        assert r.status_code == 200
        assert r.headers['content-type'].startswith('text/csv')
        assert 'Content-Disposition' in r.headers
