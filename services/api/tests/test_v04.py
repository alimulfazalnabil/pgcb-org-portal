import time
from app.core.mfa import _hotp, verify_totp
from app.db.session import SessionLocal
from app.models import User
from app.routers.auth import login as login_route
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_totp_roundtrip():
    secret='JBSWY3DPEHPK3PXP'
    counter=int(time.time()//30)
    code=_hotp(secret,counter)
    assert len(code)==6
    assert verify_totp(secret,code)

def test_admin_mfa_setup_enable_login_disable():
    r=client.post('/api/v1/auth/login',json={'email':'admin@example.org','password':'ChangeMe123!'})
    assert r.status_code==200
    cookies=r.cookies
    r=client.post('/api/v1/admin/mfa/setup',cookies=cookies)
    assert r.status_code==200
    secret=r.json()['secret']
    from app.core.mfa import _hotp
    code=_hotp(secret,int(time.time()//30))
    r=client.post('/api/v1/admin/mfa/enable',params={'code':code},cookies=cookies)
    assert r.status_code==200 and r.json()['enabled'] is True

    r=client.post('/api/v1/auth/login',json={'email':'admin@example.org','password':'ChangeMe123!'})
    assert r.status_code==200 and r.json()['mfa_required'] is True
    r=client.post('/api/v1/auth/login',json={'email':'admin@example.org','password':'ChangeMe123!','mfa_code':code})
    assert r.status_code==200

    # cleanup by disabling using a fresh code
    r=client.post('/api/v1/auth/login',json={'email':'admin@example.org','password':'ChangeMe123!','mfa_code':_hotp(secret,int(time.time()//30))})
    assert r.status_code==200
    cookies=r.cookies
    disable_code=_hotp(secret,int(time.time()//30))
    r=client.post('/api/v1/admin/mfa/disable',params={'code':disable_code},cookies=cookies)
    assert r.status_code==200 and r.json()['enabled'] is False
