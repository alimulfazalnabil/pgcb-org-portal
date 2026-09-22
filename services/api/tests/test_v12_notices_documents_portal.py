from datetime import datetime
from io import BytesIO
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models import User
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


def test_public_settings():
    r = client.get('/api/v1/public/settings')
    assert r.status_code == 200, r.text
    data = r.json()
    assert 'org_name_bn' in data or isinstance(data, dict)


def test_notices_crud_and_urgent():
    cookies = _login()
    
    # 1. Create urgent notice as admin
    payload = {
        'title_bn': 'জরুরী বিদ্যুৎ ব্যবস্থাপনা নোটিশ',
        'title_en': 'Emergency Power Management Notice',
        'content_bn': 'গ্রিড রক্ষণাবেক্ষণের জন্য সাময়িক নির্দেশনা।',
        'content_en': 'Temporary instructions for grid maintenance.',
        'category': 'CIRCULAR',
        'priority': 'URGENT',
        'is_urgent': True,
        'is_pinned': True,
        'is_published': True
    }
    r = client.post('/api/v1/notices', cookies=cookies, json=payload)
    assert r.status_code == 201, r.text
    notice = r.json()
    notice_id = notice['id']
    assert notice['priority'] == 'URGENT'

    # 2. Query public urgent notice
    r_urgent = client.get('/api/v1/notices/urgent')
    assert r_urgent.status_code == 200, r_urgent.text
    urgent_notice = r_urgent.json()
    assert urgent_notice is not None
    assert urgent_notice['id'] == notice_id

    # 3. Query public list
    r_list = client.get('/api/v1/notices?category=CIRCULAR')
    assert r_list.status_code == 200, r_list.text
    items = r_list.json()
    assert any(n['id'] == notice_id for n in items)

    # 4. View single notice
    r_single = client.get(f'/api/v1/notices/{notice_id}')
    assert r_single.status_code == 200, r_single.text
    assert r_single.json()['id'] == notice_id


def test_documents_crud_and_download():
    cookies = _login()

    # 1. Upload document file as admin
    dummy_file = BytesIO(b'%PDF-1.4 simulated pdf document for pgcb')
    files = {'file': ('service_rules_2026.pdf', dummy_file, 'application/pdf')}
    r_up = client.post('/api/v1/documents/upload', cookies=cookies, files=files)
    assert r_up.status_code == 201, r_up.text
    upload_res = r_up.json()
    assert 'file_path' in upload_res

    # 2. Create document record
    doc_payload = {
        'title_bn': 'কর্মচারী আচরণ বিধিমালা ২০২৬',
        'title_en': 'Employee Code of Conduct 2026',
        'category': 'RULE',
        'description_bn': 'পিজিসিবি কর্মচারী আচরণ নির্দেশিকা',
        'file_path': upload_res['file_path'],
        'file_size': upload_res['file_size'],
        'content_type': upload_res['content_type'],
        'is_published': True
    }
    r = client.post('/api/v1/documents', cookies=cookies, json=doc_payload)
    assert r.status_code == 201, r.text
    doc = r.json()
    doc_id = doc['id']
    assert doc['category'] == 'RULE'

    # 3. Public document list
    r_list = client.get('/api/v1/documents?category=RULE')
    assert r_list.status_code == 200, r_list.text
    items = r_list.json()
    assert any(d['id'] == doc_id for d in items)

    # 4. Stream download and increment download counter
    r_dl = client.get(f'/api/v1/documents/{doc_id}/download')
    assert r_dl.status_code == 200, r_dl.text
    assert r_dl.content.startswith(b'%PDF-1.4')

    # Verify counter incremented
    r_single = client.get(f'/api/v1/documents/{doc_id}')
    assert r_single.status_code == 200
    assert r_single.json()['download_count'] >= 1


def test_public_membership_application_and_track():
    app_data = {
        'name_bn': 'প্রকৌশলী রফিকুল ইসলাম',
        'name_en': 'Engr. Rafiqul Islam',
        'email': f'rafiq.{datetime.utcnow().timestamp()}@example.org',
        'phone': '01711223344',
        'designation_bn': 'উপ-বিভাগীয় প্রকৌশলী',
        'password': 'StrongPassword123!',
        'membership_type': 'FULL'
    }
    r = client.post('/api/v1/public/membership/apply', json=app_data)
    assert r.status_code == 200, r.text
    res = r.json()
    assert res['ok'] is True
    app_no = res['application_no']
    assert app_no.startswith('APP-')

    # Track application
    r_track = client.get(f'/api/v1/public/membership/track/{app_no}')
    assert r_track.status_code == 200, r_track.text
    track_res = r_track.json()
    assert track_res['application_no'] == app_no
    assert track_res['status'] == 'SUBMITTED'


def test_admin_csv_member_import():
    cookies = _login()

    ts = datetime.utcnow().timestamp()
    csv_data = f"""full_name_bn,full_name_en,email,phone,designation,circle
মো: করিম উল্লাহ,Md. Karim Ullah,karim.{ts}@example.org,01811223344,Assistant Engineer,Dhaka
তারেক মাহমুদ,Tarek Mahmud,tarek.{ts}@example.org,01911223344,Sub-Assistant Engineer,Chattogram
"""
    files = {'file': ('test_members.csv', BytesIO(csv_data.encode('utf-8')), 'text/csv')}
    r_preview = client.post('/api/v1/admin/imports/members/preview', cookies=cookies, files=files)
    assert r_preview.status_code == 200, r_preview.text
    preview = r_preview.json()
    assert preview['total_rows'] == 2
    assert preview['valid_count'] == 2

    # Commit import
    r_commit = client.post('/api/v1/admin/imports/members/commit', cookies=cookies, json={'rows': preview['rows']})
    assert r_commit.status_code == 200, r_commit.text
    commit_res = r_commit.json()
    assert commit_res['imported_count'] == 2


def test_auth_password_change():
    cookies = _login('admin@example.org', 'ChangeMe123!')
    
    r = client.post('/api/v1/auth/password/change', cookies=cookies, json={
        'old_password': 'ChangeMe123!',
        'new_password': 'NewAdminPass2026!'
    })
    assert r.status_code == 200, r.text
    assert r.json()['ok'] is True

    # Test login with old password fails
    r_old = client.post('/api/v1/auth/login', json={'email': 'admin@example.org', 'password': 'ChangeMe123!'})
    assert r_old.status_code == 401

    # Test login with new password succeeds
    r_new = client.post('/api/v1/auth/login', json={'email': 'admin@example.org', 'password': 'NewAdminPass2026!'})
    assert r_new.status_code == 200

    # Reset back to ChangeMe123! for subsequent tests
    _login('admin@example.org', 'ChangeMe123!')
