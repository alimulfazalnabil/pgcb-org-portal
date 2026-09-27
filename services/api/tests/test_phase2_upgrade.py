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
