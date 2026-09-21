import os
os.environ['DATABASE_URL'] = 'sqlite:///./test_v03.db'

from fastapi.testclient import TestClient
from io import BytesIO
from app.main import app
from app.db.session import Base, engine
from app.db.seed import main as seed_main
from app.routers.card import verification_token

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
seed_main()
client = TestClient(app)


def login(email, password='ChangeMe123!'):
    r = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    assert r.status_code == 200
    return r.cookies


def test_signed_verification_and_card_pdf():
    token = verification_token('PGD-2026-1001')
    r = client.get(f'/api/v1/public/verify-token/{token}')
    assert r.status_code == 200
    assert r.json()['verified'] is True

    cookies = login('member@example.org')
    r = client.get('/api/v1/member/card/pdf', cookies=cookies)
    assert r.status_code == 200
    assert r.headers['content-type'].startswith('application/pdf')
    assert r.content[:4] == b'%PDF'


def test_password_reset_flow():
    r = client.post('/api/v1/auth/password-reset/request', json={'email': 'member@example.org'})
    assert r.status_code == 200 and r.json().get('reset_token')
    token = r.json()['reset_token']
    r = client.post('/api/v1/auth/password-reset/confirm', json={'token': token, 'password': 'NewPassword123!'})
    assert r.status_code == 200
    r = client.post('/api/v1/auth/login', json={'email': 'member@example.org', 'password': 'NewPassword123!'})
    assert r.status_code == 200


def test_admin_crud_and_permissions():
    cookies = login('admin@example.org')
    r = client.post('/api/v1/admin/circles', cookies=cookies, json={'name_bn': 'টেস্ট সার্কেল', 'name_en': 'Test Circle', 'description_bn': 'Test', 'active': True})
    assert r.status_code == 200
    circle_id = r.json()['id']
    r = client.put(f'/api/v1/admin/circles/{circle_id}', cookies=cookies, json={'name_bn': 'টেস্ট সার্কেল আপডেট', 'name_en': 'Test Circle Updated', 'description_bn': 'Test 2', 'active': True})
    assert r.status_code == 200
    r = client.delete(f'/api/v1/admin/circles/{circle_id}', cookies=cookies)
    assert r.status_code == 200
    r = client.patch('/api/v1/admin/messages/1', cookies=cookies, json={'status': 'IN_PROGRESS'})
    assert r.status_code in (200, 404)
    r = client.get('/api/v1/admin/permissions', cookies=cookies)
    assert r.status_code == 200 and '*' in r.json()['permissions']


def test_public_asset_upload_and_serving():
    cookies = login('admin@example.org')
    r = client.post('/api/v1/admin/uploads/public', cookies=cookies, files={'file': ('hello.txt', b'hello', 'text/plain')})
    assert r.status_code == 400
    r = client.post('/api/v1/admin/uploads/public', cookies=cookies, files={'file': ('hello.pdf', b'%PDF-1.4\n', 'application/pdf')})
    assert r.status_code == 200
    url = r.json()['url']
    r = client.get(url)
    assert r.status_code == 200
