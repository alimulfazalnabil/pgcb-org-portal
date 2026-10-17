from __future__ import annotations

import concurrent.futures
from datetime import datetime
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import select, func

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Event, EventAttendance, EventRegistration, Member, User
from app.services.event_service import EventService


def _setup_test_event_and_admin(db):
    admin = db.scalar(select(User).where(User.email == 'admin@example.org'))
    if not admin:
        admin = User(
            email=f"admin_test_{uuid.uuid4().hex[:8]}@example.org",
            password_hash=hash_password("Pass123!"),
            name_bn="অ্যাডমিন",
            role="SUPER_ADMIN",
            is_active=True,
            email_verified=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    event = Event(
        title_bn=f"কনকারেন্সি টেস্ট ইভেন্ট {uuid.uuid4().hex[:6]}",
        title_en="Concurrency Test Event",
        event_date=datetime.utcnow(),
        location_bn="প্রধান কার্যালয়",
        capacity=100,
        fee_amount=0,
        registration_enabled=True,
        is_published=True,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return admin, event


def test_first_valid_checkin_succeeds():
    """1. First valid check-in succeeds and creates exactly one attendance record."""
    with SessionLocal() as db:
        admin, event = _setup_test_event_and_admin(db)
        participant = User(
            email=f"part_valid_{uuid.uuid4().hex[:8]}@example.org",
            password_hash=hash_password("Pass123!"),
            name_bn="বৈধ অংশগ্রহণকারী",
            role="MEMBER",
            is_active=True,
            email_verified=True,
        )
        db.add(participant)
        db.commit()
        db.refresh(participant)

        reg = EventService.register_for_event(
            db=db,
            event_id=event.id,
            user=participant,
            data={"ticket_count": 1},
        )
        ticket_code = reg.ticket_code

        res = EventService.check_in_attendee(
            db=db,
            event_id=event.id,
            token_or_code=ticket_code,
            admin_user=admin,
            method="QR",
        )
        assert res["ok"] is True
        assert res["attendance_status"] == "ATTENDED"
        assert res["ticket_code"] == ticket_code

        # Verify attendance record in database
        att_count = db.scalar(
            select(func.count(EventAttendance.id)).where(EventAttendance.registration_id == reg.id)
        )
        assert att_count == 1


def test_repeated_checkin_returns_http_409():
    """2. Repeated check-in attempts return HTTP 409 Conflict with 'ALREADY CHECKED IN'."""
    with SessionLocal() as db:
        admin, event = _setup_test_event_and_admin(db)
        participant = User(
            email=f"part_rep_{uuid.uuid4().hex[:8]}@example.org",
            password_hash=hash_password("Pass123!"),
            name_bn="পুনরাবৃত্তি অংশগ্রহণকারী",
            role="MEMBER",
            is_active=True,
            email_verified=True,
        )
        db.add(participant)
        db.commit()
        db.refresh(participant)

        reg = EventService.register_for_event(
            db=db,
            event_id=event.id,
            user=participant,
            data={"ticket_count": 1},
        )
        ticket_code = reg.ticket_code

        # First check-in succeeds
        res1 = EventService.check_in_attendee(
            db=db,
            event_id=event.id,
            token_or_code=ticket_code,
            admin_user=admin,
        )
        assert res1["ok"] is True

        # Second check-in must raise HTTP 409
        with pytest.raises(HTTPException) as exc_info:
            EventService.check_in_attendee(
                db=db,
                event_id=event.id,
                token_or_code=ticket_code,
                admin_user=admin,
            )
        assert exc_info.value.status_code == 409
        assert "ALREADY CHECKED IN" in exc_info.value.detail


def test_concurrent_member_checkin_produces_exactly_one_success():
    """3. Concurrent requests for the same member registration produce exactly one success and 409s."""
    with SessionLocal() as db:
        admin, event = _setup_test_event_and_admin(db)
        member_obj = db.scalar(select(Member).where(Member.status == "ACTIVE"))
        user = member_obj.user if member_obj else None
        if not user:
            user = User(
                email=f"member_user_{uuid.uuid4().hex[:8]}@example.org",
                password_hash=hash_password("Pass123!"),
                name_bn="সদস্য ইউজার",
                role="MEMBER",
                is_active=True,
                email_verified=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        reg = EventRegistration(
            event_id=event.id,
            user_id=user.id,
            member_id=member_obj.id if member_obj else None,
            name="Concurrent Member Attendee",
            email=user.email,
            ticket_code=f"TKT-CONC-MEM-{uuid.uuid4().hex[:8].upper()}",
            registration_status="CONFIRMED",
            attendance_status="NOT_CHECKED_IN",
            payment_status="PAID",
        )
        db.add(reg)
        db.commit()
        db.refresh(reg)
        ticket_code = reg.ticket_code
        event_id = event.id
        admin_id = admin.id
        reg_id = reg.id

    def worker_checkin():
        with SessionLocal() as worker_db:
            admin_u = worker_db.get(User, admin_id)
            try:
                result = EventService.check_in_attendee(
                    db=worker_db,
                    event_id=event_id,
                    token_or_code=ticket_code,
                    admin_user=admin_u,
                )
                return ("SUCCESS", result)
            except HTTPException as e:
                return ("HTTP_ERROR", e.status_code, e.detail)
            except Exception as e:
                return ("UNEXPECTED_ERROR", str(e))

    num_threads = 5
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker_checkin) for _ in range(num_threads)]
        results = [f.result() for f in futures]

    successes = [r for r in results if r[0] == "SUCCESS"]
    conflicts = [r for r in results if r[0] == "HTTP_ERROR" and r[1] == 409]
    unexpected = [r for r in results if r[0] not in ("SUCCESS", "HTTP_ERROR")]

    assert len(unexpected) == 0, f"Unexpected errors encountered: {unexpected}"
    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}: {results}"
    assert len(conflicts) == num_threads - 1

    # Verify database state has exactly 1 attendance record
    with SessionLocal() as db:
        att_count = db.scalar(
            select(func.count(EventAttendance.id)).where(EventAttendance.registration_id == reg_id)
        )
        assert att_count == 1


def test_concurrent_guest_checkin_produces_exactly_one_success():
    """4. Concurrent requests for a guest registration (member_id=NULL) produce exactly one success."""
    with SessionLocal() as db:
        admin, event = _setup_test_event_and_admin(db)
        reg = EventRegistration(
            event_id=event.id,
            user_id=None,
            member_id=None,  # Guest registration: member_id is NULL
            name="External Guest Attendee",
            email=f"guest_{uuid.uuid4().hex[:8]}@example.com",
            ticket_code=f"TKT-CONC-GUEST-{uuid.uuid4().hex[:8].upper()}",
            registration_status="CONFIRMED",
            attendance_status="NOT_CHECKED_IN",
            payment_status="PAID",
        )
        db.add(reg)
        db.commit()
        db.refresh(reg)
        ticket_code = reg.ticket_code
        event_id = event.id
        admin_id = admin.id
        reg_id = reg.id

    def worker_checkin():
        with SessionLocal() as worker_db:
            admin_u = worker_db.get(User, admin_id)
            try:
                result = EventService.check_in_attendee(
                    db=worker_db,
                    event_id=event_id,
                    token_or_code=ticket_code,
                    admin_user=admin_u,
                )
                return ("SUCCESS", result)
            except HTTPException as e:
                return ("HTTP_ERROR", e.status_code, e.detail)
            except Exception as e:
                return ("UNEXPECTED_ERROR", str(e))

    num_threads = 5
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker_checkin) for _ in range(num_threads)]
        results = [f.result() for f in futures]

    successes = [r for r in results if r[0] == "SUCCESS"]
    conflicts = [r for r in results if r[0] == "HTTP_ERROR" and r[1] == 409]
    unexpected = [r for r in results if r[0] not in ("SUCCESS", "HTTP_ERROR")]

    assert len(unexpected) == 0, f"Unexpected errors encountered: {unexpected}"
    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}: {results}"
    assert len(conflicts) == num_threads - 1

    # Verify database state has exactly 1 attendance record
    with SessionLocal() as db:
        att_count = db.scalar(
            select(func.count(EventAttendance.id)).where(EventAttendance.registration_id == reg_id)
        )
        assert att_count == 1


def test_independent_registrations_checkin_successfully():
    """5. Different registrations can be checked in independently without collision."""
    with SessionLocal() as db:
        admin, event = _setup_test_event_and_admin(db)
        reg_a = EventRegistration(
            event_id=event.id,
            name="Attendee A",
            email=f"attendee_a_{uuid.uuid4().hex[:6]}@example.com",
            ticket_code=f"TKT-IND-A-{uuid.uuid4().hex[:8].upper()}",
            registration_status="CONFIRMED",
            attendance_status="NOT_CHECKED_IN",
            payment_status="PAID",
        )
        reg_b = EventRegistration(
            event_id=event.id,
            name="Attendee B",
            email=f"attendee_b_{uuid.uuid4().hex[:6]}@example.com",
            ticket_code=f"TKT-IND-B-{uuid.uuid4().hex[:8].upper()}",
            registration_status="CONFIRMED",
            attendance_status="NOT_CHECKED_IN",
            payment_status="PAID",
        )
        db.add_all([reg_a, reg_b])
        db.commit()
        db.refresh(reg_a)
        db.refresh(reg_b)

        # Check in A
        res_a = EventService.check_in_attendee(
            db=db,
            event_id=event.id,
            token_or_code=reg_a.ticket_code,
            admin_user=admin,
        )
        assert res_a["ok"] is True
        assert res_a["attendance_status"] == "ATTENDED"

        # Check in B
        res_b = EventService.check_in_attendee(
            db=db,
            event_id=event.id,
            token_or_code=reg_b.ticket_code,
            admin_user=admin,
        )
        assert res_b["ok"] is True
        assert res_b["attendance_status"] == "ATTENDED"

        # Check total attendance records for event
        event_att_count = db.scalar(
            select(func.count(EventAttendance.id)).where(EventAttendance.event_id == event.id)
        )
        assert event_att_count >= 2


def test_failed_checkin_leaves_no_duplicate_or_partial_state():
    """6. Failed check-in leaves no duplicate attendance record or partial transaction state."""
    with SessionLocal() as db:
        admin, event = _setup_test_event_and_admin(db)
        reg = EventRegistration(
            event_id=event.id,
            name="Cancelled Attendee",
            email=f"cancelled_{uuid.uuid4().hex[:6]}@example.com",
            ticket_code=f"TKT-CANCELLED-{uuid.uuid4().hex[:8].upper()}",
            registration_status="CANCELLED",
            attendance_status="NOT_CHECKED_IN",
            payment_status="PAID",
        )
        db.add(reg)
        db.commit()
        db.refresh(reg)

        # Attempt to check in cancelled registration
        with pytest.raises(HTTPException) as exc_info:
            EventService.check_in_attendee(
                db=db,
                event_id=event.id,
                token_or_code=reg.ticket_code,
                admin_user=admin,
            )
        assert exc_info.value.status_code == 409

        # Confirm no EventAttendance record was inserted
        att = db.scalar(
            select(EventAttendance).where(EventAttendance.registration_id == reg.id)
        )
        assert att is None

        # Confirm registration status remains unaffected
        db.refresh(reg)
        assert reg.attendance_status == "NOT_CHECKED_IN"
        assert reg.checked_in_at is None


def test_checkin_status_consistency_and_certificate_compatibility():
    """Verify that attendees with attendance_status 'ATTENDED' or 'CHECKED_IN' are fully recognized by certificates, admin stats, and repeat check-in logic."""
    from unittest.mock import MagicMock
    from app.routers.certificates import create_event_certificate
    from app.routers.admin import _apply_check_in

    with SessionLocal() as db:
        admin, event = _setup_test_event_and_admin(db)
        event.certificate_eligible = True
        db.commit()

        # Case 1: Attendee checked in via check_in_attendee (status='ATTENDED')
        part_attended = User(
            email=f"part_att_{uuid.uuid4().hex[:8]}@example.org",
            password_hash=hash_password("Pass123!"),
            name_bn="উপস্থিত অংশগ্রহণকারী",
            role="MEMBER",
            is_active=True,
            email_verified=True,
        )
        db.add(part_attended)
        db.commit()
        db.refresh(part_attended)

        reg_attended = EventRegistration(
            event_id=event.id,
            user_id=part_attended.id,
            name="Attended Member",
            email=part_attended.email,
            ticket_code=f"TKT-ATT-{uuid.uuid4().hex[:8].upper()}",
            registration_status="CONFIRMED",
            attendance_status="NOT_CHECKED_IN",
            payment_status="PAID",
        )
        db.add(reg_attended)
        db.commit()
        db.refresh(reg_attended)

        # Before check-in: create_event_certificate should raise 409
        with pytest.raises(HTTPException) as exc_info:
            create_event_certificate(registration_id=reg_attended.id, db=db)
        assert exc_info.value.status_code == 409
        assert "must be checked in" in exc_info.value.detail

        # Check in attendee -> status becomes ATTENDED
        res = EventService.check_in_attendee(
            db=db,
            event_id=event.id,
            token_or_code=reg_attended.ticket_code,
            admin_user=admin,
        )
        assert res["ok"] is True
        assert res["attendance_status"] == "ATTENDED"
        db.refresh(reg_attended)
        assert reg_attended.attendance_status == "ATTENDED"

        # Now certificate creation must SUCCEED for ATTENDED status
        cert_res = create_event_certificate(registration_id=reg_attended.id, db=db)
        assert cert_res is not None
        assert "certificate_no" in cert_res

        # Admin stats query counts ATTENDED in checked_in
        checked_in_count = db.scalar(
            select(func.count(EventRegistration.id)).where(
                EventRegistration.event_id == event.id,
                EventRegistration.attendance_status.in_(['CHECKED_IN', 'ATTENDED']),
            )
        )
        assert checked_in_count >= 1

        # Case 2: Attendee with legacy CHECKED_IN status is also accepted by certificate creation
        part_checkedin = User(
            email=f"part_chk_{uuid.uuid4().hex[:8]}@example.org",
            password_hash=hash_password("Pass123!"),
            name_bn="চেকড-ইন অংশগ্রহণকারী",
            role="MEMBER",
            is_active=True,
            email_verified=True,
        )
        db.add(part_checkedin)
        db.commit()
        db.refresh(part_checkedin)

        reg_checkedin = EventRegistration(
            event_id=event.id,
            user_id=part_checkedin.id,
            name="CheckedIn Member",
            email=part_checkedin.email,
            ticket_code=f"TKT-CHK-{uuid.uuid4().hex[:8].upper()}",
            registration_status="CONFIRMED",
            attendance_status="CHECKED_IN",
            payment_status="PAID",
        )
        db.add(reg_checkedin)
        db.commit()
        db.refresh(reg_checkedin)

        cert_res2 = create_event_certificate(registration_id=reg_checkedin.id, db=db)
        assert cert_res2 is not None
        assert "certificate_no" in cert_res2

        # Case 3: _apply_check_in recognizes both CHECKED_IN and ATTENDED as already checked in
        dummy_req = MagicMock()
        dummy_req.client.host = "127.0.0.1"
        dummy_req.headers = {}
        res_chk_repeat = _apply_check_in(db, admin, reg_attended, dummy_req, 'CHECK_IN')
        assert res_chk_repeat['already_checked_in'] is True
        assert res_chk_repeat['attendance_status'] == 'ATTENDED'

        res_chk_repeat2 = _apply_check_in(db, admin, reg_checkedin, dummy_req, 'CHECK_IN')
        assert res_chk_repeat2['already_checked_in'] is True
        assert res_chk_repeat2['attendance_status'] == 'CHECKED_IN'
