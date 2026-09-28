"""
End-to-End Business Workflow Integration Tests for PGCB Portal.
Validates complete user journeys across Membership, Events & Attendance, Certificates, and Payments.
"""

from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.models import User, Event, EventRegistration, Member
from app.core.security import hash_password, create_token
from app.db.session import SessionLocal
from app.services import MembershipService, EventService, CertificateService, PaymentService

client = TestClient(app)


def _get_admin_cookie() -> dict:
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.email == 'admin@example.org'))
        if not admin:
            admin = User(
                email='admin@example.org',
                password_hash=hash_password('ChangeMe123!'),
                role='SUPER_ADMIN',
                is_active=True,
                email_verified=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
        token, _ = create_token(admin.id)
        return {'access_token': token}


def test_membership_full_lifecycle():
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.email == 'admin@example.org'))
        applicant_user = User(
            email=f"e2e_app_{datetime.utcnow().timestamp()}@example.org",
            password_hash=hash_password("Pass123!"),
            name_bn="ইটুঈ আবেদনকারী",
            name_en="E2E Applicant",
            role="MEMBER",
            is_active=True,
            email_verified=True,
        )
        db.add(applicant_user)
        db.commit()
        db.refresh(applicant_user)

        # 1. Submit application
        member = MembershipService.submit_application(
            db=db,
            user=applicant_user,
            data={
                'name_bn': 'ইটুঈ আবেদনকারী',
                'name_en': 'E2E Applicant',
                'designation_bn': 'সহকারী প্রকৌশলী',
                'membership_type': 'REGULAR',
            },
        )
        assert member.status == 'SUBMITTED'
        assert member.application_no.startswith('PGCB-APP-')

        # 2. Move to Review
        reviewed = MembershipService.review_application(
            db=db,
            admin_user=admin,
            member_id=member.id,
            action='REVIEW',
        )
        assert reviewed.status == 'UNDER_REVIEW'

        # 3. Approve Application
        approved = MembershipService.review_application(
            db=db,
            admin_user=admin,
            member_id=member.id,
            action='APPROVE',
        )
        assert approved.status == 'ACTIVE'
        assert approved.membership_id.startswith('PGD-')

        # 4. Suspend Member
        suspended = MembershipService.review_application(
            db=db,
            admin_user=admin,
            member_id=member.id,
            action='SUSPEND',
        )
        assert suspended.status == 'SUSPENDED'

        # 5. Reactivate Member
        reactivated = MembershipService.review_application(
            db=db,
            admin_user=admin,
            member_id=member.id,
            action='REACTIVATE',
        )
        assert reactivated.status == 'ACTIVE'


def test_event_registration_qr_checkin_anti_reuse():
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.email == 'admin@example.org'))
        participant = User(
            email=f"event_part_{datetime.utcnow().timestamp()}@example.org",
            password_hash=hash_password("Pass123!"),
            name_bn="ইভেন্ট প্রতিনিধি",
            role="MEMBER",
            is_active=True,
            email_verified=True,
        )
        db.add(participant)

        event = Event(
            title_bn="ইটুঈ বার্ষিক কারিগরি সম্মেলন",
            event_date=datetime.utcnow(),
            location_bn="প্রধান কার্যালয়",
            capacity=100,
            fee_amount=0,
            registration_enabled=True,
            is_published=True,
        )
        db.add(event)
        db.commit()
        db.refresh(participant)
        db.refresh(event)

        # 1. Register for event
        reg = EventService.register_for_event(
            db=db,
            event_id=event.id,
            user=participant,
            data={'ticket_count': 1},
        )
        assert reg.ticket_code.startswith('TKT-')
        assert reg.payment_status == 'PAID'
        assert reg.attendance_status in ('NOT_CHECKED_IN', 'REGISTERED')

        # 2. Check in via ticket code (First scan - Valid)
        checkin_res = EventService.check_in_ticket(
            db=db,
            ticket_code=reg.ticket_code,
            admin_user=admin,
        )
        assert checkin_res['ok'] is True
        assert checkin_res['attendance_status'] == 'CHECKED_IN'

        # 3. Check in via ticket code (Second scan - Anti-reuse Rejection)
        try:
            EventService.check_in_ticket(
                db=db,
                ticket_code=reg.ticket_code,
                admin_user=admin,
            )
            assert False, "Duplicate QR checkin should have been rejected"
        except Exception as e:
            assert 'ইতিমধ্যে ব্যবহৃত' in str(e) or 'reused' in str(e).lower() or getattr(e, 'status_code', None) == 409


def test_certificate_issuance_and_revocation():
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.email == 'admin@example.org'))
        recipient = User(
            email=f"cert_rec_{datetime.utcnow().timestamp()}@example.org",
            password_hash=hash_password("Pass123!"),
            name_bn="সনদ গ্রহীতা",
            role="MEMBER",
            is_active=True,
            email_verified=True,
        )
        db.add(recipient)
        db.commit()
        db.refresh(recipient)

        # 1. Issue certificate
        cert = CertificateService.issue_certificate(
            db=db,
            admin_user=admin,
            recipient_user_id=recipient.id,
            certificate_type='MEMBERSHIP',
        )
        assert cert.status == 'ISSUED'
        assert cert.certificate_number.startswith('PGCB-CERT-')

        # 2. Public verification (Valid)
        verification = CertificateService.verify_public(db, cert.token)
        assert verification['valid'] is True
        assert verification['status'] == 'ISSUED'
        assert verification['recipient_name'] == 'সনদ গ্রহীতা'
        # Crucial privacy assertion: No private email or phone exposed
        assert 'email' not in verification
        assert 'phone' not in verification

        # 3. Revoke certificate
        revoked = CertificateService.revoke_certificate(
            db=db,
            admin_user=admin,
            cert_id_or_token=cert.token,
            reason="তথ্যের গরমিল পাওয়া গেছে",
        )
        assert revoked.status == 'REVOKED'

        # 4. Public verification after revocation
        rev_verification = CertificateService.verify_public(db, cert.token)
        assert rev_verification['valid'] is False
        assert rev_verification['revoked'] is True
        assert rev_verification['revocation_reason'] == "তথ্যের গরমিল পাওয়া গেছে"


def test_payment_service_lifecycle():
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == 'admin@example.org'))

        # 1. Create transaction
        trx, checkout = PaymentService.create_transaction(
            db=db,
            user=user,
            amount=500.0,
            purpose='MEMBERSHIP_FEE',
            method='BKASH',
        )
        assert trx.status == 'INITIATED'
        assert trx.transaction_id.startswith('PGCB-TX-')
        assert 'checkout' in checkout['payment_url']

        # 2. Complete transaction
        completed = PaymentService.complete_transaction(
            db=db,
            transaction_id=trx.transaction_id,
            provider_payload={'trxID': 'TRX99887766'},
            actor_user=user,
        )
        assert completed.status == 'SUCCESS'
        assert completed.provider_transaction_id == 'TRX99887766'
        assert completed.completed_at is not None


def test_p0_golden_e2e_and_security_sprint():
    """
    P0.1 – P0.7 Golden E2E & Production Blocker Verification:
    REGISTER -> LOGIN -> PROFILE -> DOCUMENT -> APPLICATION -> ADMIN REVIEW ->
    PAYMENT -> PAYMENT VERIFICATION -> APPROVAL -> MEMBERSHIP ID ->
    DIGITAL ID -> QR VERIFICATION -> CERTIFICATE
    Plus P0.2 IDOR prevention, P0.3 client amount tampering rejection,
    P0.4 DB uniqueness constraints, P0.5 controlled document download, and P0.6 DR drill.
    """
    import io
    from sqlalchemy.exc import IntegrityError
    from scripts.backup_pgcb import run_disaster_recovery_drill

    # P0.1: Deployment foundation health & readiness checks
    health_res = client.get('/health')
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data['status'] == 'ok'
    assert health_data['database'] == 'connected'

    ready_res = client.get('/ready')
    assert ready_res.status_code == 200
    assert ready_res.json()['status'] == 'ready'

    ts_suffix = int(datetime.utcnow().timestamp() * 1000)
    applicant_email = f'golden_e2e_{ts_suffix}@pgcb.gov.bd'
    intruder_email = f'intruder_{ts_suffix}@pgcb.gov.bd'
    password = 'GoldenPass123!'

    # 1. REGISTER (Applicant & Intruder for P0.2 IDOR checks)
    reg_res = client.post(
        '/api/v1/auth/register',
        json={
            'name_bn': 'গোল্ডেন ইটুঈ প্রকৌশলী',
            'name_en': 'Golden E2E Engineer',
            'email': applicant_email,
            'phone': f'017{ts_suffix % 100000000:08d}',
            'password': password,
            'designation_bn': 'উপ-সহকারী প্রকৌশলী',
        },
    )
    assert reg_res.status_code in (200, 201), reg_res.text

    intruder_reg = client.post(
        '/api/v1/auth/register',
        json={
            'name_bn': 'অনধিকার প্রবেশকারী',
            'name_en': 'Intruder Member',
            'email': intruder_email,
            'phone': f'018{ts_suffix % 100000000:08d}',
            'password': password,
            'designation_bn': 'উপ-সহকারী প্রকৌশলী',
        },
    )
    assert intruder_reg.status_code in (200, 201), intruder_reg.text

    # Mark both email_verified so they can log in even when REQUIRE_EMAIL_VERIFICATION is enabled
    with SessionLocal() as db:
        for em in (applicant_email, intruder_email):
            u = db.scalar(select(User).where(User.email == em))
            assert u is not None
            u.email_verified = True
        db.commit()

    # 2. LOGIN
    login_res = client.post('/api/v1/auth/login', json={'email': applicant_email, 'password': password})
    assert login_res.status_code == 200, login_res.text
    applicant_token = login_res.cookies.get('pgcb_access_token') or login_res.json().get('access_token')
    applicant_headers = {'Authorization': f'Bearer {applicant_token}'}

    intruder_login = client.post('/api/v1/auth/login', json={'email': intruder_email, 'password': password})
    assert intruder_login.status_code == 200
    intruder_token = intruder_login.cookies.get('pgcb_access_token') or intruder_login.json().get('access_token')
    intruder_headers = {'Authorization': f'Bearer {intruder_token}'}

    # 3. PROFILE
    prof_res = client.patch(
        '/api/v1/member/profile',
        headers=applicant_headers,
        json={
            'name_bn': 'গোল্ডেন ইটুঈ প্রকৌশলী',
            'name_en': 'Golden E2E Engineer',
            'phone': f'017{ts_suffix % 100000000:08d}',
            'designation_bn': 'উপ-সহকারী প্রকৌশলী',
            'designation_en': 'Sub-Assistant Engineer',
            'employee_id': f'PGCB-EMP-{ts_suffix % 100000}',
            'diploma_institution': 'Dhaka Polytechnic Institute',
            'graduation_year': 2018,
            'nid_number': f'1995{ts_suffix % 1000000000:09d}',
            'date_of_birth': '1995-06-15',
            'current_address': 'Rampura, Dhaka',
            'permanent_address': 'Cumilla, Bangladesh',
            'circle_id': 1,
        },
    )
    assert prof_res.status_code == 200, prof_res.text
    member_id = prof_res.json()['id']

    # 4. DOCUMENT (P0.5: File-type validation, malware scan, safe filename, controlled download)
    # 4a. Malicious EICAR upload must be blocked
    eicar_bytes = b'%PDF-1.4\nX5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
    bad_upload = client.post(
        '/api/v1/member/documents?document_type=NID',
        headers=applicant_headers,
        files={'file': ('nid.pdf', io.BytesIO(eicar_bytes), 'application/pdf')},
    )
    assert bad_upload.status_code == 400

    # 4b. Valid PDF upload succeeds
    valid_pdf = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n'
    doc_res = client.post(
        '/api/v1/member/documents?document_type=NID',
        headers=applicant_headers,
        files={'file': ('official_nid.pdf', io.BytesIO(valid_pdf), 'application/pdf')},
    )
    assert doc_res.status_code == 200, doc_res.text
    doc_id = doc_res.json()['id']

    # 4c. P0.2 & P0.5 IDOR check: Intruder cannot download applicant's document by changing document_id
    idor_dl = client.get(f'/api/v1/member/documents/{doc_id}/download', headers=intruder_headers)
    assert idor_dl.status_code in (403, 404)

    # 4d. Owner controlled download succeeds
    owner_dl = client.get(f'/api/v1/member/documents/{doc_id}/download', headers=applicant_headers)
    assert owner_dl.status_code == 200
    assert owner_dl.content.startswith(b'%PDF-1.4')

    # 5. APPLICATION
    app_res = client.post('/api/v1/member/application', headers=applicant_headers)
    assert app_res.status_code == 200, app_res.text
    assert app_res.json()['status'] == 'SUBMITTED'

    # P0.2: Regular member cannot access admin review endpoints
    idor_admin = client.get('/api/v1/admin/members', headers=intruder_headers)
    assert idor_admin.status_code in (401, 403)

    # 6. ADMIN REVIEW & 7. PAYMENT + 8. PAYMENT VERIFICATION (P0.3)
    # P0.3a: Browser tampering with payment amount must be rejected by the server
    tampered_pay = client.post(
        '/api/v1/member/payments',
        headers=applicant_headers,
        json={
            'purpose': 'MEMBERSHIP',
            'membership_plan_id': 'ANNUAL_STANDARD',
            'amount': 15,  # Tampered low amount
            'provider': 'BKASH',
        },
    )
    assert tampered_pay.status_code == 400

    # P0.3b: Valid server-calculated payment transaction & verification
    with SessionLocal() as db:
        applicant_user = db.scalar(select(User).where(User.email == applicant_email))
        admin_user = db.scalar(select(User).where(User.email == 'admin@example.org'))
        if not admin_user:
            admin_user = User(
                email='admin@example.org',
                password_hash=hash_password('ChangeMe123!'),
                role='SUPER_ADMIN',
                is_active=True,
                email_verified=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

        # Step 6: Admin moves to UNDER_REVIEW
        reviewed = MembershipService.review_application(
            db=db,
            admin_user=admin_user,
            member_id=member_id,
            action='REVIEW',
        )
        assert reviewed.status == 'UNDER_REVIEW'

        # Step 7 & 8: Server-side payment creation & verification
        trx, checkout = PaymentService.create_transaction(
            db=db,
            user=applicant_user,
            amount=500.0,
            purpose='MEMBERSHIP_FEE',
            method='BKASH',
        )
        assert trx.status == 'INITIATED'
        completed_trx = PaymentService.complete_transaction(
            db=db,
            transaction_id=trx.transaction_id,
            provider_payload={'trxID': f'BKASH-GOLDEN-{ts_suffix}'},
            actor_user=admin_user,
        )
        assert completed_trx.status == 'SUCCESS'

        # 9. APPROVAL & 10. MEMBERSHIP ID
        approved = MembershipService.review_application(
            db=db,
            admin_user=admin_user,
            member_id=member_id,
            action='APPROVE',
        )
        assert approved.status == 'ACTIVE'
        assert approved.membership_id is not None
        assigned_mid = approved.membership_id

        # P0.4: Database integrity — duplicate email must be rejected by DB constraint
        dup_user = User(
            email=applicant_email,
            password_hash=hash_password('Dup123!'),
            name_bn='ডুপ্লিকেট',
            role='MEMBER',
        )
        db.add(dup_user)
        try:
            db.commit()
            assert False, 'Duplicate email should have raised IntegrityError'
        except IntegrityError:
            db.rollback()

    # 11. DIGITAL ID
    card_res = client.get('/api/v1/member/card/details', headers=applicant_headers)
    assert card_res.status_code == 200, card_res.text
    card_data = card_res.json()
    assert card_data['membership_id'] == assigned_mid
    assert card_data['status'] == 'ACTIVE'

    # 12. QR VERIFICATION
    qr_res = client.get(f'/api/v1/public/verify/{assigned_mid}')
    assert qr_res.status_code == 200, qr_res.text
    qr_data = qr_res.json()
    assert qr_data['membership_id'] == assigned_mid
    assert qr_data['status'] == 'ACTIVE'
    assert 'nid_number' not in qr_data

    # 13. CERTIFICATE
    cert_list_res = client.get('/api/v1/member/certificates', headers=applicant_headers)
    assert cert_list_res.status_code == 200, cert_list_res.text
    certs = cert_list_res.json()
    assert len(certs) >= 1
    cert_no = certs[0].get('certificate_no') or certs[0].get('certificate_number')
    assert cert_no and cert_no.startswith('PGCB-CERT-')

    cert_verify_res = client.get(f'/api/v1/certificates/verify/{cert_no}')
    assert cert_verify_res.status_code == 200, cert_verify_res.text
    assert cert_verify_res.json()['valid'] is True

    # P0.6: Backup & Restore Verification Drill
    import tempfile
    from pathlib import Path
    from app.core.config import settings
    from app.services import BASE_STORAGE

    with tempfile.TemporaryDirectory() as tmp_backup:
        dr_res = run_disaster_recovery_drill(
            database_url=settings.database_url,
            storage_root=BASE_STORAGE,
            backup_dir=Path(tmp_backup),
        )
        assert dr_res['drill_status'] == 'PASSED'
        assert dr_res['drill_duration_seconds'] < 60


def test_pre_hosting_local_hardening_suite():
    """
    Pre-Hosting Local Hardening Verification:
    1. Core Database (14 core tables present & queryable)
    2. 6-Role RBAC Matrix (Member, Circle Admin, Finance Admin, Content Admin, Central Admin, Super Admin)
    3. Sandbox Payment & Webhook Simulation (Development -> Payment Sandbox -> Webhook Simulation -> Activation)
    """
    from sqlalchemy import inspect as sa_inspect
    from app.db.session import engine
    from app.core.rbac import has_permission

    # 1. Verify all 14 core database entities exist in schema
    inspector = sa_inspect(engine)
    existing_tables = set(inspector.get_table_names())
    required_tables = {
        'users',
        'members',
        'roles',
        'circles',
        'membership_renewals',
        'membership_applications',
        'payment_transactions',
        'documents',
        'certificates',
        'events',
        'notices',
        'circulars',
        'notifications',
        'audit_logs',
    }
    missing = required_tables - existing_tables
    assert not missing, f'Missing core database tables: {missing}'

    # 2. Verify all 6 institutional RBAC roles
    # Member
    assert has_permission('MEMBER', 'member.self') is True
    assert has_permission('MEMBER', 'admin.stats') is False
    # Circle Admin
    assert has_permission('CIRCLE_ADMIN', 'circle.write') is True
    assert has_permission('CIRCLE_ADMIN', 'member.review') is True
    assert has_permission('CIRCLE_ADMIN', 'finance.write') is False
    # Finance Admin
    assert has_permission('FINANCE_ADMIN', 'finance.read') is True
    assert has_permission('FINANCE_ADMIN', 'finance.write') is True
    assert has_permission('FINANCE_ADMIN', 'content.publish') is False
    # Content Admin
    assert has_permission('CONTENT_ADMIN', 'content.publish') is True
    assert has_permission('CONTENT_ADMIN', 'news.publish') is True
    assert has_permission('CONTENT_ADMIN', 'finance.write') is False
    # Central Admin
    assert has_permission('CENTRAL_ADMIN', 'member.review') is True
    assert has_permission('CENTRAL_ADMIN', 'content.publish') is True
    assert has_permission('CENTRAL_ADMIN', 'audit.read') is True
    # Super Admin
    assert has_permission('SUPER_ADMIN', 'finance.write') is True
    assert has_permission('SUPER_ADMIN', 'any.custom.permission') is True

    # 3. Verify Sandbox Payment & Webhook Simulation -> Membership Activation
    ts = int(datetime.utcnow().timestamp() * 1000)
    sb_email = f'sandbox_member_{ts}@pgcb.gov.bd'
    sb_pass = 'SandboxPass123!'
    reg = client.post(
        '/api/v1/auth/register',
        json={
            'name_bn': 'স্যান্ডবক্স সদস্য',
            'name_en': 'Sandbox Member',
            'email': sb_email,
            'phone': f'019{ts % 100000000:08d}',
            'password': sb_pass,
            'designation_bn': 'সহকারী প্রকৌশলী',
        },
    )
    assert reg.status_code in (200, 201)
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.email == sb_email))
        u.email_verified = True
        db.commit()

    login = client.post('/api/v1/auth/login', json={'email': sb_email, 'password': sb_pass})
    assert login.status_code == 200
    token = login.cookies.get('pgcb_access_token') or login.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}

    # Create server-authoritative payment intent in sandbox mode
    pay_intent = client.post(
        '/api/v1/member/payments',
        headers=headers,
        json={
            'purpose': 'MEMBERSHIP',
            'membership_plan_id': 'ANNUAL_STANDARD',
            'provider': 'BKASH',
        },
    )
    assert pay_intent.status_code == 200, pay_intent.text
    payment_id = pay_intent.json()['id']
    assert pay_intent.json()['status'] == 'PENDING'

    # Simulate Sandbox Webhook -> Payment PAID + Receipt Issued + Membership Activated
    sim_res = client.post(
        '/api/v1/payments/sandbox/simulate',
        headers=headers,
        json={'payment_id': payment_id},
    )
    assert sim_res.status_code == 200, sim_res.text
    sim_data = sim_res.json()
    assert sim_data['status'] == 'success'
    assert sim_data['payment_mode'] == 'sandbox'
    assert sim_data['payment_status'] == 'PAID'
    assert sim_data['receipt_no'].startswith('PGCB-RCP-')

    # Idempotent replay check
    replay_res = client.post(
        '/api/v1/payments/sandbox/simulate',
        headers=headers,
        json={'payment_id': payment_id},
    )
    assert replay_res.status_code == 200
    assert replay_res.json()['idempotent_replay'] is True


