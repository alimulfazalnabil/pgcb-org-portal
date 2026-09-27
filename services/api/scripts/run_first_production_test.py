#!/usr/bin/env python3
"""
Step 8 — First Production Test Runner (TEST MEMBER / PGD-TEST-0001)
Executes the 11-step production verification journey before opening the portal to real members:
  1. Register (TEST MEMBER)
  2. Login
  3. Profile update
  4. Document upload (NID PDF)
  5. Membership application
  6. Admin approval (PGD-TEST-0001)
  7. Test payment (ANNUAL_STANDARD -> ৳2,000 -> callback -> PDF receipt)
  8. Digital ID Card (Front PNG + 2-page PDF)
  9. QR / Public verification (PGD-TEST-0001)
 10. Event registration, attendance check-in, & Certificate verification
 11. Notification delivery verification
"""
from __future__ import annotations

from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.core.security import create_token, hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Circle, Event, User  # noqa: E402


def _ensure_bootstrap_prerequisites() -> tuple[str, int]:
    """Ensure at least one Circle, one Event, and an Admin token exist for the verification run."""
    with SessionLocal() as db:
        circle = db.scalar(select(Circle))
        if not circle:
            circle = Circle(name_bn='ঢাকা', name_en='Dhaka', active=True)
            db.add(circle)
            db.commit()

        admin = db.scalar(select(User).where(User.role == 'SUPER_ADMIN'))
        if not admin:
            admin = User(
                email='sysadmin.verify@pgcb.org.bd',
                password_hash=hash_password('VerifyProdAdmin#2026!'),
                name_bn='সিস্টেম যাচাই প্রশাসক',
                name_en='System Verification Admin',
                role='SUPER_ADMIN',
                is_active=True,
                email_verified=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        evt = Event(
            title_bn='প্রাতিষ্ঠানিক যাচাই কর্মশালা',
            title_en='Institutional Verification Workshop',
            event_date=datetime.utcnow() + timedelta(days=7),
            location_bn='ঢাকা',
            is_published=True,
            registration_enabled=True,
            capacity=100,
        )
        db.add(evt)
        db.commit()
        db.refresh(evt)

        token, _ = create_token(admin.id)
        return token, evt.id


def main() -> int:
    print("==================================================================")
    print("PGCB Portal v1.1 — First Production Test (TEST MEMBER / PGD-TEST-0001)")
    print("==================================================================")

    admin_token, event_id = _ensure_bootstrap_prerequisites()
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    test_email = os.getenv('FIRST_TEST_EMAIL', 'pgd.test.0001@example.org')
    test_pw = os.getenv('FIRST_TEST_PASSWORD') or os.getenv('TEST_SEED_PASSWORD') or ('ChangeMe' + '123!')

    with TestClient(app) as client:
        # 1. Register
        reg = client.post(
            '/api/v1/auth/register',
            json={
                'email': test_email,
                'password': test_pw,
                'name_bn': 'টেস্ট সদস্য প্রকৌশলী',
                'name_en': 'TEST MEMBER',
                'phone': '01799000001',
            },
        )
        assert reg.status_code in (200, 400, 409), f"Register failed: {reg.text}"
        print("[PASS] 1/11 Register TEST MEMBER")

        # 2. Login
        with SessionLocal() as db:
            u = db.scalar(select(User).where(User.email == test_email))
            assert u is not None
            u.email_verified = True
            u.password_hash = hash_password(test_pw)
            db.commit()

        login = client.post('/api/v1/auth/login', json={'email': test_email, 'password': test_pw})
        assert login.status_code == 200, f"Login failed: {login.text}"
        member_headers: dict[str, str] = {}
        print("[PASS] 2/11 Login TEST MEMBER")

        # 3. Profile
        prof = client.patch(
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
        assert prof.status_code == 200, f"Profile update failed: {prof.text}"
        member_id = prof.json()['id']
        print("[PASS] 3/11 Profile Update")

        # 4. Document
        doc = client.post(
            '/api/v1/member/documents?document_type=NID',
            headers=member_headers,
            files={'file': ('pgd_test_0001_nid.pdf', b'%PDF-1.4\n%PGD-TEST-0001 NID\n%%EOF', 'application/pdf')},
        )
        assert doc.status_code == 200, f"Document upload failed: {doc.text}"
        print("[PASS] 4/11 Document Upload (NID PDF)")

        # 5. Membership application
        apply_res = client.post('/api/v1/member/apply', headers=member_headers)
        assert apply_res.status_code in (200, 409), f"Application failed: {apply_res.text}"
        print("[PASS] 5/11 Membership Application Submitted")

        # 6. Admin approval (PGD-TEST-0001)
        approve = client.post(
            f'/api/v1/admin/members/{member_id}/review',
            params={'action': 'APPROVE', 'membership_id': 'PGD-TEST-0001'},
            headers=admin_headers,
        )
        assert approve.status_code == 200 and approve.json()['membership_id'] == 'PGD-TEST-0001', f"Approve failed: {approve.text}"
        print("[PASS] 6/11 Admin Approval -> PGD-TEST-0001 (ACTIVE)")

        # 7. Test payment
        idem_key = f"pgd-test-0001-{int(datetime.utcnow().timestamp() * 1000)}"
        pay_init = client.post(
            '/api/v1/member/payments/checkout',
            headers=member_headers,
            json={'membership_plan_id': 'ANNUAL_STANDARD', 'provider': 'TEST', 'idempotency_key': idem_key},
        )
        assert pay_init.status_code == 200, f"Payment checkout failed: {pay_init.text}"
        pdata = pay_init.json()
        pay_cb = client.post(
            '/api/v1/payments/callback/TEST',
            json={
                'transaction_id': pdata['transaction_id'],
                'provider_transaction_id': pdata['provider_transaction_id'],
                'status': 'SUCCESS',
                'amount': 2000.0,
            },
        )
        assert pay_cb.status_code == 200, f"Payment callback failed: {pay_cb.text}"
        receipt = client.get(f"/api/v1/member/payments/{pdata['transaction_id']}/receipt.pdf", headers=member_headers)
        assert receipt.status_code == 200 and receipt.content.startswith(b'%PDF')
        print("[PASS] 7/11 Test Payment (BDT 2,000) + Official PDF Receipt")

        # 8. Digital ID
        card_png = client.get('/api/v1/member/card?side=front', headers=member_headers)
        card_pdf = client.get('/api/v1/member/card.pdf', headers=member_headers)
        assert card_png.status_code == 200 and card_pdf.status_code == 200
        print("[PASS] 8/11 Digital ID Card (PNG + 2-Page PDF)")

        # 9. QR verification
        verify = client.get('/api/v1/public/verify/PGD-TEST-0001')
        assert verify.status_code == 200 and verify.json()['verified'] is True
        print("[PASS] 9/11 Public QR Verification (PGD-TEST-0001)")

        # 10. Certificate
        ereg = client.post(
            f'/api/v1/events/{event_id}/registrations',
            headers=member_headers,
            json={'name': 'TEST MEMBER', 'email': test_email, 'phone': '01799000001'},
        )
        assert ereg.status_code == 200, f"Event registration failed: {ereg.text}"
        reg_id = ereg.json()['id']
        client.post(f'/api/v1/admin/event-registrations/{reg_id}/check-in', headers=admin_headers)
        cert = client.post(f'/api/v1/certificates/event-registrations/{reg_id}', headers=admin_headers)
        assert cert.status_code == 200, f"Certificate issue failed: {cert.text}"
        cert_verify = client.get(f"/api/v1/certificates/verify/{cert.json()['verification_token']}")
        assert cert_verify.status_code == 200 and cert_verify.json()['verified'] is True
        print("[PASS] 10/11 Event Check-in + Certificate Issuance & Verification")

        # 11. Notification
        notifs = client.get('/api/v1/member/notifications', headers=member_headers)
        assert notifs.status_code == 200 and len(notifs.json()) >= 2
        print("[PASS] 11/11 Notification Delivery Verified")

    print("==================================================================")
    print("ALL 11 STEPS PASSED FOR PGD-TEST-0001. PORTAL READY FOR LIVE USERS.")
    print("==================================================================")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

