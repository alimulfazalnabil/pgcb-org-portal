"""
Comprehensive Automated Test Suite for Phase 6: Member Events & Platform-Wide Notifications.
Covers:
- Event listing and tab filtering (all, upcoming, registered, past)
- Atomic capacity registration, duplicate prevention, and waitlist queueing
- Voluntary cancellation and automatic promotion of waitlisted members
- Digital Event Pass with cryptographic HMAC-SHA256 signatures
- Admin QR / Ticket check-in and duplicate prevention (409 Conflict)
- Automatic Certificate of Participation generation upon qualifying check-in
- Notification feed, unread counters, actionable deep-links, and read-all actions
- Notification settings preference matrix across categories and channels
- AI Assistant event inquiry tools
"""

from __future__ import annotations

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.core import Certificate, Event, EventAttendance, EventRegistration, Member, Notification, User

client = TestClient(app)


def _get_user_and_headers(
    email: str,
    name_bn: str,
    name_en: str,
    role: str = "MEMBER",
    membership_id: str | None = None,
) -> tuple[dict[str, str], User, Member | None]:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                email=email,
                name_bn=name_bn,
                name_en=name_en,
                password_hash="fake_hash",
                role=role,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        member = None
        if membership_id:
            member = db.scalar(select(Member).where(Member.user_id == user.id))
            if not member:
                member = Member(
                    user_id=user.id,
                    membership_id=membership_id,
                    membership_type="GENERAL",
                    status="ACTIVE",
                    designation_en="Sub-Divisional Engineer",
                    designation_bn="উপ-বিভাগীয় প্রকৌশলী",
                )
                db.add(member)
                db.commit()
                db.refresh(member)

        token = create_access_token(user.id, roles=[user.role])
        return {"Authorization": f"Bearer {token}"}, user, member
    finally:
        db.close()


def test_member_events_list_and_tab_filtering():
    headers, user, member = _get_user_and_headers(
        email="test_event_member1@pgcb.org.bd",
        name_bn="প্রকৌশলী তানভীর আহমেদ",
        name_en="Engr. Tanvir Ahmed",
        membership_id="PGCB-MEM-009101",
    )

    # 1. Fetch all events
    res = client.get("/api/v1/member/events?tab=all", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "items" in data
    assert "counts" in data
    assert "categories" in data
    assert data["counts"]["all"] >= 0

    # 2. Fetch upcoming events
    res_upcoming = client.get("/api/v1/member/events?tab=upcoming", headers=headers)
    assert res_upcoming.status_code == 200
    upcoming_data = res_upcoming.json()
    assert upcoming_data["counts"]["upcoming"] >= 0

    # 3. Category filter
    res_cat = client.get("/api/v1/member/events?category=AGM", headers=headers)
    assert res_cat.status_code == 200


def test_event_atomic_registration_and_waitlist_queue():
    db = SessionLocal()
    try:
        # Create an event with strictly 1 seat capacity
        now = datetime.utcnow()
        event = Event(
            title_bn="ন্যাশনাল পাওয়ার গ্রিড সিম্পোজিয়াম ২০২৬",
            title_en="National Power Grid Symposium 2026",
            category="CONFERENCE",
            event_date=now + timedelta(days=15),
            start_date=now + timedelta(days=15),
            capacity=1,
            fee_amount=0,
            fee_currency="BDT",
            venue="ইঞ্জিনিয়ার্স ইনস্টিটিউশন মিলনায়তন",
            is_published=True,
            registration_enabled=True,
            certificate_eligible=True,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        event_id = event.id
    finally:
        db.close()

    headers_m1, user_m1, _ = _get_user_and_headers(
        email="attendee_one@pgcb.org.bd",
        name_bn="সদস্য ১",
        name_en="Member One",
        membership_id="PGCB-MEM-001001",
    )
    headers_m2, user_m2, _ = _get_user_and_headers(
        email="attendee_two@pgcb.org.bd",
        name_bn="সদস্য ২",
        name_en="Member Two",
        membership_id="PGCB-MEM-001002",
    )
    headers_m3, user_m3, _ = _get_user_and_headers(
        email="attendee_three@pgcb.org.bd",
        name_bn="সদস্য ৩",
        name_en="Member Three",
        membership_id="PGCB-MEM-001003",
    )

    # First member registers -> Confirmed (Seat 1 of 1)
    res1 = client.post(f"/api/v1/member/events/{event_id}/register", json={}, headers=headers_m1)
    assert res1.status_code == 200, res1.text
    reg1 = res1.json()["registration"]
    assert reg1["registration_status"] == "CONFIRMED"
    assert reg1["ticket_code"].startswith("TKT-")

    # Second member registers -> Capacity reached -> Placed on Waitlist (Position 1)
    res2 = client.post(f"/api/v1/member/events/{event_id}/register", json={}, headers=headers_m2)
    assert res2.status_code == 200, res2.text
    reg2 = res2.json()["registration"]
    assert reg2["registration_status"] == "WAITLISTED"
    assert reg2["waitlist_position"] == 1

    # Third member registers -> Placed on Waitlist (Position 2)
    res3 = client.post(f"/api/v1/member/events/{event_id}/register", json={}, headers=headers_m3)
    assert res3.status_code == 200, res3.text
    reg3 = res3.json()["registration"]
    assert reg3["registration_status"] == "WAITLISTED"
    assert reg3["waitlist_position"] == 2

    # Duplicate registration attempt should be rejected with 400
    res_dup = client.post(f"/api/v1/member/events/{event_id}/register", json={}, headers=headers_m1)
    assert res_dup.status_code == 400


def test_event_cancellation_and_auto_promotion():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        event = Event(
            title_bn="স্মার্ট গ্রিড টেকনোলজি সেমিনার ২০২৬",
            title_en="Smart Grid Technology Seminar 2026",
            category="SEMINAR",
            event_date=now + timedelta(days=20),
            start_date=now + timedelta(days=20),
            capacity=1,
            fee_amount=0,
            fee_currency="BDT",
            venue="পিজিসিবি কনফারেন্স রুম",
            is_published=True,
            registration_enabled=True,
            certificate_eligible=True,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        event_id = event.id
    finally:
        db.close()

    headers_a, user_a, _ = _get_user_and_headers(
        email="cancel_user_a@pgcb.org.bd",
        name_bn="সদস্য ক",
        name_en="Member A",
        membership_id="PGCB-MEM-002001",
    )
    headers_b, user_b, _ = _get_user_and_headers(
        email="waitlist_user_b@pgcb.org.bd",
        name_bn="সদস্য খ",
        name_en="Member B",
        membership_id="PGCB-MEM-002002",
    )

    # User A registers (CONFIRMED)
    res_a = client.post(f"/api/v1/member/events/{event_id}/register", json={}, headers=headers_a)
    assert res_a.status_code == 200
    assert res_a.json()["registration"]["registration_status"] == "CONFIRMED"

    # User B registers (WAITLISTED #1)
    res_b = client.post(f"/api/v1/member/events/{event_id}/register", json={}, headers=headers_b)
    assert res_b.status_code == 200
    assert res_b.json()["registration"]["registration_status"] == "WAITLISTED"

    # User A cancels their registration
    res_cancel = client.post(
        f"/api/v1/member/events/{event_id}/cancel",
        json={"reason": "অফিশিয়াল সাবস্টেশন ভিজিট"},
        headers=headers_a,
    )
    assert res_cancel.status_code == 200, res_cancel.text
    cancel_data = res_cancel.json()
    assert cancel_data["ok"] is True
    assert cancel_data["promoted_attendee_id"] is not None

    # Verify User B was automatically promoted to CONFIRMED
    db = SessionLocal()
    try:
        reg_b_updated = db.scalar(
            select(EventRegistration).where(
                EventRegistration.event_id == event_id,
                EventRegistration.user_id == user_b.id,
            )
        )
        assert reg_b_updated is not None
        assert reg_b_updated.registration_status == "CONFIRMED"
        assert reg_b_updated.waitlist_position is None

        # Verify notification was sent to promoted User B
        notif = db.scalar(
            select(Notification).where(
                Notification.user_id == user_b.id,
                Notification.notification_type == "EVENT_REGISTRATION",
            ).order_by(Notification.created_at.desc())
        )
        assert notif is not None
        assert "নিবন্ধন নিশ্চিত" in notif.title_bn
        assert f"/member/events/{event_id}/pass" in (notif.data_json or {}).get("action", {}).get("route", "")
    finally:
        db.close()


def test_digital_event_pass_and_signed_qr():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        event = Event(
            title_bn="বার্ষিক প্রকৌশলী সম্মেলন ২০২৬",
            title_en="Annual Engineers Conference 2026",
            category="AGM",
            event_date=now + timedelta(days=10),
            venue="বঙ্গবন্ধু আন্তর্জাতিক সম্মেলন কেন্দ্র (BICC)",
            is_published=True,
            registration_enabled=True,
            certificate_eligible=True,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        event_id = event.id
    finally:
        db.close()

    headers, user, member = _get_user_and_headers(
        email="pass_holder@pgcb.org.bd",
        name_bn="প্রকৌশলী রফিকুল ইসলাম",
        name_en="Engr. Rafiqul Islam",
        membership_id="PGCB-MEM-003001",
    )

    # Register
    res_reg = client.post(f"/api/v1/member/events/{event_id}/register", json={}, headers=headers)
    assert res_reg.status_code == 200

    # Retrieve Digital Event Pass
    res_pass = client.get(f"/api/v1/member/events/{event_id}/pass", headers=headers)
    assert res_pass.status_code == 200, res_pass.text
    pass_info = res_pass.json()["pass"]

    assert pass_info["ticket_code"].startswith("TKT-")
    assert "." in pass_info["qr_token"]  # HMAC signed token
    assert pass_info["qr_image_data_url"].startswith("data:image/png;base64,")
    assert pass_info["registration_status"] == "CONFIRMED"
    assert pass_info["event"]["title_bn"] == event.title_bn
    assert pass_info["attendee"]["membership_id"] == "PGCB-MEM-003001"

    # Test QR image stream endpoint
    res_qr = client.get(f"/api/v1/member/events/{event_id}/qr", headers=headers)
    assert res_qr.status_code == 200
    assert res_qr.headers["content-type"] == "image/png"


def test_admin_checkin_and_automatic_certificate_issuance():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        event = Event(
            title_bn="গ্রিড রিলায়েবিলিটি ট্রেনিং কর্মশালা",
            title_en="Grid Reliability Training Workshop",
            category="TRAINING",
            event_date=now + timedelta(days=5),
            venue="পিজিসিবি ট্রেনিং একাডেমি, রামপুরা",
            is_published=True,
            registration_enabled=True,
            certificate_eligible=True,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        event_id = event.id
    finally:
        db.close()

    # Create Member & Register
    headers_member, user_member, member = _get_user_and_headers(
        email="trainee_attendee@pgcb.org.bd",
        name_bn="প্রকৌশলী ফারহানা রহমান",
        name_en="Engr. Farhana Rahman",
        membership_id="PGCB-MEM-004001",
    )
    res_reg = client.post(f"/api/v1/member/events/{event_id}/register", json={}, headers=headers_member)
    assert res_reg.status_code == 200
    ticket_code = res_reg.json()["registration"]["ticket_code"]

    # Get Pass signed QR token
    res_pass = client.get(f"/api/v1/member/events/{event_id}/pass", headers=headers_member)
    qr_token = res_pass.json()["pass"]["qr_token"]

    # Create Admin User
    headers_admin, user_admin, _ = _get_user_and_headers(
        email="event_admin@pgcb.org.bd",
        name_bn="অ্যাডমিন অফিসার",
        name_en="Admin Officer",
        role="SUPER_ADMIN",
    )

    # 1. Admin scans QR token for check-in
    res_checkin = client.post(
        f"/api/v1/admin/events/{event_id}/check-in",
        json={"qr_token": qr_token, "method": "QR"},
        headers=headers_admin,
    )
    assert res_checkin.status_code == 200, res_checkin.text
    checkin_data = res_checkin.json()
    assert checkin_data["ok"] is True
    assert checkin_data["registration"]["attendance_status"] == "ATTENDED"
    assert checkin_data["certificate"] is not None
    assert checkin_data["certificate"]["certificate_no"].startswith("PGCB-EVT-CERT-")

    # Verify Certificate was persisted in wallet
    db = SessionLocal()
    try:
        cert = db.scalar(
            select(Certificate).where(
                Certificate.member_id == member.id,
                Certificate.certificate_type == "EVENT",
            )
        )
        assert cert is not None
        assert cert.status == "VALID"
        assert event.title_bn in cert.title_bn
    finally:
        db.close()

    # 2. Duplicate Check-in Attempt -> Must be rejected with 409 Conflict
    res_dup_checkin = client.post(
        f"/api/v1/admin/events/{event_id}/check-in",
        json={"qr_token": qr_token, "method": "QR"},
        headers=headers_admin,
    )
    assert res_dup_checkin.status_code == 409
    assert "ALREADY CHECKED IN" in res_dup_checkin.json()["detail"]

    # 3. Check attendance log endpoint
    res_att = client.get(f"/api/v1/admin/events/{event_id}/attendance", headers=headers_admin)
    assert res_att.status_code == 200
    att_data = res_att.json()
    assert att_data["total_checked_in"] == 1
    assert att_data["check_in_rate_percent"] == 100.0


def test_member_notifications_and_settings_matrix():
    headers, user, _ = _get_user_and_headers(
        email="notif_tester@pgcb.org.bd",
        name_bn="নোটিফিকেশন টেস্টার",
        name_en="Notification Tester",
        membership_id="PGCB-MEM-005001",
    )

    # Inject a test notification
    db = SessionLocal()
    try:
        notif = Notification(
            user_id=user.id,
            notification_type="MEMBERSHIP_RENEWAL",
            title_bn="বার্ষিক সদস্যপদ নবায়ন বিজ্ঞপ্তি",
            title_en="Annual Membership Renewal Reminder",
            body_bn="আপনার সদস্যপদের মেয়াদ ৩০ দিনের মধ্যে শেষ হবে।",
            body_en="Your membership will expire in 30 days. Please renew to keep member benefits active.",
            priority="HIGH",
            data_json={"action": {"label": "Renew", "label_bn": "নবায়ন", "route": "/member/membership"}},
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        notif_id = notif.id
    finally:
        db.close()

    # 1. Fetch notification feed
    res_list = client.get("/api/v1/member/notifications?status=all", headers=headers)
    assert res_list.status_code == 200, res_list.text
    data = res_list.json()
    assert data["unread_count"] >= 1
    item = next((n for n in data["items"] if n["id"] == notif_id), None)
    assert item is not None
    assert item["is_read"] is False
    assert item["action"]["route"] == "/member/membership"

    # 2. Mark single notification as read
    res_read = client.post(f"/api/v1/member/notifications/{notif_id}/read", headers=headers)
    assert res_read.status_code == 200
    assert res_read.json()["ok"] is True

    # 3. Mark all read
    res_read_all = client.post("/api/v1/member/notifications/read-all", headers=headers)
    assert res_read_all.status_code == 200
    assert res_read_all.json()["ok"] is True

    # 4. Get notification preference settings matrix
    res_settings = client.get("/api/v1/member/notification-settings", headers=headers)
    assert res_settings.status_code == 200
    settings_data = res_settings.json()
    assert "preferences" in settings_data
    assert "categories" in settings_data

    # 5. Update settings matrix
    new_prefs = {
        "EVENTS": {"in_app": True, "email": True, "sms": True},
        "PAYMENTS": {"in_app": True, "email": True, "sms": False},
    }
    res_patch = client.patch(
        "/api/v1/member/notification-settings",
        json={"preferences": new_prefs},
        headers=headers,
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["ok"] is True
    assert res_patch.json()["preferences"]["EVENTS"]["sms"] is True


def test_ai_assistant_event_tools():
    headers, user, member = _get_user_and_headers(
        email="ai_event_member@pgcb.org.bd",
        name_bn="প্রকৌশলী এআই ইউজার",
        name_en="Engr. AI User",
        membership_id="PGCB-MEM-006001",
    )

    # Ask AI about events
    res_ai_events = client.post(
        "/api/v1/ai/chat",
        json={"message": "আমার registered events কী কী?", "mode": "MEMBER"},
        headers=headers,
    )
    assert res_ai_events.status_code == 200, res_ai_events.text
    ai_events_data = res_ai_events.json()
    ans1 = ai_events_data.get("answer") or ai_events_data.get("answer_bn") or ai_events_data.get("answer_en") or ""
    assert len(ans1) > 0
    assert any(term in ans1 for term in ("ইভেন্ট", "রেজিস্ট্রেশন", "নিবন্ধন", "event", "registered"))

    # Ask AI about event pass
    res_ai_pass = client.post(
        "/api/v1/ai/chat",
        json={"message": "আমার event pass দেখাও", "mode": "MEMBER"},
        headers=headers,
    )
    assert res_ai_pass.status_code == 200, res_ai_pass.text
    ai_pass_data = res_ai_pass.json()
    ans2 = ai_pass_data.get("answer") or ai_pass_data.get("answer_bn") or ai_pass_data.get("answer_en") or ""
    assert len(ans2) > 0
    assert any(term in ans2 for term in ("পাস", "টিকিট", "pass", "ticket", "QR", "কিউআর"))
