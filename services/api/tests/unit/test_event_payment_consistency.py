from __future__ import annotations

from datetime import datetime, timedelta
import uuid
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models.core import Event, EventRegistration, Member, User, PaymentTransaction as CorePaymentTransaction
from app.models.payments import PaymentStatus
from app.routers.payments import admin_reconcile_payment
from app.services.event_service import EventService
from app.services.receipt_service import confirm_event_registration_payment

client = TestClient(app)


def _setup_test_environment(db, fee_amount: int = 1000) -> tuple[User, Member, User, Event]:
    """Helper to create admin user, member user, member profile, and a paid event."""
    uid = uuid.uuid4().hex[:8]
    admin = User(
        email=f"admin_eventpay_{uid}@pgcb.org.bd",
        password_hash=hash_password("AdminPass123!"),
        name_en="Engr. Event Admin",
        name_bn="প্রকৌশলী ইভেন্ট অ্যাডমিন",
        role="SUPER_ADMIN",
        is_active=True,
        email_verified=True,
    )
    user = User(
        email=f"member_eventpay_{uid}@pgcb.org.bd",
        password_hash=hash_password("MemberPass123!"),
        name_en="Engr. Attendee",
        name_bn="প্রকৌশলী অংশগ্রহণকারী",
        role="MEMBER",
        is_active=True,
        email_verified=True,
    )
    db.add_all([admin, user])
    db.commit()
    db.refresh(admin)
    db.refresh(user)

    member = Member(
        user_id=user.id,
        membership_id=f"PGCB-PAY-{uid.upper()[:6]}",
        membership_type="Professional",
        status="ACTIVE",
        issue_date=datetime.utcnow() - timedelta(days=50),
        validity_date=datetime.utcnow() + timedelta(days=315),
    )
    event = Event(
        title_bn=f"পেমেন্ট কনসিস্টেন্সি ইভেন্ট {uid}",
        title_en="Payment Consistency Event",
        event_date=datetime.utcnow() + timedelta(days=7),
        capacity=50,
        fee_amount=fee_amount,
        registration_enabled=True,
        is_published=True,
    )
    db.add_all([member, event])
    db.commit()
    db.refresh(member)
    db.refresh(event)
    return admin, member, user, event


def test_payment_verification_confirms_registration_and_enables_checkin():
    """
    1. Verifies that before payment, check-in is rejected with HTTP 409.
       Once payment succeeds, registration transitions from REGISTERED to CONFIRMED,
       payment_status becomes PAID, and check-in successfully marks attendee ATTENDED.
    """
    with SessionLocal() as db:
        admin, member, user, event = _setup_test_environment(db, fee_amount=1000)

        # Create paid event registration with initial REGISTERED and REQUIRED status
        reg = EventRegistration(
            event_id=event.id,
            user_id=user.id,
            member_id=member.id,
            name=user.name_bn,
            email=user.email,
            ticket_code=f"TKT-PAY-{uuid.uuid4().hex[:8].upper()}",
            registration_status="REGISTERED",
            payment_status="REQUIRED",
            attendance_status="NOT_CHECKED_IN",
            registered_at=datetime.utcnow(),
        )
        db.add(reg)
        db.commit()
        db.refresh(reg)

        # Before payment: check-in MUST fail
        with pytest.raises(HTTPException) as exc_info:
            EventService.check_in_attendee(db, event.id, reg.ticket_code, admin)
        assert exc_info.value.status_code == 409
        assert "Payment must be completed before check-in" in exc_info.value.detail

        # Create pending payment transaction linked to registration
        tx = CorePaymentTransaction(
            user_id=user.id,
            member_id=member.id,
            event_registration_id=reg.id,
            purpose="EVENT",
            amount=1000,
            currency="BDT",
            provider="BKASH",
            transaction_ref=f"TRX-{uuid.uuid4().hex[:10].upper()}",
            status="PENDING",
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)

        # Payment succeeds
        tx.status = "PAID"
        tx.provider_transaction_id = f"BKASH-{tx.transaction_ref}"
        confirmed_reg = confirm_event_registration_payment(db, tx)
        db.commit()
        db.refresh(reg)

        assert confirmed_reg is not None
        assert reg.payment_status == "PAID"
        assert reg.registration_status == "CONFIRMED"

        # Check-in MUST now succeed
        result = EventService.check_in_attendee(db, event.id, reg.ticket_code, admin)
        assert result["ok"] is True
        assert result["attendance_status"] == "ATTENDED"
        db.refresh(reg)
        assert reg.attendance_status == "ATTENDED"
        assert reg.checked_in_at is not None


def test_failed_or_unverified_payment_does_not_confirm_or_allow_checkin():
    """
    2. Verifies that when a payment fails, registration is NOT confirmed,
       payment_status is NOT marked PAID, and check-in remains blocked.
    """
    with SessionLocal() as db:
        admin, member, user, event = _setup_test_environment(db, fee_amount=500)

        reg = EventRegistration(
            event_id=event.id,
            user_id=user.id,
            member_id=member.id,
            name=user.name_bn,
            email=user.email,
            ticket_code=f"TKT-FAIL-{uuid.uuid4().hex[:8].upper()}",
            registration_status="REGISTERED",
            payment_status="REQUIRED",
            attendance_status="NOT_CHECKED_IN",
            registered_at=datetime.utcnow(),
        )
        db.add(reg)
        db.commit()
        db.refresh(reg)

        tx = CorePaymentTransaction(
            user_id=user.id,
            member_id=member.id,
            event_registration_id=reg.id,
            purpose="EVENT",
            amount=500,
            currency="BDT",
            provider="BKASH",
            transaction_ref=f"TRX-FAIL-{uuid.uuid4().hex[:8].upper()}",
            status="FAILED",
        )
        db.add(tx)
        db.commit()

        # confirm_event_registration_payment defensively ignores FAILED transactions
        res = confirm_event_registration_payment(db, tx)
        db.commit()
        db.refresh(reg)

        assert res is None
        assert reg.payment_status != "PAID"
        assert reg.registration_status == "REGISTERED"

        # Check-in still blocked
        with pytest.raises(HTTPException) as exc_info:
            EventService.check_in_attendee(db, event.id, reg.ticket_code, admin)
        assert exc_info.value.status_code == 409
        assert "Payment must be completed before check-in" in exc_info.value.detail


def test_duplicate_payment_callback_idempotency():
    """
    3. Verifies that duplicate payment callbacks / replays do not duplicate side-effects
       and maintain consistent PAID and CONFIRMED states.
    """
    with SessionLocal() as db:
        admin, member, user, event = _setup_test_environment(db, fee_amount=750)

        reg = EventRegistration(
            event_id=event.id,
            user_id=user.id,
            member_id=member.id,
            name=user.name_bn,
            email=user.email,
            ticket_code=f"TKT-IDEM-{uuid.uuid4().hex[:8].upper()}",
            registration_status="REGISTERED",
            payment_status="REQUIRED",
            attendance_status="NOT_CHECKED_IN",
            registered_at=datetime.utcnow(),
        )
        db.add(reg)
        db.commit()

        tx = CorePaymentTransaction(
            user_id=user.id,
            member_id=member.id,
            event_registration_id=reg.id,
            purpose="EVENT",
            amount=750,
            currency="BDT",
            provider="BKASH",
            transaction_ref=f"TRX-IDEM-{uuid.uuid4().hex[:8].upper()}",
            status="PAID",
        )
        db.add(tx)
        db.commit()

        # First confirmation
        res1 = confirm_event_registration_payment(db, tx)
        db.commit()
        db.refresh(reg)
        assert res1 is not None
        assert reg.payment_status == "PAID"
        assert reg.registration_status == "CONFIRMED"

        # Duplicate replay invocation
        res2 = confirm_event_registration_payment(db, tx)
        db.commit()
        db.refresh(reg)
        assert res2 is not None
        assert reg.payment_status == "PAID"
        assert reg.registration_status == "CONFIRMED"


def test_non_event_payment_does_not_alter_registrations():
    """
    4. Verifies that transactions without an event_registration_id (e.g. membership fees)
       safely return None and do not affect unrelated registrations.
    """
    with SessionLocal() as db:
        admin, member, user, event = _setup_test_environment(db, fee_amount=1000)

        unrelated_reg = EventRegistration(
            event_id=event.id,
            user_id=user.id,
            member_id=member.id,
            name=user.name_bn,
            email=user.email,
            ticket_code=f"TKT-UNRELATED-{uuid.uuid4().hex[:8].upper()}",
            registration_status="REGISTERED",
            payment_status="REQUIRED",
            attendance_status="NOT_CHECKED_IN",
            registered_at=datetime.utcnow(),
        )
        db.add(unrelated_reg)
        db.commit()

        mem_tx = CorePaymentTransaction(
            user_id=user.id,
            member_id=member.id,
            event_registration_id=None,
            purpose="MEMBERSHIP",
            amount=2000,
            currency="BDT",
            provider="BKASH",
            status="PAID",
        )
        db.add(mem_tx)
        db.commit()

        res = confirm_event_registration_payment(db, mem_tx)
        db.commit()
        db.refresh(unrelated_reg)

        assert res is None
        assert unrelated_reg.payment_status == "REQUIRED"
        assert unrelated_reg.registration_status == "REGISTERED"


def test_waitlisted_and_cancelled_registrations_preserve_status_on_payment():
    """
    5. Verifies that paying for a WAITLISTED or CANCELLED registration marks
       payment_status as PAID, but leaves registration_status intact.
       In both cases, check_in_attendee still rejects entry with HTTP 409.
    """
    with SessionLocal() as db:
        admin, member, user, event = _setup_test_environment(db, fee_amount=500)

        # 5A: WAITLISTED registration
        reg_waitlisted = EventRegistration(
            event_id=event.id,
            user_id=user.id,
            member_id=member.id,
            name=user.name_bn,
            email=user.email,
            ticket_code=f"TKT-WL-{uuid.uuid4().hex[:8].upper()}",
            registration_status="WAITLISTED",
            payment_status="REQUIRED",
            attendance_status="NOT_CHECKED_IN",
            waitlist_position=1,
            registered_at=datetime.utcnow(),
        )
        db.add(reg_waitlisted)
        db.commit()

        tx_wl = CorePaymentTransaction(
            user_id=user.id,
            member_id=member.id,
            event_registration_id=reg_waitlisted.id,
            purpose="EVENT",
            amount=500,
            currency="BDT",
            status="PAID",
        )
        db.add(tx_wl)
        db.commit()

        confirm_event_registration_payment(db, tx_wl)
        db.commit()
        db.refresh(reg_waitlisted)

        assert reg_waitlisted.payment_status == "PAID"
        assert reg_waitlisted.registration_status == "WAITLISTED"  # Preserved!

        with pytest.raises(HTTPException) as exc_wl:
            EventService.check_in_attendee(db, event.id, reg_waitlisted.ticket_code, admin)
        assert exc_wl.value.status_code == 409
        assert "Attendee is on the waitlist" in exc_wl.value.detail

        # 5B: CANCELLED registration
        reg_cancelled = EventRegistration(
            event_id=event.id,
            user_id=user.id,
            member_id=member.id,
            name=user.name_bn,
            email=f"cancelled_{user.email}",
            ticket_code=f"TKT-CN-{uuid.uuid4().hex[:8].upper()}",
            registration_status="CANCELLED",
            payment_status="REQUIRED",
            attendance_status="NOT_CHECKED_IN",
            registered_at=datetime.utcnow(),
        )
        db.add(reg_cancelled)
        db.commit()

        tx_cn = CorePaymentTransaction(
            user_id=user.id,
            member_id=member.id,
            event_registration_id=reg_cancelled.id,
            purpose="EVENT",
            amount=500,
            currency="BDT",
            status="PAID",
        )
        db.add(tx_cn)
        db.commit()

        confirm_event_registration_payment(db, tx_cn)
        db.commit()
        db.refresh(reg_cancelled)

        assert reg_cancelled.payment_status == "PAID"
        assert reg_cancelled.registration_status == "CANCELLED"  # Preserved!

        with pytest.raises(HTTPException) as exc_cn:
            EventService.check_in_attendee(db, event.id, reg_cancelled.ticket_code, admin)
        assert exc_cn.value.status_code == 409
        assert "This registration has been cancelled" in exc_cn.value.detail


def test_admin_reconcile_payment_confirms_event_registration():
    """
    6. Verifies that admin manual payment reconciliation updates
       EventRegistration.payment_status to PAID and registration_status to CONFIRMED.
    """
    with SessionLocal() as db:
        admin, member, user, event = _setup_test_environment(db, fee_amount=1200)

        reg = EventRegistration(
            event_id=event.id,
            user_id=user.id,
            member_id=member.id,
            name=user.name_bn,
            email=user.email,
            ticket_code=f"TKT-REC-{uuid.uuid4().hex[:8].upper()}",
            registration_status="REGISTERED",
            payment_status="REQUIRED",
            attendance_status="NOT_CHECKED_IN",
            registered_at=datetime.utcnow(),
        )
        db.add(reg)
        db.commit()

        tx = CorePaymentTransaction(
            user_id=user.id,
            member_id=member.id,
            event_registration_id=reg.id,
            purpose="EVENT",
            amount=1200,
            currency="BDT",
            provider="MANUAL",
            status="PENDING",
        )
        db.add(tx)
        db.commit()
        reg_id = reg.id
        event_id = event.id
        tx_id = tx.id
        admin_id = admin.id
        admin_role = admin.role

    token = create_access_token(admin_id, roles=[admin_role])
    resp = client.post(
        f"/api/v1/admin/payments/{tx_id}/reconcile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "provider_transaction_id": f"BANK-REC-{uuid.uuid4().hex[:8].upper()}",
            "method": "MANUAL",
            "note": "Reconciled by finance chair",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    with SessionLocal() as db:
        reg_after = db.get(EventRegistration, reg_id)
        assert reg_after.payment_status == "PAID"
        assert reg_after.registration_status == "CONFIRMED"

        # Check-in succeeds
        admin_refreshed = db.get(User, admin_id)
        chk = EventService.check_in_attendee(db, event_id, reg_after.ticket_code, admin_refreshed)
        assert chk["ok"] is True
        assert chk["attendance_status"] == "ATTENDED"


def test_sandbox_simulation_confirms_event_registration():
    """
    7. Verifies end-to-end sandbox simulation updates EventRegistration
       to PAID and CONFIRMED, and idempotency protects against multiple simulations.
    """
    with SessionLocal() as db:
        admin, member, user, event = _setup_test_environment(db, fee_amount=800)

        reg = EventRegistration(
            event_id=event.id,
            user_id=user.id,
            member_id=member.id,
            name=user.name_bn,
            email=user.email,
            ticket_code=f"TKT-SIM-{uuid.uuid4().hex[:8].upper()}",
            registration_status="REGISTERED",
            payment_status="REQUIRED",
            attendance_status="NOT_CHECKED_IN",
            registered_at=datetime.utcnow(),
        )
        db.add(reg)
        db.commit()

        tx = CorePaymentTransaction(
            user_id=user.id,
            member_id=member.id,
            event_registration_id=reg.id,
            purpose="EVENT",
            amount=800,
            currency="BDT",
            provider="BKASH",
            status="PENDING",
        )
        db.add(tx)
        db.commit()
        reg_id = reg.id
        tx_id = tx.id
        user_id = user.id
        user_role = user.role

    user_token = create_access_token(user_id, roles=[user_role])
    headers = {"Authorization": f"Bearer {user_token}"}

    # Simulate sandbox webhook
    sim_resp = client.post(
        "/api/v1/payments/sandbox/simulate",
        headers=headers,
        json={"payment_id": tx_id},
    )
    assert sim_resp.status_code == 200
    assert sim_resp.json()["status"] == "success"
    assert sim_resp.json()["payment_status"] == "PAID"

    with SessionLocal() as db:
        reg_after = db.get(EventRegistration, reg_id)
        assert reg_after.payment_status == "PAID"
        assert reg_after.registration_status == "CONFIRMED"

    # Replay simulation
    replay_resp = client.post(
        "/api/v1/payments/sandbox/simulate",
        headers=headers,
        json={"payment_id": tx_id},
    )
    assert replay_resp.status_code == 200
    assert replay_resp.json()["idempotent_replay"] is True

    with SessionLocal() as db:
        reg_after2 = db.get(EventRegistration, reg_id)
        assert reg_after2.payment_status == "PAID"
        assert reg_after2.registration_status == "CONFIRMED"


def test_missing_and_none_payment_status_rejected_safely():
    """
    8. Verifies that transactions with missing status, None, or empty/whitespace strings
       are safely rejected by confirm_event_registration_payment() without modifying the registration.
    """
    with SessionLocal() as db:
        admin, member, user, event = _setup_test_environment(db, fee_amount=500)

        reg = EventRegistration(
            event_id=event.id,
            user_id=user.id,
            member_id=member.id,
            name=user.name_bn,
            email=f"guard_{user.email}",
            ticket_code=f"TKT-GUARD-{uuid.uuid4().hex[:8].upper()}",
            registration_status="REGISTERED",
            payment_status="REQUIRED",
            attendance_status="NOT_CHECKED_IN",
            registered_at=datetime.utcnow(),
        )
        db.add(reg)
        db.commit()
        reg_id = reg.id
        event_id = event.id

        # Case A: Object with completely missing 'status' attribute
        class MissingStatusPayment:
            event_registration_id = reg_id

        res_missing = confirm_event_registration_payment(db, MissingStatusPayment())
        assert res_missing is None

        # Case B: Object with status = None
        class NoneStatusPayment:
            event_registration_id = reg_id
            status = None

        res_none = confirm_event_registration_payment(db, NoneStatusPayment())
        assert res_none is None

        # Case C: Object with empty or whitespace status
        class WhitespaceStatusPayment:
            event_registration_id = reg_id
            status = "   "

        res_ws = confirm_event_registration_payment(db, WhitespaceStatusPayment())
        assert res_ws is None

        # Case D: Real CorePaymentTransaction model instance with status set to None
        tx = CorePaymentTransaction(
            user_id=user.id,
            member_id=member.id,
            event_registration_id=reg_id,
            purpose="EVENT",
            amount=500,
            currency="BDT",
        )
        tx.status = None

        res_tx_none = confirm_event_registration_payment(db, tx)
        assert res_tx_none is None

        # Verify registration state remains untouched across all guards
        db.commit()
        reg_check = db.get(EventRegistration, reg_id)
        assert reg_check.payment_status == "REQUIRED"
        assert reg_check.registration_status == "REGISTERED"

        # Check-in remains rejected
        with pytest.raises(HTTPException) as exc_info:
            EventService.check_in_attendee(db, event_id, reg_check.ticket_code, admin)
        assert exc_info.value.status_code == 409
        assert "Payment must be completed before check-in" in exc_info.value.detail


def test_enum_and_case_insensitive_status_accepted():
    """
    9. Verifies that enum values (PaymentStatus.PAID) and case-insensitive strings
       ('paid', 'SUCCESS', 'completed') safely confirm event registrations.
    """
    with SessionLocal() as db:
        admin, member, user, event = _setup_test_environment(db, fee_amount=500)

        # 9A: PaymentStatus Enum
        reg_enum = EventRegistration(
            event_id=event.id,
            user_id=user.id,
            member_id=member.id,
            name=user.name_bn,
            email=f"enum_{user.email}",
            ticket_code=f"TKT-ENUM-{uuid.uuid4().hex[:8].upper()}",
            registration_status="REGISTERED",
            payment_status="REQUIRED",
            attendance_status="NOT_CHECKED_IN",
            registered_at=datetime.utcnow(),
        )
        db.add(reg_enum)
        db.commit()

        class EnumPayment:
            event_registration_id = reg_enum.id
            status = PaymentStatus.PAID

        res_enum = confirm_event_registration_payment(db, EnumPayment())
        assert res_enum is not None
        assert reg_enum.payment_status == "PAID"
        assert reg_enum.registration_status == "CONFIRMED"

        # 9B: Lowercase string 'paid'
        reg_str = EventRegistration(
            event_id=event.id,
            user_id=user.id,
            member_id=member.id,
            name=user.name_bn,
            email=f"str_{user.email}",
            ticket_code=f"TKT-STR-{uuid.uuid4().hex[:8].upper()}",
            registration_status="REGISTERED",
            payment_status="REQUIRED",
            attendance_status="NOT_CHECKED_IN",
            registered_at=datetime.utcnow(),
        )
        db.add(reg_str)
        db.commit()

        class LowercasePayment:
            event_registration_id = reg_str.id
            status = "paid"

        res_str = confirm_event_registration_payment(db, LowercasePayment())
        assert res_str is not None
        assert reg_str.payment_status == "PAID"
        assert reg_str.registration_status == "CONFIRMED"
