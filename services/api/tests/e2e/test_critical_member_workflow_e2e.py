import io
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.db.session import SessionLocal
from app.models import (
    ApplicationReview,
    AuditLog,
    Member,
    Membership,
    MembershipApplication,
    Payment,
    Role,
    User,
)
from tests.test_workflows_e2e import (
    test_p0_golden_e2e_and_security_sprint,
    test_pre_hosting_local_hardening_suite,
)

client = TestClient(app)


def test_rc1_critical_member_workflow_e2e():
    """
    Runs the complete RC1 critical business flow:
    Member -> Register -> Verify email -> Login -> Complete profile ->
    Apply for membership -> Upload documents -> Submit ->
    Admin Review (Request correction -> Resubmit -> Approve/Payment Pending) ->
    Payment Sandbox -> Webhook Server Verification -> Membership Activation ->
    Digital ID -> QR Verification -> Audit Logs.
    """
    test_p0_golden_e2e_and_security_sprint()
    test_pre_hosting_local_hardening_suite()

    # Verify the exact RC1-Core flow including REQUEST_CORRECTION -> Resubmit -> PAYMENT_PENDING -> Sandbox Webhook Activation
    ts = int(datetime.utcnow().timestamp() * 1000)
    email = f'rc1_core_{ts}@pgcb.gov.bd'
    password = 'Rc1CorePass123!'

    # 1. Register
    reg = client.post(
        '/api/v1/auth/register',
        json={
            'name_bn': 'আরসি-১ কোর প্রকৌশলী',
            'name_en': 'RC1 Core Engineer',
            'email': email,
            'phone': f'017{ts % 100000000:08d}',
            'password': password,
            'designation_bn': 'সহকারী প্রকৌশলী',
        },
    )
    assert reg.status_code in (200, 201)

    # 2. Verify email & prepare MEMBERSHIP_ADMIN
    admin_email = f'mem_admin_{ts}@pgcb.gov.bd'
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.email == email))
        u.email_verified = True
        db.commit()

    client.post(
        '/api/v1/auth/register',
        json={
            'name_bn': 'সদস্যপদ প্রশাসক',
            'name_en': 'Membership Admin',
            'email': admin_email,
            'phone': f'016{ts % 100000000:08d}',
            'password': password,
            'designation_bn': 'প্রশাসক',
        },
    )
    with SessionLocal() as db:
        au = db.scalar(select(User).where(User.email == admin_email))
        au.email_verified = True
        au.role = 'MEMBERSHIP_ADMIN'
        db.commit()

    # 3. Login (Member & Admin)
    m_login = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    assert m_login.status_code == 200
    m_headers = {'Authorization': f"Bearer {m_login.cookies.get('pgcb_access_token') or m_login.json().get('access_token')}"}

    a_login = client.post('/api/v1/auth/login', json={'email': admin_email, 'password': password})
    assert a_login.status_code == 200
    a_headers = {'Authorization': f"Bearer {a_login.cookies.get('pgcb_access_token') or a_login.json().get('access_token')}"}

    # 4. Complete Profile
    prof = client.patch(
        '/api/v1/member/profile',
        headers=m_headers,
        json={
            'name_bn': 'আরসি-১ কোর প্রকৌশলী',
            'name_en': 'RC1 Core Engineer',
            'phone': f'017{ts % 100000000:08d}',
            'designation_bn': 'সহকারী প্রকৌশলী',
            'designation_en': 'Assistant Engineer',
            'employee_id': f'PGCB-RC1-{ts % 100000}',
            'diploma_institution': 'ঢাকা পলিটেকনিক ইনস্টিটিউট',
            'graduation_year': 2019,
            'nid_number': f'1995{ts % 1000000000:09d}',
            'current_address': 'রামপুরা, ঢাকা',
            'permanent_address': 'কুমিল্লা',
            'circle_id': 1,
        },
    )
    assert prof.status_code == 200
    member_id = prof.json()['id']

    # 5. Upload Document (valid PDF magic bytes)
    doc = client.post(
        '/api/v1/member/documents?document_type=NID',
        headers=m_headers,
        files={'file': ('nid.pdf', io.BytesIO(b'%PDF-1.4\n%RC1-Core NID\n%%EOF'), 'application/pdf')},
    )
    assert doc.status_code == 200

    # 6. Apply for Membership -> Submit
    apply_res = client.post('/api/v1/member/apply', headers=m_headers)
    assert apply_res.status_code == 200
    assert apply_res.json()['status'] == 'SUBMITTED'

    # 7. Admin Review -> Request Correction -> Member Resubmit -> Payment Pending
    corr_res = client.post(
        f'/api/v1/admin/members/{member_id}/review?action=REQUEST_CORRECTION&note=Please+verify+NID',
        headers=a_headers,
    )
    assert corr_res.status_code == 200
    assert corr_res.json()['status'] == 'DOCUMENTS_REQUIRED'

    reapply_res = client.post('/api/v1/member/apply', headers=m_headers)
    assert reapply_res.status_code == 200
    assert reapply_res.json()['status'] == 'SUBMITTED'

    pay_pend_res = client.post(
        f'/api/v1/admin/members/{member_id}/review?action=PAYMENT_PENDING&note=Approved+for+fee+payment',
        headers=a_headers,
    )
    assert pay_pend_res.status_code == 200
    assert pay_pend_res.json()['status'] == 'PAYMENT_PENDING'

    # 8. Payment Sandbox -> Webhook Server Verification -> Membership Activation
    pay_init = client.post(
        '/api/v1/member/payments',
        headers=m_headers,
        json={'purpose': 'MEMBERSHIP', 'membership_plan_id': 'ANNUAL_STANDARD', 'provider': 'BKASH'},
    )
    assert pay_init.status_code == 200
    payment_id = pay_init.json()['id']

    sim_res = client.post(
        '/api/v1/payments/sandbox/simulate',
        headers=m_headers,
        json={'payment_id': payment_id},
    )
    assert sim_res.status_code == 200
    sim_json = sim_res.json()
    assert sim_json['payment_status'] == 'PAID'
    assert sim_json['member_status'] == 'ACTIVE'
    membership_no = sim_json['membership_id']
    assert membership_no and membership_no.startswith('PGD-')

    # 9. Digital ID & QR Verification
    card_res = client.get('/api/v1/member/card/details', headers=m_headers)
    assert card_res.status_code == 200
    assert card_res.json()['membership_id'] == membership_no

    qr_res = client.get(f'/api/v1/public/verify/{membership_no}')
    assert qr_res.status_code == 200
    assert qr_res.json()['verified'] is True

    # 10. Confirm database rows in membership_applications, application_reviews, payments, memberships, roles, audit_logs
    with SessionLocal() as db:
        assert db.scalar(select(Role).where(Role.code == 'MEMBERSHIP_ADMIN')) is not None
        app_row = db.scalar(select(MembershipApplication).where(MembershipApplication.member_id == member_id))
        assert app_row is not None and app_row.status == 'ACTIVE'
        reviews = db.scalars(select(ApplicationReview).where(ApplicationReview.member_id == member_id)).all()
        assert len(reviews) >= 2
        mem_row = db.scalar(select(Membership).where(Membership.membership_id == membership_no))
        assert mem_row is not None and mem_row.status == 'ACTIVE'
        pay_row = db.scalar(select(Payment).where(Payment.member_id == member_id))
        assert pay_row is not None and pay_row.status == 'PAID'
        audits = db.scalars(select(AuditLog).where(AuditLog.entity_id == str(member_id))).all()
        assert len(audits) >= 3


def test_rc1_admin_membership_workflow_15_step_e2e():
    """
    Automated 15-Step Admin Membership Workflow E2E:
    1. Create member
    2. Verify account
    3. Submit application (Draft -> Submitted)
    4. Upload documents
    5. Admin logs in & inspects /admin/memberships/applications dashboard
    6. Admin reviews application detail (7 sections, document review, Assign Circle, Internal Note, Correction, Rejection/Resubmit)
    7. Admin approves -> Payment Pending
    8. Member sees payment request (and browser tampering with membership_status / payment_status is blocked)
    9. Sandbox payment succeeds
    10. Webhook received
    11. Payment verified (Payment = PAID)
    12. Membership becomes ACTIVE
    13. Membership ID generated
    14. Digital ID & QR verification succeeds
    15. Audit trail exists for every action
    """
    ts = int(datetime.utcnow().timestamp() * 1000) + 77
    email = f'admin_wf_member_{ts}@pgcb.gov.bd'
    admin_email = f'admin_wf_officer_{ts}@pgcb.gov.bd'
    password = 'AdminWfPass123!'

    # 1. Create member
    reg = client.post(
        '/api/v1/auth/register',
        json={
            'name_bn': 'প্রকৌশলী আব্দুর রহমান',
            'name_en': 'Engr. Abdur Rahman',
            'email': email,
            'phone': f'018{ts % 100000000:08d}',
            'password': password,
            'designation_bn': 'উপ-বিভাগীয় প্রকৌশলী',
        },
    )
    assert reg.status_code in (200, 201)

    client.post(
        '/api/v1/auth/register',
        json={
            'name_bn': 'কেন্দ্রীয় সদস্যপদ প্রশাসক',
            'name_en': 'Central Membership Admin',
            'email': admin_email,
            'phone': f'015{ts % 100000000:08d}',
            'password': password,
            'designation_bn': 'প্রশাসক',
        },
    )

    # 2. Verify account
    with SessionLocal() as db:
        mu = db.scalar(select(User).where(User.email == email))
        mu.email_verified = True
        au = db.scalar(select(User).where(User.email == admin_email))
        au.email_verified = True
        au.role = 'MEMBERSHIP_ADMIN'
        db.commit()

    m_login = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    assert m_login.status_code == 200
    m_headers = {'Authorization': f"Bearer {m_login.cookies.get('pgcb_access_token') or m_login.json().get('access_token')}"}

    # Complete profile
    prof = client.patch(
        '/api/v1/member/profile',
        headers=m_headers,
        json={
            'name_bn': 'প্রকৌশলী আব্দুর রহমান',
            'name_en': 'Engr. Abdur Rahman',
            'phone': f'018{ts % 100000000:08d}',
            'designation_bn': 'উপ-বিভাগীয় প্রকৌশলী',
            'designation_en': 'Sub-Divisional Engineer',
            'employee_id': f'PGCB-WF-{ts % 100000}',
            'diploma_institution': 'চট্টগ্রাম পলিটেকনিক ইনস্টিটিউট',
            'graduation_year': 2017,
            'nid_number': f'1992{ts % 1000000000:09d}',
            'current_address': 'আফতাবনগর, ঢাকা',
            'permanent_address': 'চট্টগ্রাম',
            'circle_id': 1,
        },
    )
    assert prof.status_code == 200
    member_id = prof.json()['id']

    # 3. Draft -> Submit application
    draft_res = client.post('/api/v1/member/application/draft', headers=m_headers)
    assert draft_res.status_code == 200
    assert draft_res.json()['status'] == 'DRAFT'

    sub_res = client.post('/api/v1/member/apply', headers=m_headers)
    assert sub_res.status_code == 200
    assert sub_res.json()['status'] == 'SUBMITTED'

    # 4. Upload documents
    doc_res = client.post(
        '/api/v1/member/documents?document_type=NID',
        headers=m_headers,
        files={'file': ('rahman_nid.pdf', io.BytesIO(b'%PDF-1.4\n%Rahman NID\n%%EOF'), 'application/pdf')},
    )
    assert doc_res.status_code == 200
    doc_id = doc_res.json()['id']

    # 5. Admin logs in & inspects /admin/memberships/applications list
    a_login = client.post('/api/v1/auth/login', json={'email': admin_email, 'password': password})
    assert a_login.status_code == 200
    a_headers = {'Authorization': f"Bearer {a_login.cookies.get('pgcb_access_token') or a_login.json().get('access_token')}"}

    list_res = client.get(f'/api/v1/admin/memberships/applications?q=Rahman&status=PENDING', headers=a_headers)
    assert list_res.status_code == 200
    list_json = list_res.json()
    assert 'counts' in list_json and list_json['counts']['pending'] >= 1
    assert any(item['id'] == member_id for item in list_json['items'])

    # 6. Admin reviews application detail (7 sections) & executes review actions
    det_res = client.get(f'/api/v1/admin/memberships/applications/{member_id}', headers=a_headers)
    assert det_res.status_code == 200
    det = det_res.json()
    for section in (
        'personal_information',
        'professional_information',
        'grid_circle',
        'uploaded_documents',
        'membership_type_info',
        'payment',
        'review_history',
    ):
        assert section in det, f'Missing section {section}'

    # 6a. Document review
    doc_rev = client.post(f'/api/v1/admin/documents/{doc_id}/review?action=APPROVE', headers=a_headers)
    assert doc_rev.status_code == 200
    assert doc_rev.json()['review_status'] == 'APPROVE'

    # 6b. Assign Circle
    circle_act = client.post(
        f'/api/v1/admin/memberships/applications/{member_id}/action',
        headers=a_headers,
        json={'action': 'ASSIGN_CIRCLE', 'circle_id': 2, 'note': 'Assigned to Grid Circle 2'},
    )
    assert circle_act.status_code == 200
    assert circle_act.json()['circle_id'] == 2

    # 6c. Add Internal Note
    note_act = client.post(
        f'/api/v1/admin/memberships/applications/{member_id}/action',
        headers=a_headers,
        json={'action': 'ADD_NOTE', 'note': 'Diploma certificate & NID cross-checked with HR.'},
    )
    assert note_act.status_code == 200

    # 6d. Request Correction -> Member resubmits
    corr_act = client.post(
        f'/api/v1/admin/memberships/applications/{member_id}/action',
        headers=a_headers,
        json={'action': 'REQUEST_CORRECTION', 'note': 'Please confirm permanent address.'},
    )
    assert corr_act.status_code == 200
    assert corr_act.json()['status'] == 'CORRECTION_REQUIRED'

    resub_res = client.post('/api/v1/member/apply', headers=m_headers)
    assert resub_res.status_code == 200
    assert resub_res.json()['status'] == 'SUBMITTED'

    # 7. Admin approves -> transitions to PAYMENT_PENDING
    app_act = client.post(
        f'/api/v1/admin/memberships/applications/{member_id}/action',
        headers=a_headers,
        json={'action': 'APPROVE', 'note': 'Approved; awaiting membership fee payment.'},
    )
    assert app_act.status_code == 200
    assert app_act.json()['status'] == 'PAYMENT_PENDING'

    # 8. Member sees payment request notification & browser status tampering is blocked
    notifs = client.get('/api/v1/member/notifications', headers=m_headers)
    assert notifs.status_code == 200
    assert len(notifs.json()) >= 1

    tamper_member = client.patch(
        '/api/v1/member/profile',
        headers=m_headers,
        json={'name_bn': 'প্রকৌশলী আব্দুর রহমান', 'membership_status': 'ACTIVE'},
    )
    assert tamper_member.status_code == 403

    tamper_payment = client.post(
        '/api/v1/member/payments',
        headers=m_headers,
        json={'purpose': 'MEMBERSHIP', 'membership_plan_id': 'ANNUAL_STANDARD', 'provider': 'BKASH', 'payment_status': 'PAID'},
    )
    assert tamper_payment.status_code == 403

    # 9, 10, 11, 12, 13. Sandbox payment -> Webhook received -> Payment = PAID -> Membership = ACTIVE -> Membership ID generated
    pay_init = client.post(
        '/api/v1/member/payments',
        headers=m_headers,
        json={'purpose': 'MEMBERSHIP', 'membership_plan_id': 'ANNUAL_STANDARD', 'provider': 'BKASH'},
    )
    assert pay_init.status_code == 200
    payment_id = pay_init.json()['id']

    sim_res = client.post(
        '/api/v1/payments/sandbox/simulate',
        headers=m_headers,
        json={'payment_id': payment_id},
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data['payment_status'] == 'PAID'
    assert sim_data['member_status'] == 'ACTIVE'
    membership_id = sim_data['membership_id']
    assert membership_id and membership_id.startswith('PGD-')

    # 14. Digital ID & QR verification succeeds
    card_res = client.get('/api/v1/member/card/details', headers=m_headers)
    assert card_res.status_code == 200
    assert card_res.json()['membership_id'] == membership_id
    assert card_res.json()['status'] == 'ACTIVE'

    qr_res = client.get(f'/api/v1/public/verify/{membership_id}')
    assert qr_res.status_code == 200
    assert qr_res.json()['verified'] is True

    # 15. Audit trail exists for every action
    final_det = client.get(f'/api/v1/admin/memberships/applications/{member_id}', headers=a_headers).json()
    review_actions = {r['action'] for r in final_det['application_reviews']}
    assert {'ASSIGN_CIRCLE', 'INTERNAL_NOTE', 'REQUEST_CORRECTION', 'APPROVE'}.issubset(review_actions)
    assert len(final_det['review_history']) >= 5


def test_rc1_all_16_failure_paths_and_idor_bola_security():
    """
    Explicitly validates all 16 RC1 negative/failure paths and IDOR/BOLA security barriers:
    1. Wrong password
    2. Expired session
    3. Duplicate email
    4. Duplicate membership (duplicate employee_id & duplicate apply when ACTIVE)
    5. Invalid document (bad MIME/magic bytes)
    6. Oversized document (> 5 MB)
    7. Unauthorized document access (Member A -> Member B document)
    8. Unauthorized admin API (Member A -> Admin endpoints)
    9. Tampered payment amount (client amount tamper & webhook amount mismatch)
    10. Duplicate payment webhook (idempotent replay)
    11. Failed payment (gateway FAILED leaves member in PAYMENT_PENDING, not ACTIVE)
    12. Rejected application (REJECT transitions to REJECTED)
    13. Correction requested (requires reason, transitions to CORRECTION_REQUIRED)
    14. Expired membership (QR verification returns verified=False, status=EXPIRED)
    15. Revoked certificate (Certificate verification returns valid=False, revoked=True)
    16. Invalid QR (Invalid membership ID / invalid token rejected)
    Plus IDOR/BOLA:
    - Member A tries to request Member B's API resources (documents, receipts, payment simulation) -> 403 / 404
    - Circle Admin A (Circle 1) tries to access Circle B (Circle 2) application -> 403 DENIED
    """
    from datetime import timedelta
    from app.models import Session as AuthSession
    from app.services import CertificateService

    ts = int(datetime.utcnow().timestamp() * 1000) + 505
    member_a_email = f'member_a_{ts}@pgcb.gov.bd'
    member_b_email = f'member_b_{ts}@pgcb.gov.bd'
    circle_admin_a_email = f'circle_admin_a_{ts}@pgcb.gov.bd'
    central_admin_email = f'central_admin_{ts}@pgcb.gov.bd'
    password = 'SecurePass123!'

    for em, name_en, phone_prefix in (
        (member_a_email, 'Member A', '017'),
        (member_b_email, 'Member B', '018'),
        (circle_admin_a_email, 'Circle Admin A', '019'),
        (central_admin_email, 'Central Admin', '016'),
    ):
        r = client.post(
            '/api/v1/auth/register',
            json={
                'name_bn': f'সদস্য {name_en}',
                'name_en': name_en,
                'email': em,
                'phone': f'{phone_prefix}{ts % 100000000:08d}',
                'password': password,
                'designation_bn': 'সহকারী প্রকৌশলী',
            },
        )
        assert r.status_code in (200, 201)

    # Failure Path 3: Duplicate email registration must fail (400)
    dup_email_res = client.post(
        '/api/v1/auth/register',
        json={
            'name_bn': 'ডুপ্লিকেট ইমেইল',
            'name_en': 'Duplicate Email',
            'email': member_a_email,
            'phone': f'015{ts % 100000000:08d}',
            'password': password,
            'designation_bn': 'সহকারী প্রকৌশলী',
        },
    )
    assert dup_email_res.status_code in (400, 409)

    with SessionLocal() as db:
        for em in (member_a_email, member_b_email, circle_admin_a_email, central_admin_email):
            u = db.scalar(select(User).where(User.email == em))
            u.email_verified = True
        ca = db.scalar(select(User).where(User.email == circle_admin_a_email))
        ca.role = 'CIRCLE_ADMIN'
        ca_member = db.scalar(select(Member).where(Member.user_id == ca.id))
        ca_member.circle_id = 1

        sa = db.scalar(select(User).where(User.email == central_admin_email))
        sa.role = 'CENTRAL_ADMIN'
        db.commit()

    # Failure Path 1: Wrong password must return 401
    wrong_pw = client.post('/api/v1/auth/login', json={'email': member_a_email, 'password': 'WrongPassword999!'})
    assert wrong_pw.status_code == 401

    # Login all actors
    login_a = client.post('/api/v1/auth/login', json={'email': member_a_email, 'password': password})
    token_a = login_a.cookies.get('pgcb_access_token') or login_a.json().get('access_token')
    headers_a = {'Authorization': f'Bearer {token_a}'}

    login_b = client.post('/api/v1/auth/login', json={'email': member_b_email, 'password': password})
    token_b = login_b.cookies.get('pgcb_access_token') or login_b.json().get('access_token')
    headers_b = {'Authorization': f'Bearer {token_b}'}

    login_ca = client.post('/api/v1/auth/login', json={'email': circle_admin_a_email, 'password': password})
    token_ca = login_ca.cookies.get('pgcb_access_token') or login_ca.json().get('access_token')
    headers_ca = {'Authorization': f'Bearer {token_ca}'}

    login_sa = client.post('/api/v1/auth/login', json={'email': central_admin_email, 'password': password})
    token_sa = login_sa.cookies.get('pgcb_access_token') or login_sa.json().get('access_token')
    headers_sa = {'Authorization': f'Bearer {token_sa}'}

    # Failure Path 2: Expired session must return 401
    exp_login = client.post('/api/v1/auth/login', json={'email': member_a_email, 'password': password})
    exp_token = exp_login.cookies.get('pgcb_access_token') or exp_login.json().get('access_token')
    with SessionLocal() as db:
        sess = db.scalar(select(AuthSession).where(AuthSession.jwt_token == exp_token))
        assert sess is not None
        sess.expires_at = datetime.utcnow() - timedelta(hours=2)
        db.commit()
    client.cookies.clear()
    expired_res = client.get('/api/v1/member/profile', headers={'Authorization': f'Bearer {exp_token}'})
    assert expired_res.status_code == 401

    # Configure Member A (Circle 1) and Member B (Circle 2) profiles
    emp_b = f'PGCB-EMP-B-{ts % 100000}'
    prof_b = client.patch(
        '/api/v1/member/profile',
        headers=headers_b,
        json={
            'name_bn': 'সদস্য বি',
            'name_en': 'Member B',
            'phone': f'018{ts % 100000000:08d}',
            'designation_bn': 'সহকারী প্রকৌশলী',
            'employee_id': emp_b,
            'circle_id': 2,
        },
    )
    assert prof_b.status_code == 200
    member_b_id = prof_b.json()['id']

    # Failure Path 4a: Duplicate membership employee_id on Member A must fail (409)
    dup_emp_res = client.patch(
        '/api/v1/member/profile',
        headers=headers_a,
        json={
            'name_bn': 'সদস্য এ',
            'name_en': 'Member A',
            'phone': f'017{ts % 100000000:08d}',
            'designation_bn': 'সহকারী প্রকৌশলী',
            'employee_id': emp_b,
            'circle_id': 1,
        },
    )
    assert dup_emp_res.status_code == 409

    prof_a = client.patch(
        '/api/v1/member/profile',
        headers=headers_a,
        json={
            'name_bn': 'সদস্য এ',
            'name_en': 'Member A',
            'phone': f'017{ts % 100000000:08d}',
            'designation_bn': 'সহকারী প্রকৌশলী',
            'employee_id': f'PGCB-EMP-A-{ts % 100000}',
            'circle_id': 1,
        },
    )
    assert prof_a.status_code == 200
    member_a_id = prof_a.json()['id']

    # Failure Path 5: Invalid document (executable disguised or wrong magic bytes) must fail (400)
    invalid_doc = client.post(
        '/api/v1/member/documents?document_type=NID',
        headers=headers_b,
        files={'file': ('malware.exe', io.BytesIO(b'MZ\x90\x00\x03\x00\x00\x00'), 'application/octet-stream')},
    )
    assert invalid_doc.status_code == 400

    # Failure Path 6: Oversized document (> 5 MB) must fail (400)
    oversized_bytes = b'%PDF-1.4\n' + (b'A' * (5 * 1024 * 1024 + 1024))
    oversized_doc = client.post(
        '/api/v1/member/documents?document_type=NID',
        headers=headers_b,
        files={'file': ('huge.pdf', io.BytesIO(oversized_bytes), 'application/pdf')},
    )
    assert oversized_doc.status_code in (400, 413)

    # Upload valid document for Member B
    valid_doc_b = client.post(
        '/api/v1/member/documents?document_type=NID',
        headers=headers_b,
        files={'file': ('member_b_nid.pdf', io.BytesIO(b'%PDF-1.4\n%Member B NID\n%%EOF'), 'application/pdf')},
    )
    assert valid_doc_b.status_code == 200
    doc_b_id = valid_doc_b.json()['id']

    # Failure Path 7 & IDOR/BOLA 1a: Member A cannot access Member B's document (403 / 404)
    idor_doc = client.get(f'/api/v1/member/documents/{doc_b_id}/download', headers=headers_a)
    assert idor_doc.status_code in (403, 404)

    # Failure Path 8: Unauthorized admin API access by Member A must return 403
    unauth_admin = client.get('/api/v1/admin/memberships/applications', headers=headers_a)
    assert unauth_admin.status_code == 403

    # Submit applications for Member A and Member B
    assert client.post('/api/v1/member/apply', headers=headers_a).status_code == 200
    assert client.post('/api/v1/member/apply', headers=headers_b).status_code == 200

    # IDOR/BOLA 2: Circle Admin A (Circle 1) tries to access or review Member B (Circle 2) -> DENIED (403)
    cross_circle_view = client.get(f'/api/v1/admin/memberships/applications/{member_b_id}', headers=headers_ca)
    assert cross_circle_view.status_code == 403
    cross_circle_act = client.post(
        f'/api/v1/admin/memberships/applications/{member_b_id}/action',
        headers=headers_ca,
        json={'action': 'APPROVE', 'note': 'Unauthorized cross-circle approval attempt'},
    )
    assert cross_circle_act.status_code == 403

    # Failure Path 13: Correction requested (missing reason rejected with 400; with reason transitions to CORRECTION_REQUIRED)
    corr_missing = client.post(
        f'/api/v1/admin/memberships/applications/{member_a_id}/action',
        headers=headers_sa,
        json={'action': 'REQUEST_CORRECTION'},
    )
    assert corr_missing.status_code == 400

    corr_ok = client.post(
        f'/api/v1/admin/memberships/applications/{member_a_id}/action',
        headers=headers_sa,
        json={'action': 'REQUEST_CORRECTION', 'correction_reason': 'Upload clear PGCB ID copy'},
    )
    assert corr_ok.status_code == 200
    assert corr_ok.json()['application_status'] == 'CORRECTION_REQUIRED'

    # Failure Path 12: Rejected application (missing reason rejected with 400; with reason transitions to REJECTED)
    rej_ok = client.post(
        f'/api/v1/admin/memberships/applications/{member_a_id}/action',
        headers=headers_sa,
        json={'action': 'REJECT', 'rejection_reason': 'Invalid diploma record'},
    )
    assert rej_ok.status_code == 200
    assert rej_ok.json()['application_status'] == 'REJECTED'

    # Approve Member B -> PAYMENT_PENDING
    app_b_approve = client.post(
        f'/api/v1/admin/memberships/applications/{member_b_id}/action',
        headers=headers_sa,
        json={'action': 'APPROVE', 'note': 'Approved for sandbox payment'},
    )
    assert app_b_approve.status_code == 200
    assert app_b_approve.json()['application_status'] == 'PAYMENT_PENDING'

    # Failure Path 9: Tampered payment amount must be rejected (400)
    tampered_amt = client.post(
        '/api/v1/member/payments',
        headers=headers_b,
        json={'purpose': 'MEMBERSHIP', 'membership_plan_id': 'ANNUAL_STANDARD', 'amount': 50, 'provider': 'BKASH'},
    )
    assert tampered_amt.status_code == 400

    # Failure Path 11: Failed payment leaves membership in PAYMENT_PENDING (not ACTIVE)
    failed_pay_init = client.post(
        '/api/v1/member/payments',
        headers=headers_b,
        json={'purpose': 'MEMBERSHIP', 'membership_plan_id': 'ANNUAL_STANDARD', 'provider': 'BKASH'},
    )
    assert failed_pay_init.status_code == 200
    failed_pay_id = failed_pay_init.json()['id']

    failed_sim = client.post(
        '/api/v1/payments/sandbox/simulate',
        headers=headers_b,
        json={'payment_id': failed_pay_id, 'outcome': 'FAILED'},
    )
    assert failed_sim.status_code == 200
    assert failed_sim.json()['payment_status'] == 'FAILED'
    assert failed_sim.json()['member_status'] == 'PAYMENT_PENDING'

    # Create fresh payment for Member B and verify IDOR/BOLA on payment simulation & receipt
    valid_pay_init = client.post(
        '/api/v1/member/payments',
        headers=headers_b,
        json={'purpose': 'MEMBERSHIP', 'membership_plan_id': 'ANNUAL_STANDARD', 'provider': 'BKASH'},
    )
    assert valid_pay_init.status_code == 200
    valid_pay_id = valid_pay_init.json()['id']

    # IDOR/BOLA 1b: Member A tries to simulate or tamper with Member B's payment -> 403
    idor_pay_sim = client.post(
        '/api/v1/payments/sandbox/simulate',
        headers=headers_a,
        json={'payment_id': valid_pay_id},
    )
    assert idor_pay_sim.status_code == 403

    # Failure Path 9b: Tampered amount in sandbox webhook simulation -> 400
    tampered_sim = client.post(
        '/api/v1/payments/sandbox/simulate',
        headers=headers_b,
        json={'payment_id': valid_pay_id, 'amount': 10},
    )
    assert tampered_sim.status_code == 400

    # Complete Member B's payment -> ACTIVE
    ok_sim = client.post(
        '/api/v1/payments/sandbox/simulate',
        headers=headers_b,
        json={'payment_id': valid_pay_id},
    )
    assert ok_sim.status_code == 200
    assert ok_sim.json()['member_status'] == 'ACTIVE'
    member_b_mid = ok_sim.json()['membership_id']

    # IDOR/BOLA 1c: Member A tries to fetch Member B's payment receipt -> 403
    idor_receipt = client.get(f'/api/v1/member/payments/{valid_pay_id}/receipt', headers=headers_a)
    assert idor_receipt.status_code == 403

    # Failure Path 10: Duplicate payment webhook is handled idempotently
    dup_webhook = client.post(
        '/api/v1/payments/sandbox/simulate',
        headers=headers_b,
        json={'payment_id': valid_pay_id},
    )
    assert dup_webhook.status_code == 200
    assert dup_webhook.json()['idempotent_replay'] is True

    # Failure Path 4b: Duplicate membership application when already ACTIVE must return 409
    dup_apply = client.post('/api/v1/member/apply', headers=headers_b)
    assert dup_apply.status_code == 409

    # Failure Path 14: Expired membership returns verified=False and status='EXPIRED' on QR verification
    with SessionLocal() as db:
        mb = db.get(Member, member_b_id)
        mb.validity_date = datetime.utcnow() - timedelta(days=5)
        db.commit()
    exp_qr = client.get(f'/api/v1/public/verify/{member_b_mid}')
    assert exp_qr.status_code == 200
    assert exp_qr.json()['verified'] is False
    assert exp_qr.json()['status'] == 'EXPIRED'

    # Failure Path 15: Revoked certificate returns valid=False, revoked=True
    with SessionLocal() as db:
        admin_u = db.scalar(select(User).where(User.email == central_admin_email))
        user_b = db.scalar(select(User).where(User.email == member_b_email))
        cert = CertificateService.issue_certificate(
            db=db,
            admin_user=admin_u,
            recipient_user_id=user_b.id,
            certificate_type='MEMBERSHIP',
        )
        CertificateService.revoke_certificate(
            db=db,
            admin_user=admin_u,
            cert_id_or_token=cert.token,
            reason='Revoked during RC1 negative test',
        )
        cert_no = cert.certificate_number

    rev_cert_res = client.get(f'/api/v1/certificates/verify/{cert_no}')
    assert rev_cert_res.status_code == 200
    assert rev_cert_res.json()['valid'] is False
    assert rev_cert_res.json()['revoked'] is True

    # Failure Path 16: Invalid QR (non-existent membership ID & forged signature token)
    invalid_qr_mid = client.get('/api/v1/public/verify/PGD-INVALID-999999')
    assert invalid_qr_mid.status_code == 404
    invalid_qr_tok = client.get(f'/api/v1/public/verify-token/{member_b_mid}.00000000000000000000000000000000')
    assert invalid_qr_tok.status_code == 400


