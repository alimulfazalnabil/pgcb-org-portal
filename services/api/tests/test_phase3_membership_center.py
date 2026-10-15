import io
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.db.session import SessionLocal
from app.models import (
    Circle,
    Member,
    MemberDocument,
    MembershipApplication,
    MembershipRenewal,
    MembershipStatusHistory,
    PaymentTransaction,
    User,
)
from app.core.security import hash_password


@pytest.fixture
def client():
    return TestClient(app)


def _setup_member_with_status(db, email, status='ACTIVE', days_remaining=100, member_type='PROFESSIONAL'):
    # Clean up any existing records
    user = db.scalar(select(User).where(User.email == email))
    if user:
        m = db.scalar(select(Member).where(Member.user_id == user.id))
        if m:
            db.query(MembershipStatusHistory).filter(MembershipStatusHistory.member_id == m.id).delete()
            db.query(MembershipRenewal).filter(MembershipRenewal.member_id == m.id).delete()
            db.query(PaymentTransaction).filter(PaymentTransaction.member_id == m.id).delete()
            db.query(MemberDocument).filter(MemberDocument.member_id == m.id).delete()
            db.query(MembershipApplication).filter(MembershipApplication.member_id == m.id).delete()
            db.delete(m)
        db.delete(user)
        db.commit()

    circle = db.scalar(select(Circle).where(Circle.name_en == 'Dhaka'))
    if not circle:
        circle = Circle(name_bn='ঢাকা', name_en='Dhaka', active=True)
        db.add(circle)
        db.flush()

    user = User(
        email=email,
        password_hash=hash_password('Password123!'),
        name_bn='প্রকৌশলী টেস্ট',
        name_en='Engr. Test Member',
        phone='01711223344',
        role='MEMBER',
        is_active=True,
        email_verified=True,
    )
    db.add(user)
    db.flush()

    now = datetime.utcnow()
    valid_until = now + timedelta(days=days_remaining) if days_remaining is not None else None

    member = Member(
        user_id=user.id,
        membership_id=f'PGCB-{now.year}-{user.id:04d}',
        application_no=f'PGCB-APP-{now.year}-{user.id:04d}',
        membership_type=member_type,
        designation_bn='সহকারী প্রকৌশলী',
        circle_id=circle.id,
        status=status,
        issue_date=now - timedelta(days=365),
        validity_date=valid_until,
    )
    db.add(member)
    db.flush()

    # Add verified documents
    doc = MemberDocument(
        member_id=member.id,
        document_type='NID',
        filename='nid_scan.pdf',
        storage_path='storage/documents/test_nid.pdf',
        review_status='APPROVED',
    )
    db.add(doc)
    doc2 = MemberDocument(
        member_id=member.id,
        document_type='ACADEMIC',
        filename='diploma_cert.pdf',
        storage_path='storage/documents/test_academic.pdf',
        review_status='APPROVED',
    )
    db.add(doc2)

    db.commit()
    db.refresh(user)
    db.refresh(member)
    return user, member


def test_membership_summary_and_status_engine(client):
    db = SessionLocal()
    try:
        # 1. Active member with 100 days remaining
        user_active, m_active = _setup_member_with_status(db, 'p3.active@example.org', status='ACTIVE', days_remaining=100)
        client.post('/api/v1/auth/login', json={'email': 'p3.active@example.org', 'password': 'Password123!'})
        res = client.get('/api/v1/member/membership')
        assert res.status_code == 200, res.text
        data = res.json()
        assert data['membership_id'] == m_active.membership_id
        assert data['status'] == 'ACTIVE'
        assert data['days_remaining'] is not None and data['days_remaining'] > 30
        assert data['renewal_available'] is True
        assert data['grid_circle']['name'] == 'Dhaka'

        # 2. Expiring soon member (20 days remaining <= 30 days)
        user_expiring, m_expiring = _setup_member_with_status(db, 'p3.expiring@example.org', status='ACTIVE', days_remaining=20)
        client.post('/api/v1/auth/login', json={'email': 'p3.expiring@example.org', 'password': 'Password123!'})
        res2 = client.get('/api/v1/member/membership')
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2['status'] == 'EXPIRING_SOON'
        assert data2['days_remaining'] == 20
        assert data2['renewal_available'] is True

        # 3. Expired member (-5 days remaining)
        user_expired, m_expired = _setup_member_with_status(db, 'p3.expired@example.org', status='ACTIVE', days_remaining=-5)
        client.post('/api/v1/auth/login', json={'email': 'p3.expired@example.org', 'password': 'Password123!'})
        res3 = client.get('/api/v1/member/membership')
        assert res3.status_code == 200
        data3 = res3.json()
        assert data3['status'] == 'EXPIRED'
        assert data3['days_remaining'] < 0
        assert data3['renewal_available'] is True

        # 4. Suspended member override (valid_until in future, but status = SUSPENDED)
        user_suspended, m_suspended = _setup_member_with_status(db, 'p3.suspended@example.org', status='SUSPENDED', days_remaining=300)
        client.post('/api/v1/auth/login', json={'email': 'p3.suspended@example.org', 'password': 'Password123!'})
        res4 = client.get('/api/v1/member/membership')
        assert res4.status_code == 200
        data4 = res4.json()
        # MUST return SUSPENDED, overriding date calculation!
        assert data4['status'] == 'SUSPENDED'
        assert data4['renewal_available'] is False
        assert 'স্থগিত' in (data4['renewal_ineligible_reason'] or '')
    finally:
        db.close()


def test_membership_history_and_milestones(client):
    db = SessionLocal()
    try:
        user, member = _setup_member_with_status(db, 'p3.hist@example.org', status='ACTIVE', days_remaining=50)
        client.post('/api/v1/auth/login', json={'email': 'p3.hist@example.org', 'password': 'Password123!'})

        # Add a prior renewal
        r = MembershipRenewal(
            member_id=member.id,
            previous_validity_date=datetime.utcnow() - timedelta(days=365),
            new_validity_date=datetime.utcnow() + timedelta(days=50),
            amount=2000,
            currency='BDT',
            duration_years=1,
            status='COMPLETED',
        )
        db.add(r)
        db.commit()

        res = client.get('/api/v1/member/membership/history')
        assert res.status_code == 200
        data = res.json()
        items = data.get('items', [])
        assert len(items) >= 2
        # Includes initial created record and renewal record
        actions = [item['action'] for item in items]
        assert 'CREATED' in actions
        assert 'RENEWAL' in actions
    finally:
        db.close()


def test_renewal_options_and_submission(client):
    db = SessionLocal()
    try:
        user, member = _setup_member_with_status(db, 'p3.renew@example.org', status='ACTIVE', days_remaining=25)
        client.post('/api/v1/auth/login', json={'email': 'p3.renew@example.org', 'password': 'Password123!'})

        # GET options
        res = client.get('/api/v1/member/membership/renewal/options')
        assert res.status_code == 200
        options = res.json()
        assert options['eligible'] is True
        plans = options['plans']
        assert len(plans) == 3
        assert plans[0]['duration_years'] == 1
        assert plans[1]['duration_years'] == 2
        assert plans[2]['duration_years'] == 3

        # Fee tampering check: client attempts to send amount = 100
        tamper_res = client.post('/api/v1/member/membership/renew', json={'duration_years': 1, 'amount': 100})
        assert tamper_res.status_code == 400
        assert 'does not match' in tamper_res.text

        # Valid submission
        submit_res = client.post('/api/v1/member/membership/renew', json={'duration_years': 2})
        assert submit_res.status_code == 200
        renew_data = submit_res.json()
        assert renew_data['ok'] is True
        assert renew_data['duration_years'] == 2
        assert renew_data['status'] == 'PENDING'
        assert renew_data['transaction_id'] is not None

        # Repeat submission should fail because one renewal application is now pending
        repeat_res = client.post('/api/v1/member/membership/renew', json={'duration_years': 1})
        assert repeat_res.status_code == 400
        assert 'প্রক্রিয়াধীন' in repeat_res.text or 'already in progress' in repeat_res.text.lower()
    finally:
        db.close()


def test_unified_application_center_and_document_upload(client):
    db = SessionLocal()
    try:
        user, member = _setup_member_with_status(db, 'p3.app@example.org', status='DOCUMENTS_REQUIRED', days_remaining=None)
        # Mark one document as rejected
        db.query(MemberDocument).filter(MemberDocument.member_id == member.id).update({'review_status': 'REJECTED', 'reviewer_note': 'Document is blurry'})
        db.commit()

        client.post('/api/v1/auth/login', json={'email': 'p3.app@example.org', 'password': 'Password123!'})

        # GET unified application center
        res = client.get('/api/v1/member/application')
        assert res.status_code == 200
        app_data = res.json()
        assert app_data['status'] == 'DOCUMENTS_REQUIRED'
        assert len(app_data['timeline']) == 6
        assert len(app_data['required_document_types']) >= 1

        # Upload replacement document (valid PDF magic bytes %PDF-1.4)
        pdf_bytes = b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF'
        upload_res = client.post(
            '/api/v1/member/application/documents',
            data={'document_type': 'ACADEMIC'},
            files={'file': ('diploma.pdf', pdf_bytes, 'application/pdf')},
        )
        assert upload_res.status_code == 200
        up_data = upload_res.json()
        assert up_data['ok'] is True
        assert up_data['document']['review_status'] == 'PENDING'

        # Verify member status automatically transitioned from DOCUMENTS_REQUIRED to UNDER_REVIEW
        db.refresh(member)
        assert member.status == 'UNDER_REVIEW'
    finally:
        db.close()
