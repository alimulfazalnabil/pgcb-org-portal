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

