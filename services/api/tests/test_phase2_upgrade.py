from __future__ import annotations

import os
from pathlib import Path
import tempfile

from fastapi.testclient import TestClient
import pytest

from app.core.mfa import totp_code
from app.db.seed import main as seed_main
from app.integrations.payments import (
    BKashProvider,
    NagadProvider,
    SSLCommerzProvider,
    get_payment_provider,
)
from app.main import app
from app.core.config import settings
from scripts.backup_pgcb import (
    RETENTION_POLICY,
    backup_database,
    backup_storage,
    enforce_retention,
    verify_sqlite_backup_restore,
)

TEST_PW = os.getenv('TEST_SEED_PASSWORD') or ('ChangeMe' + '123!')


@pytest.fixture(scope='module', autouse=True)
def _seed_db():
    seed_main()


def _login(client: TestClient, email: str, password: str = TEST_PW, otp: str | None = None) -> dict[str, str]:
    payload = {'email': email, 'password': password}
    if otp:
        payload['otp_code'] = otp
    res = client.post('/api/v1/auth/login', json=payload)
    assert res.status_code == 200, res.text
    assert res.json().get('ok') is True
    return {}


def test_phase2_1_payment_engine_fail_closed_in_production(monkeypatch):
    """Verify payment gateways never auto-succeed in production/staging without gateway credentials and verification."""
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.delenv('ALLOW_TEST_PAYMENTS', raising=False)
    monkeypatch.delenv('SSLCOMMERZ_STORE_ID', raising=False)
    monkeypatch.delenv('SSLCOMMERZ_STORE_PASS', raising=False)
    monkeypatch.delenv('BKASH_APP_KEY', raising=False)
    monkeypatch.delenv('NAGAD_MERCHANT_ID', raising=False)

    # TestProvider blocked in strict production
    test_prov = get_payment_provider('TEST')
    with pytest.raises(PermissionError):
        test_prov.create_payment(2000.0, 'REF-1', '/portal')
    assert test_prov.verify_payment('TEST-ABCDEF123456', expected_amount=2000.0) is False

    ssl = SSLCommerzProvider()
    assert ssl.verify_payment('PGCB-20260928-ABCDEF1234', expected_amount=2500) is False

    bkash = BKashProvider()
    assert bkash.verify_payment('BKASH-ABCDEF123456', expected_amount=2500) is False

    nagad = NagadProvider()
    assert nagad.verify_payment('NAGAD-ABCDEF123456', expected_amount=2500) is False


def test_phase2_1_payment_amount_validation_and_receipt_workflow():
    """Verify server-side fee schedule, tampered amount rejection, receipt PDF, QR verification, and membership activation."""
    with TestClient(app) as client:
        # 1. Public fee schedule
        fee_res = client.get('/api/v1/public/membership-fees')
        assert fee_res.status_code == 200
        schedule = fee_res.json()
        assert schedule['fees']['GENERAL'] == 2000
        assert schedule['fees']['LIFE'] == 10000

        headers = _login(client, 'member@example.org')

        # 2. Personalized fee calculation
        my_fee = client.get('/api/v1/member/membership-fee', headers=headers)
        assert my_fee.status_code == 200
        assert my_fee.json()['currency'] == 'BDT'

        # 3. Reject tampered client amount (e.g. 1 BDT or 99 BDT)
        bad_init = client.post(
            '/api/v1/member/payments/initiate',
            headers=headers,
            json={'purpose': 'MEMBERSHIP', 'amount': 1, 'provider': 'SSLCOMMERZ'},
        )
        assert bad_init.status_code == 400

        # 4. Reject arbitrary unissued transaction ID in provider verification
        ssl = SSLCommerzProvider()
        unissued = ssl.verify_payment('ARBITRARY-FAKE-TX-99999', expected_amount=2500)
        assert unissued is False

        # 5. Valid initiation + server-verified confirmation -> receipt + PDF + QR token verification
        good_init = client.post(
            '/api/v1/member/payments/initiate',
            headers=headers,
            json={'purpose': 'MEMBERSHIP', 'amount': 2500, 'provider': 'SSLCOMMERZ'},
        )
        assert good_init.status_code == 200, good_init.text
        init_data = good_init.json()
        payment_id = init_data['id']
        tx_id = init_data['transaction_id']

        confirm_res = client.post(
            f'/api/v1/member/payments/{payment_id}/confirm',
            headers=headers,
            params={'provider_reference': tx_id},
        )
        assert confirm_res.status_code == 200, confirm_res.text
        paid_data = confirm_res.json()
        assert paid_data['status'] == 'PAID'
        assert paid_data['receipt_no'].startswith('PGCB-RCP-')

        # 6. Fetch structured receipt & verify QR token
        rcp_res = client.get(f'/api/v1/member/payments/{payment_id}/receipt', headers=headers)
        assert rcp_res.status_code == 200
        rcp_json = rcp_res.json()
        assert rcp_json['receipt_no'] == paid_data['receipt_no']
        assert rcp_json['verification_token']

        pub_verify = client.get(f"/api/v1/public/receipts/verify/{rcp_json['verification_token']}")
        assert pub_verify.status_code == 200
        assert pub_verify.json()['verified'] is True
        assert pub_verify.json()['receipt_no'] == rcp_json['receipt_no']

        # 7. Download 300-DPI PDF receipt
        pdf_res = client.get(f'/api/v1/member/payments/{payment_id}/receipt.pdf', headers=headers)
        assert pdf_res.status_code == 200
        assert pdf_res.headers['content-type'].startswith('application/pdf')
        assert pdf_res.content.startswith(b'%PDF')


def test_phase2_1_backup_and_disaster_recovery_drill():
    """Verify automated backup creation, SHA-256 manifest, retention policy, and clean SQLite restore verification."""
    assert RETENTION_POLICY == {'daily': 14, 'weekly': 8, 'monthly': 12}
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        db_manifest = backup_database(settings.database_url, out_dir, tier='daily')
        st_manifest = backup_storage(Path(settings.storage_root), out_dir, tier='daily')
        assert db_manifest['sha256']
        assert st_manifest['sha256']

        restore_res = verify_sqlite_backup_restore(Path(db_manifest['path']), expected_sha256=db_manifest['sha256'])
        assert restore_res['verified'] is True
        assert 'users' in restore_res['tables_present']

        pruned = enforce_retention(out_dir)
        assert pruned == {'daily': 0, 'weekly': 0, 'monthly': 0}


def test_phase2_2_mfa_backup_codes_and_session_management():
    """Verify MFA TOTP setup, 8 single-use recovery backup codes, login consumption, and active session management."""
    with TestClient(app) as client:
        headers = _login(client, 'officer@example.org')

        # Setup MFA
        setup_res = client.post('/api/v1/admin/mfa/setup', headers=headers)
        assert setup_res.status_code == 200
        secret = setup_res.json()['secret']

        # Enable MFA and receive 8 backup codes
        code = totp_code(secret)
        enable_res = client.post('/api/v1/admin/mfa/enable', headers=headers, json={'code': code})
        assert enable_res.status_code == 200
        enable_data = enable_res.json()
        assert enable_data['enabled'] is True
        backup_codes = enable_data['backup_codes']
        assert len(backup_codes) == 8
        assert all(c.startswith('PGCB-') for c in backup_codes)

        # Login using a single-use backup code
        first_backup = backup_codes[0]
        login_with_backup = client.post(
            '/api/v1/auth/login',
            json={'email': 'officer@example.org', 'password': TEST_PW, 'otp_code': first_backup},
        )
        assert login_with_backup.status_code == 200

        # Re-using the same backup code must fail
        reuse_backup = client.post(
            '/api/v1/auth/login',
            json={'email': 'officer@example.org', 'password': TEST_PW, 'otp_code': first_backup},
        )
        assert reuse_backup.status_code == 401

        # Disable MFA to leave fixture clean for other tests
        disable_res = client.post(
            '/api/v1/admin/mfa/disable',
            headers=headers,
            json={'code': totp_code(secret)},
        )
        assert disable_res.status_code == 200

        # Active sessions list
        sessions_res = client.get('/api/v1/auth/sessions', headers=headers)
        assert sessions_res.status_code == 200
        assert isinstance(sessions_res.json(), list)
        assert len(sessions_res.json()) >= 1


def test_phase2_3_notifications_digital_id_and_unified_search():
    """Verify Notification Center 2.0, Front/Back Digital ID Card + 2-page PDF, and 9-entity Unified Search."""
    with TestClient(app) as client:
        headers = _login(client, 'member@example.org')

        # Notification Center 2.0
        unread = client.get('/api/v1/member/notifications/unread-count', headers=headers)
        assert unread.status_code == 200
        assert 'unread_count' in unread.json()

        prefs_put = client.put(
            '/api/v1/member/notification-preferences',
            headers=headers,
            json={'in_app_enabled': True, 'email_enabled': True, 'sms_enabled': False},
        )
        assert prefs_put.status_code == 200
        assert prefs_put.json()['sms_enabled'] is False

        read_all = client.post('/api/v1/member/notifications/read-all', headers=headers)
        assert read_all.status_code == 200

        # Digital ID Card Front, Back, and 2-page PDF
        front_res = client.get('/api/v1/member/card?side=front', headers=headers)
        assert front_res.status_code == 200
        assert front_res.headers['content-type'] == 'image/png'

        back_res = client.get('/api/v1/member/card/back', headers=headers)
        assert back_res.status_code == 200
        assert back_res.headers['content-type'] == 'image/png'

        pdf_card = client.get('/api/v1/member/card.pdf', headers=headers)
        assert pdf_card.status_code == 200
        assert pdf_card.content.startswith(b'%PDF')

        # Unified Search across 9 entity types + suggestions
        search_res = client.get('/api/v1/public/search', params={'q': 'ঢাকা'})
        assert search_res.status_code == 200
        s_data = search_res.json()
        assert s_data['total'] >= 1
        assert isinstance(s_data['items'], list)

        sugg_res = client.get('/api/v1/public/search/suggestions', params={'q': 'প্রকৌশলী'})
        assert sugg_res.status_code == 200
        assert 'suggestions' in sugg_res.json()


def test_phase2_4_secretariat_circles_workflows_data_quality_analytics_and_templates():
    """Verify 9 official PGCB Grid Circles, multi-entity workflows, Data Quality Engine, Executive Analytics, and 12 Email Templates."""
    with TestClient(app) as client:
        # 1. All 9 official PGCB Grid Circles
        circles_res = client.get('/api/v1/public/circles')
        assert circles_res.status_code == 200
        circles = circles_res.json()
        assert len(circles) >= 9
        en_names = {c.get('name_en') for c in circles}
        for expected in ('Dhaka', 'Chattogram', 'Cumilla', 'Sylhet', 'Khulna', 'Rajshahi', 'Rangpur', 'Mymensingh', 'Barishal'):
            assert expected in en_names

        circle_detail = client.get(f"/api/v1/public/circles/{circles[0]['id']}")
        assert circle_detail.status_code == 200
        assert 'statistics' in circle_detail.json()

        admin_headers = _login(client, 'admin@example.org')

        # 2. Approval workflow across NOTICE (DRAFT -> SUBMITTED -> IN_REVIEW -> APPROVED -> PUBLISHED)
        notices_payload = client.get('/api/v1/notices').json()
        notices = notices_payload if isinstance(notices_payload, list) else notices_payload['items']
        notice_id = notices[0]['id']
        for st in ('DRAFT', 'SUBMITTED', 'IN_REVIEW', 'APPROVED', 'PUBLISHED'):
            wf_res = client.post(
                f'/api/v1/admin/workflows/NOTICE/{notice_id}/transition',
                headers=admin_headers,
                json={'status': st, 'review_note': f'Transition to {st}'},
            )
            assert wf_res.status_code == 200, wf_res.text
            assert wf_res.json()['status'] == st

        # 3. Data Quality Engine
        dq_res = client.get('/api/v1/admin/data-quality', headers=admin_headers)
        assert dq_res.status_code == 200
        dq = dq_res.json()
        assert 'records_requiring_attention' in dq
        for key in (
            'duplicate_nid',
            'duplicate_mobile',
            'duplicate_email',
            'duplicate_membership_id',
            'missing_documents',
            'expired_membership',
            'invalid_circle',
            'incomplete_profile',
        ):
            assert key in dq['summary']

        # 4. Executive Dashboard 2.0 Analytics
        exec_res = client.get('/api/v1/admin/analytics/executive', headers=admin_headers)
        assert exec_res.status_code == 200
        exec_data = exec_res.json()
        assert 'kpis' in exec_data
        assert 'members_by_circle' in exec_data
        assert 'revenue_by_month' in exec_data
        assert 'payment_method_breakdown' in exec_data
        assert 'application_conversion' in exec_data
        assert 'event_attendance' in exec_data
        assert 'certificate_issuance' in exec_data
        assert 'document_downloads' in exec_data

        # 5. 12 Institutional Email Templates
        tpl_res = client.get('/api/v1/admin/email-templates', headers=admin_headers)
        assert tpl_res.status_code == 200
        tpl_data = tpl_res.json()
        assert tpl_data['total'] == 12
        update_tpl = client.put(
            '/api/v1/admin/email-templates/payment_receipt',
            headers=admin_headers,
            json={
                'subject_bn': '[PGCB পোর্টাল] আপডেটেড পেমেন্ট রসিদ {{receipt_no}}',
                'subject_en': '[PGCB Portal] Updated Official Receipt {{receipt_no}}',
                'body_bn': 'প্রিয় {{name}}, আপনার পেমেন্ট রসিদ {{receipt_no}} সফলভাবে যাচাইকৃত হয়েছে।',
                'body_en': 'Dear {{name}}, your payment receipt {{receipt_no}} has been verified.',
            },
        )
        assert update_tpl.status_code == 200
        assert 'Updated Official Receipt' in update_tpl.json()['subject_en']


def test_phase2_5_institutional_ai_helpdesk():
    """Verify PGCB Institutional AI Helpdesk topics and contextual Q&A with database citations."""
    with TestClient(app) as client:
        topics_res = client.get('/api/v1/public/helpdesk/topics')
        assert topics_res.status_code == 200
        assert len(topics_res.json()['topics']) >= 5

        fee_ask = client.post(
            '/api/v1/public/helpdesk/ask',
            json={'question': 'সদস্যপদ ফি ও নবায়ন চার্জ কত টাকা?', 'language': 'bn'},
        )
        assert fee_ask.status_code == 200
        fee_ans = fee_ask.json()
        assert fee_ans['matched_topic'] == 'membership_fees'
        assert '২,৫০০' in fee_ans['answer_bn']

        circ_ask = client.post(
            '/api/v1/public/helpdesk/ask',
            json={'question': 'সর্বশেষ সার্কুলার কী?', 'language': 'bn'},
        )
        assert circ_ask.status_code == 200
        assert circ_ask.json()['matched_topic'] == 'circulars'
        assert len(circ_ask.json()['citations']) >= 1


def test_sprint1_payment_security_idempotency_and_state_machine():
    """
    Verify Sprint 1 Production Hardening:
    1. Server-calculated amount for membership_plan_id (reject tampered amount=1 for ANNUAL_STANDARD).
    2. Idempotency via idempotency_key and provider_transaction_id (no duplicate notifications on replay; 409 on cross-tx reuse).
    3. Strict transaction state machine (SUCCESS -> FAILED is impossible; missing trxID in bKash/Nagad fails verification).
    """
    from app.models.core import PaymentTransaction
    from app.services.payment_service import BKashProvider, NagadProvider

    # 1. Verify bKash and Nagad never synthesize a fake trxID when trxID is missing
    dummy_trx = PaymentTransaction(id=999999, transaction_ref='PGCB-TX-TEST-1', amount=2000.0, status='PENDING')
    bkash_missing = BKashProvider().verify_payment(dummy_trx, {})
    assert bkash_missing['success'] is False
    assert bkash_missing['status'] == 'FAILED'
    assert bkash_missing['provider_transaction_id'] is None

    nagad_missing = NagadProvider().verify_payment(dummy_trx, {'issuerPaymentRefNo': ''})
    assert nagad_missing['success'] is False
    assert nagad_missing['status'] == 'FAILED'
    assert nagad_missing['provider_transaction_id'] is None

    with TestClient(app) as client:
        headers = _login(client, 'member@example.org')

        # 2. Tampered client amount (amount=1 with membership_plan_id='ANNUAL_STANDARD') MUST be rejected (HTTP 400)
        tampered_res = client.post(
            '/api/v1/member/payments/checkout',
            headers=headers,
            json={
                'membership_plan_id': 'ANNUAL_STANDARD',
                'amount': 1,
                'currency': 'BDT',
                'purpose': 'MEMBERSHIP',
                'provider': 'TEST',
            },
        )
        assert tampered_res.status_code == 400
        assert 'ANNUAL_STANDARD' in tampered_res.json()['detail']

        # Unknown membership_plan_id MUST be rejected (HTTP 400)
        invalid_plan_res = client.post(
            '/api/v1/member/payments/checkout',
            headers=headers,
            json={
                'membership_plan_id': 'FAKE_PLAN_999',
                'provider': 'TEST',
            },
        )
        assert invalid_plan_res.status_code == 400

        # 3. Valid membership_plan_id ('ANNUAL_STANDARD') calculates ৳2,000 server-side + idempotency_key deduplication
        from datetime import datetime
        unique_ts = int(datetime.utcnow().timestamp() * 1000)
        idem_key = f'idem-sprint1-annual-standard-{unique_ts}-1'
        checkout_1 = client.post(
            '/api/v1/member/payments/checkout',
            headers=headers,
            json={
                'membership_plan_id': 'ANNUAL_STANDARD',
                'currency': 'BDT',
                'purpose': 'MEMBERSHIP',
                'provider': 'TEST',
                'idempotency_key': idem_key,
            },
        )
        assert checkout_1.status_code == 200, checkout_1.text
        c1_data = checkout_1.json()
        assert c1_data['amount'] == 2000.0
        assert c1_data['membership_plan_id'] == 'ANNUAL_STANDARD'
        tx_id = c1_data['transaction_id']
        prov_tx_id = c1_data['provider_transaction_id']

        # Re-submitting with the same idempotency_key returns the exact same transaction
        checkout_2 = client.post(
            '/api/v1/member/payments/checkout',
            headers=headers,
            json={
                'membership_plan_id': 'ANNUAL_STANDARD',
                'currency': 'BDT',
                'purpose': 'MEMBERSHIP',
                'provider': 'TEST',
                'idempotency_key': idem_key,
            },
        )
        assert checkout_2.status_code == 200
        assert checkout_2.json()['transaction_id'] == tx_id

        # 4. Complete payment via callback and verify idempotent replay does not duplicate notifications
        unread_before = client.get('/api/v1/member/notifications/unread-count', headers=headers).json()['unread_count']

        cb_1 = client.post(
            '/api/v1/payments/callback/TEST',
            json={
                'transaction_id': tx_id,
                'provider_transaction_id': prov_tx_id,
                'status': 'SUCCESS',
                'amount': 2000.0,
            },
        )
        assert cb_1.status_code == 200, cb_1.text
        assert cb_1.json()['status'] in ('PAID', 'SUCCESS')

        unread_after_first = client.get('/api/v1/member/notifications/unread-count', headers=headers).json()['unread_count']
        assert unread_after_first == unread_before + 1

        # Replay identical callback -> returns 200 with idempotent_replay=True and does NOT increment notifications
        cb_replay = client.post(
            '/api/v1/payments/callback/TEST',
            json={
                'transaction_id': tx_id,
                'provider_transaction_id': prov_tx_id,
                'status': 'SUCCESS',
                'amount': 2000.0,
            },
        )
        assert cb_replay.status_code == 200
        assert cb_replay.json().get('idempotent_replay') is True

        unread_after_replay = client.get('/api/v1/member/notifications/unread-count', headers=headers).json()['unread_count']
        assert unread_after_replay == unread_after_first

        # 5. State machine guard: SUCCESS -> FAILED transition via callback MUST be rejected with HTTP 409
        invalid_transition = client.post(
            '/api/v1/payments/callback/TEST',
            json={
                'transaction_id': tx_id,
                'provider_transaction_id': prov_tx_id,
                'status': 'FAILED',
            },
        )
        assert invalid_transition.status_code == 409

        # 6. Cross-transaction provider_transaction_id reuse MUST be rejected with HTTP 409
        other_checkout = client.post(
            '/api/v1/member/payments/checkout',
            headers=headers,
            json={
                'membership_plan_id': 'ANNUAL_STANDARD',
                'provider': 'TEST',
                'idempotency_key': f'idem-sprint1-annual-standard-{unique_ts}-2',
            },
        )
        assert other_checkout.status_code == 200
        other_tx_id = other_checkout.json()['transaction_id']
        assert other_tx_id != tx_id

        reuse_prov_tx = client.post(
            '/api/v1/payments/callback/TEST',
            json={
                'transaction_id': other_tx_id,
                'provider_transaction_id': prov_tx_id,  # Already used by tx_id!
                'status': 'SUCCESS',
            },
        )
        assert reuse_prov_tx.status_code == 409


def test_sprint1_first_production_test_pgd_test_0001():
    """
    Step 8 — First Production Test (TEST MEMBER / PGD-TEST-0001):
    Register -> Login -> Profile -> Document -> Membership application ->
    Admin approval (PGD-TEST-0001) -> Test payment -> Digital ID ->
    QR verification -> Certificate -> Email/In-App notification.
    """
    with TestClient(app) as client:
        test_email = 'pgd.test.0001@example.org'

        # 1. Register TEST MEMBER
        reg_res = client.post(
            '/api/v1/auth/register',
            json={
                'email': test_email,
                'password': TEST_PW,
                'name_bn': 'টেস্ট সদস্য প্রকৌশলী',
                'name_en': 'TEST MEMBER',
                'phone': '01799000001',
            },
        )
        assert reg_res.status_code in (200, 400, 409)  # 400/409 if re-run in same DB

        # 2. Login as TEST MEMBER
        member_headers = _login(client, test_email)

        # 3. Profile update
        prof_patch = client.patch(
            '/api/v1/member/profile',
            headers=member_headers,
            json={
                'name_bn': 'টেস্ট সদস্য প্রকৌশলী',
                'name_en': 'TEST MEMBER',
                'phone': '01799000001',
                'designation_bn': 'সহকারী প্রকৌশলী',
                'designation_en': 'Assistant Engineer',
                'employee_id': 'PGCB-TEST-0001',
                'diploma_institution': 'ঢাকা পলিটেকনিক ইনস্টিটিউট',
                'graduation_year': 2016,
                'nid_number': '1994000000001',
                'current_address': 'পিজিসিবি প্রধান কার্যালয়, ঢাকা',
                'permanent_address': 'ঢাকা, বাংলাদেশ',
            },
        )
        assert prof_patch.status_code == 200, prof_patch.text
        member_id = prof_patch.json()['id']

        # 4. Document upload (valid PDF)
        doc_res = client.post(
            '/api/v1/member/documents?document_type=NID',
            headers=member_headers,
            files={'file': ('pgd_test_0001_nid.pdf', b'%PDF-1.4\n%PGD-TEST-0001 NID\n%%EOF', 'application/pdf')},
        )
        assert doc_res.status_code == 200, doc_res.text

        # 5. Membership application submission
        apply_res = client.post('/api/v1/member/apply', headers=member_headers)
        assert apply_res.status_code in (200, 409), apply_res.text

        # 6. Admin approval with dedicated ID PGD-TEST-0001
        admin_headers = _login(client, 'admin@example.org')
        approve_res = client.post(
            f'/api/v1/admin/members/{member_id}/review',
            params={'action': 'APPROVE', 'membership_id': 'PGD-TEST-0001'},
            headers=admin_headers,
        )
        assert approve_res.status_code == 200, approve_res.text
        assert approve_res.json()['membership_id'] == 'PGD-TEST-0001'
        assert approve_res.json()['status'] == 'ACTIVE'

        # Switch back to TEST MEMBER session for steps 7-9
        member_headers = _login(client, test_email)

        # 7. Test payment (ANNUAL_STANDARD -> ৳2,000 -> callback -> receipt)
        pay_init = client.post(
            '/api/v1/member/payments/checkout',
            headers=member_headers,
            json={
                'membership_plan_id': 'ANNUAL_STANDARD',
                'provider': 'TEST',
                'idempotency_key': 'pgd-test-0001-annual-payment',
            },
        )
        assert pay_init.status_code == 200, pay_init.text
        pay_data = pay_init.json()
        assert pay_data['amount'] == 2000.0

        pay_cb = client.post(
            '/api/v1/payments/callback/TEST',
            json={
                'transaction_id': pay_data['transaction_id'],
                'provider_transaction_id': pay_data['provider_transaction_id'],
                'status': 'SUCCESS',
                'amount': 2000.0,
            },
        )
        assert pay_cb.status_code == 200, pay_cb.text
        assert pay_cb.json()['status'] in ('PAID', 'SUCCESS')

        receipt_pdf = client.get(
            f"/api/v1/member/payments/{pay_data['transaction_id']}/receipt.pdf",
            headers=member_headers,
        )
        assert receipt_pdf.status_code == 200
        assert receipt_pdf.content.startswith(b'%PDF')

        # 8. Digital ID Card (Front, Back, and 2-page PDF)
        card_front = client.get('/api/v1/member/card?side=front', headers=member_headers)
        assert card_front.status_code == 200
        assert card_front.headers['content-type'] == 'image/png'

        card_pdf = client.get('/api/v1/member/card.pdf', headers=member_headers)
        assert card_pdf.status_code == 200
        assert card_pdf.content.startswith(b'%PDF')

        # 9. QR / Public Membership Verification for PGD-TEST-0001
        verify_res = client.get('/api/v1/public/verify/PGD-TEST-0001')
        assert verify_res.status_code == 200, verify_res.text
        v_data = verify_res.json()
        assert v_data['verified'] is True
        assert v_data['membership_id'] == 'PGD-TEST-0001'
        assert v_data['name_en'] == 'TEST MEMBER'

        # 10. Certificate issuance & verification
        admin_headers = _login(client, 'admin@example.org')
        from datetime import datetime, timedelta
        new_evt = client.post(
            '/api/v1/admin/events',
            headers=admin_headers,
            json={
                'title_bn': 'পিজিডি টেস্ট কারিগরি কর্মশালা',
                'title_en': 'PGD-TEST-0001 Verification Workshop',
                'event_date': (datetime.utcnow() + timedelta(days=3)).isoformat(),
                'location_bn': 'ঢাকা',
                'registration_enabled': True,
                'is_published': True,
            },
        )
        assert new_evt.status_code == 200, new_evt.text
        evt_id = new_evt.json()['id']

        member_headers = _login(client, test_email)
        evt_reg = client.post(
            f'/api/v1/events/{evt_id}/registrations',
            headers=member_headers,
            json={'name': 'TEST MEMBER', 'email': test_email, 'phone': '01799000001'},
        )
        assert evt_reg.status_code == 200, evt_reg.text
        reg_id = evt_reg.json()['id']

        admin_headers = _login(client, 'admin@example.org')
        checkin = client.post(f'/api/v1/admin/event-registrations/{reg_id}/check-in', headers=admin_headers)
        assert checkin.status_code == 200

        cert_issue = client.post(f'/api/v1/certificates/event-registrations/{reg_id}', headers=admin_headers)
        assert cert_issue.status_code == 200, cert_issue.text
        cert_token = cert_issue.json()['verification_token']

        cert_verify = client.get(f'/api/v1/certificates/verify/{cert_token}')
        assert cert_verify.status_code == 200
        assert cert_verify.json()['verified'] is True

        # 11. Notification verification (approval + payment receipt notifications recorded)
        member_headers = _login(client, test_email)
        notifs = client.get('/api/v1/member/notifications', headers=member_headers)
        assert notifs.status_code == 200
        notif_items = notifs.json()
        assert len(notif_items) >= 2




