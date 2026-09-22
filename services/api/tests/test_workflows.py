import os
os.environ['DATABASE_URL'] = 'sqlite:///./test_workflows.db'
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base, engine, SessionLocal
from app.db.seed import main as seed_main

Base.metadata.create_all(bind=engine)
client = TestClient(app)

def test_public_content_and_verification():
    r=client.get('/api/v1/public/verify/PGD-2026-1001'); assert r.status_code==200; assert r.json()['verified'] is True
    assert client.get('/api/v1/public/circulars').status_code == 200
    assert len(client.get('/api/v1/public/circles').json()) == 9
    assert client.get('/api/v1/public/committee').status_code == 200
    assert client.get('/api/v1/public/journals').status_code == 200
    assert client.get('/api/v1/public/events').status_code == 200

def test_login_and_admin_member_list():
    r=client.post('/api/v1/auth/login',json={'email':'admin@example.org','password':'ChangeMe123!'}); assert r.status_code==200
    cookies=r.cookies
    r=client.get('/api/v1/admin/members',cookies=cookies); assert r.status_code==200; assert any(m.get('membership_id') == 'PGD-2026-1001' for m in r.json())
