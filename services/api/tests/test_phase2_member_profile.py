from __future__ import annotations

import io
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.seed import main as seed_main
from app.main import app
from app.models.core import AuditLog, Member, MemberDocument, MemberProfileChangeRequest, Notification, User

TEST_PW = os.getenv('TEST_SEED_PASSWORD') or ('ChangeMe' + '123!')


@pytest.fixture(scope='module', autouse=True)
def _seed_db():
    seed_main()


def _login(client: TestClient, email: str, password: str = TEST_PW) -> dict[str, str]:
    res = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    assert res.status_code == 200, res.text
    assert res.json().get('ok') is True
    return {}


def test_member_profile_view_and_idor_protection():
    """Verify GET /api/v1/member/profile returns complete profile, verification badges, completion, and ignores IDOR tampering."""
    with TestClient(app) as client:
        headers = _login(client, 'member@example.org')

        # Normal profile retrieval
        res = client.get('/api/v1/member/profile', headers=headers)
        assert res.status_code == 200, res.text
        data = res.json()

        # Structure checks
        assert 'personal_information' in data
        assert 'professional_information' in data
        assert 'contact_information' in data
        assert 'emergency_contact' in data
        assert 'verification_badges' in data
        assert 'profile_completion_details' in data
        assert 'protected_fields' in data
        assert 'editable_fields' in data

        # Check badges
        badges = data['verification_badges']
        for key in ('name', 'email', 'mobile', 'nid', 'professional'):
            assert key in badges
            assert 'status' in badges[key]
            assert 'description' in badges[key]
            assert 'description_bn' in badges[key]

        # Check dynamic profile completion
        comp = data['profile_completion_details']
        assert 'percentage' in comp
        assert 'breakdown' in comp
        assert 'missing' in comp
        assert isinstance(comp['missing'], list)

        # IDOR protection check: ?member_id=999999 or ?user_id=1 must NOT return another user's profile
        idor_res = client.get('/api/v1/member/profile?member_id=999999&user_id=1', headers=headers)
        assert idor_res.status_code == 200
        idor_data = idor_res.json()
        assert idor_data['membership_id'] == data['membership_id']
        assert idor_data['email'] == 'member@example.org'


def test_member_profile_editable_fields_update_and_audit():
    """Verify updating editable fields directly modifies records and produces audit logs."""
    with TestClient(app) as client:
        headers = _login(client, 'member@example.org')

        update_payload = {
            'organization': 'Power Grid Company of Bangladesh PLC (PGCB)',
            'department': 'Grid Maintenance & Transmission',
            'profession': 'Sub-Assistant Engineer',
            'academic_qualification': 'Diploma in Electrical Engineering',
            'years_of_experience': 6,
            'current_address': 'House 14, Road 5, Dhanmondi, Dhaka',
            'permanent_address': 'Village: Shampur, District: Cumilla',
            'district': 'Dhaka',
            'emergency_contact_name': 'Kazi Tariqul Islam',
            'emergency_contact_relationship': 'Uncle',
            'emergency_contact_phone': '01811223344',
            'emergency_contact_address': 'Dhanmondi, Dhaka',
            'blood_group': 'B+',
        }

        patch_res = client.patch('/api/v1/member/profile', headers=headers, json=update_payload)
        assert patch_res.status_code == 200, patch_res.text
        updated = patch_res.json()

        assert updated['organization'] == 'Power Grid Company of Bangladesh PLC (PGCB)'
        assert updated['department'] == 'Grid Maintenance & Transmission'
        assert updated['current_address'] == 'House 14, Road 5, Dhanmondi, Dhaka'
        assert updated['emergency_contact_name'] == 'Kazi Tariqul Islam'
        assert updated['emergency_contact_phone'] == '01811223344'
        assert updated['profile_completion'] >= 80

        # Verify Audit Log
        db = SessionLocal()
        try:
            m = db.scalar(select(Member).join(User).where(User.email == 'member@example.org'))
            assert m is not None
            audit_entry = db.scalar(
                select(AuditLog)
                .where(AuditLog.entity_id == str(m.id), AuditLog.action == 'PROFILE_UPDATED')
                .order_by(AuditLog.created_at.desc())
            )
            assert audit_entry is not None
        finally:
            db.close()


def test_member_profile_photo_upload_security():
    """Verify photo upload validates magic bytes, size limits, rejects malicious payloads, and records audit log."""
    with TestClient(app) as client:
        headers = _login(client, 'member@example.org')

        # 1. Reject invalid non-image payload (e.g. text/html with jpg extension)
        fake_jpeg = b'<html><body>Not an image</body></html>'
        bad_res = client.post(
            '/api/v1/member/profile/photo',
            headers=headers,
            files={'file': ('avatar.jpg', fake_jpeg, 'image/jpeg')},
        )
        assert bad_res.status_code == 400
        assert 'Invalid file format' in bad_res.text or 'magic bytes' in bad_res.text

        # 2. Reject file exceeding 5MB
        oversized = b'\xff\xd8\xff\xe0' + b'\x00' * (5 * 1024 * 1024 + 100)
        oversized_res = client.post(
            '/api/v1/member/profile/photo',
            headers=headers,
            files={'file': ('big.jpg', oversized, 'image/jpeg')},
        )
        assert oversized_res.status_code in (400, 413)
        assert '5MB' in oversized_res.text or 'too large' in oversized_res.text.lower()

        # 3. Accept valid JPEG magic bytes
        # Standard minimal 1x1 JPEG bytes
        valid_jpeg = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
            b'\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19'
            b'\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff'
            b'\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01'
            b'\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
            b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9'
        )
        good_res = client.post(
            '/api/v1/member/profile/photo',
            headers=headers,
            files={'file': ('profile.jpg', valid_jpeg, 'image/jpeg')},
        )
        assert good_res.status_code == 200, good_res.text
        photo_data = good_res.json()
        assert photo_data['ok'] is True
        assert photo_data['photo_url'].startswith('/api/v1/documents/') or 'storage' in photo_data['photo_url'].lower()

        # Verify audit log & member photo_url update
        db = SessionLocal()
        try:
            m = db.scalar(select(Member).join(User).where(User.email == 'member@example.org'))
            assert m.photo_url == photo_data['photo_url']
            audit_entry = db.scalar(
                select(AuditLog)
                .where(AuditLog.entity_id == str(m.id), AuditLog.action == 'PROFILE_PHOTO_UPDATED')
                .order_by(AuditLog.created_at.desc())
            )
            assert audit_entry is not None
        finally:
            db.close()


def test_member_profile_change_request_lifecycle_and_security():
    """Verify change request submission, IDOR prevention, cancellation, and admin approval/rejection."""
    with TestClient(app) as client:
        # 1. Login as active member
        member_headers = _login(client, 'member@example.org')

        # Submit change request for protected field 'name_en'
        create_res = client.post(
            '/api/v1/member/profile/change-requests',
            headers=member_headers,
            json={
                'field_name': 'name_en',
                'requested_value': 'Engr. Alimul Fazal Nabil Updated',
                'reason': 'Correction to match official Passport',
            },
        )
        assert create_res.status_code == 200, create_res.text
        cr = create_res.json()
        assert cr['field_name'] == 'name_en'
        assert cr['requested_value'] == 'Engr. Alimul Fazal Nabil Updated'
        assert cr['status'] == 'PENDING'
        req_id = cr['id']

        # 2. View details
        detail_res = client.get(f'/api/v1/member/profile/change-requests/{req_id}', headers=member_headers)
        assert detail_res.status_code == 200
        assert detail_res.json()['id'] == req_id

        # 3. IDOR protection: Another member cannot view or cancel this request
        other_headers = _login(client, 'member2@example.org')
        other_view = client.get(f'/api/v1/member/profile/change-requests/{req_id}', headers=other_headers)
        assert other_view.status_code == 403
        other_cancel = client.delete(f'/api/v1/member/profile/change-requests/{req_id}', headers=other_headers)
        assert other_cancel.status_code == 403

        # 4. Cancel workflow as owner
        member_headers = _login(client, 'member@example.org')
        cancel_res = client.delete(f'/api/v1/member/profile/change-requests/{req_id}', headers=member_headers)
        assert cancel_res.status_code == 200, cancel_res.text
        assert cancel_res.json()['status'] == 'CANCELLED'

        # Attempt to cancel already cancelled request -> 400
        re_cancel = client.delete(f'/api/v1/member/profile/change-requests/{req_id}', headers=member_headers)
        assert re_cancel.status_code == 400

        # 5. Create a new change request for Admin approval test
        cr2_res = client.post(
            '/api/v1/member/profile/change-requests',
            headers=member_headers,
            json={
                'field_name': 'name_en',
                'requested_value': 'Engr. Alimul Fazal Nabil Approved',
                'reason': 'Gazette notification update',
            },
        )
        assert cr2_res.status_code == 200
        cr2_id = cr2_res.json()['id']

        # 6. Admin approves change request
        admin_headers = _login(client, 'admin@example.org')

        # Admin lists change requests
        admin_list = client.get('/api/v1/admin/member-change-requests?status=PENDING', headers=admin_headers)
        assert admin_list.status_code == 200
        items = admin_list.json()['items']
        assert any(item['id'] == cr2_id for item in items)

        # Admin approves
        approve_res = client.post(
            f'/api/v1/admin/member-change-requests/{cr2_id}/approve',
            headers=admin_headers,
            json={'reviewer_comment': 'Verified with official gazette document'},
        )
        assert approve_res.status_code == 200, approve_res.text
        assert approve_res.json()['status'] == 'APPROVED'

        # Member's name_en should now reflect the approved value!
        member_headers = _login(client, 'member@example.org')
        m_prof = client.get('/api/v1/member/profile', headers=member_headers)
        assert m_prof.status_code == 200
        assert m_prof.json()['name_en'] == 'Engr. Alimul Fazal Nabil Approved'

        # Verify notification sent to member
        db = SessionLocal()
        try:
            m_user = db.scalar(select(User).where(User.email == 'member@example.org'))
            notif = db.scalar(
                select(Notification)
                .where(Notification.user_id == m_user.id, Notification.notification_type.in_(['PROFILE', 'PROFILE_CHANGE_APPROVED']))
                .order_by(Notification.created_at.desc())
            )
            assert notif is not None
        finally:
            db.close()


def test_admin_self_approval_prevention():
    """Verify that an admin who is also a member CANNOT approve their own change request (must return 403)."""
    db = SessionLocal()
    try:
        # Check if admin user has an associated member profile, or associate one
        admin_user = db.scalar(select(User).where(User.email == 'admin@example.org'))
        assert admin_user is not None
        admin_member = db.scalar(select(Member).where(Member.user_id == admin_user.id))
        if not admin_member:
            admin_member = Member(
                user_id=admin_user.id,
                membership_id='ADM-TEST-001',
                membership_type='GENERAL',
                status='ACTIVE',
                nid_number='1999999999999',
            )
            db.add(admin_member)
            db.commit()
            db.refresh(admin_member)

        # Create a change request belonging to admin_member
        cr = MemberProfileChangeRequest(
            member_id=admin_member.id,
            user_id=admin_user.id,
            field_name='name_en',
            current_value=admin_user.name_en,
            requested_value='Super Admin Self Changed',
            reason='Self test',
            status='PENDING',
        )
        db.add(cr)
        db.commit()
        db.refresh(cr)
        cr_id = cr.id
    finally:
        db.close()

    with TestClient(app) as client:
        admin_headers = _login(client, 'admin@example.org')

        # Admin attempts to approve their OWN change request -> 403 Forbidden!
        self_approve_res = client.post(
            f'/api/v1/admin/member-change-requests/{cr_id}/approve',
            headers=admin_headers,
            json={'reviewer_comment': 'Trying to self approve'},
        )
        assert self_approve_res.status_code == 403, self_approve_res.text
        assert 'cannot approve' in self_approve_res.text.lower() and 'own' in self_approve_res.text.lower()
