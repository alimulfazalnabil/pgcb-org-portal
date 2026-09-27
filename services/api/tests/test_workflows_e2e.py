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
