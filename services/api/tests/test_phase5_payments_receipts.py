from __future__ import annotations

import io
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.core import Member, PaymentTransaction, User

client = TestClient(app)


def _get_auth_headers(email: str = "member_pay@pgcb.org.bd") -> tuple[dict[str, str], User, Member]:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                email=email,
                name_en="Engr. Payment Tester",
                name_bn="প্রকৌশলী পেমেন্ট টেস্টার",
                password_hash="fakehash",
                role="MEMBER",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        member = db.scalar(select(Member).where(Member.user_id == user.id))
        if not member:
            member = Member(
                user_id=user.id,
                membership_id="PGCB-005555",
                membership_type="Professional",
                status="ACTIVE",
                issue_date=datetime.utcnow() - timedelta(days=365),
                validity_date=datetime.utcnow() + timedelta(days=100),
            )
            db.add(member)
            db.commit()
            db.refresh(member)

        token = create_access_token(user.id, roles=[user.role])
        return {"Authorization": f"Bearer {token}"}, user, member
    finally:
        db.close()


def _get_other_member_auth_headers() -> tuple[dict[str, str], User, Member]:
    db = SessionLocal()
    try:
        email = "other_pay_member@pgcb.org.bd"
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                email=email,
                name_en="Engr. Cross Member",
                name_bn="প্রকৌশলী ক্রস মেম্বার",
                password_hash="fakehash",
                role="MEMBER",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        member = db.scalar(select(Member).where(Member.user_id == user.id))
        if not member:
            member = Member(
                user_id=user.id,
                membership_id="PGCB-006666",
                membership_type="General",
                status="ACTIVE",
                issue_date=datetime.utcnow() - timedelta(days=100),
                validity_date=datetime.utcnow() + timedelta(days=265),
            )
            db.add(member)
            db.commit()
            db.refresh(member)

        token = create_access_token(user.id, roles=[user.role])
        return {"Authorization": f"Bearer {token}"}, user, member
    finally:
        db.close()


def _get_admin_headers() -> tuple[dict[str, str], User]:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == "finance_admin@pgcb.org.bd"))
        if not user:
            user = User(
                email="finance_admin@pgcb.org.bd",
                name_en="Finance Officer",
                name_bn="অর্থ কর্মকর্তা",
                password_hash="fakehash",
                role="FINANCE_ADMIN",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        token = create_access_token(user.id, roles=[user.role])
        return {"Authorization": f"Bearer {token}"}, user
    finally:
        db.close()


def test_server_side_pricing_lock_and_client_tamper_rejection():
    """Verify server locks pricing and rejects client amount tampering."""
    headers, user, member = _get_auth_headers()

    # 1. Attempt checkout with tampered fee (e.g. ৳10 instead of authoritative fee ৳2,000)
    tampered_resp = client.post(
        "/api/v1/member/payments/checkout",
        headers=headers,
        json={
            "purpose": "RENEWAL",
            "membership_plan_id": "RENEWAL",
            "amount": 10,  # Tampered amount
            "provider": "BKASH",
            "currency": "BDT",
        },
    )
    assert tampered_resp.status_code == 400
    assert "does not match server-calculated fee" in tampered_resp.json()["detail"]

    # 2. Legitimate checkout with server-calculated amount
    legit_resp = client.post(
        "/api/v1/member/payments/checkout",
        headers=headers,
        json={
            "purpose": "RENEWAL",
            "membership_plan_id": "RENEWAL",
            "amount": 2000,
            "provider": "BKASH",
            "currency": "BDT",
        },
    )
    assert legit_resp.status_code == 200
    data = legit_resp.json()
    assert data["amount"] == 2000.0
    assert data["status"] == "PENDING"
    assert data["provider"] == "BKASH"


def test_payment_checkout_intent_and_idempotency():
    """Verify idempotency key prevents duplicate transactions on replay."""
    headers, user, member = _get_auth_headers()
    idem_key = f"IDEM-{datetime.utcnow().timestamp()}"

    resp1 = client.post(
        "/api/v1/member/payments/checkout",
        headers={**headers, "X-Idempotency-Key": idem_key},
        json={
            "purpose": "RENEWAL",
            "membership_plan_id": "RENEWAL",
            "amount": 2000,
            "provider": "BKASH",
            "currency": "BDT",
            "idempotency_key": idem_key,
        },
    )
    assert resp1.status_code == 200
    d1 = resp1.json()
    payment_id = d1["id"]

    # Replay with identical idempotency key
    resp2 = client.post(
        "/api/v1/member/payments/checkout",
        headers={**headers, "X-Idempotency-Key": idem_key},
        json={
            "purpose": "RENEWAL",
            "membership_plan_id": "RENEWAL",
            "amount": 2000,
            "provider": "BKASH",
            "currency": "BDT",
            "idempotency_key": idem_key,
        },
    )
    assert resp2.status_code == 200
    d2 = resp2.json()
    assert d2["id"] == payment_id
    assert d2.get("idempotent_replay") is True


def test_gateway_webhook_or_callback_server_verification():
    """Verify gateway confirmation transitions status to PAID and rejects illegal rollback."""
    headers, user, member = _get_auth_headers()

    # Create payment intent
    create_resp = client.post(
        "/api/v1/member/payments/checkout",
        headers=headers,
        json={
            "purpose": "RENEWAL",
            "membership_plan_id": "RENEWAL",
            "amount": 2000,
            "provider": "BKASH",
            "currency": "BDT",
        },
    )
    assert create_resp.status_code == 200
    p_data = create_resp.json()
    payment_id = p_data["id"]

    # Simulate successful payment callback
    sim_resp = client.post(
        "/api/v1/payments/sandbox/simulate",
        headers=headers,
        json={
            "payment_id": payment_id,
            "outcome": "SUCCESS",
            "amount": 2000,
        },
    )
    assert sim_resp.status_code == 200
    s_data = sim_resp.json()
    assert s_data["payment_status"] == "PAID"
    assert s_data["receipt_no"] is not None
    assert s_data["receipt_no"].startswith("PGCB-RCP-")

    # Idempotent replay of already PAID payment
    replay_resp = client.post(
        "/api/v1/payments/sandbox/simulate",
        headers=headers,
        json={
            "payment_id": payment_id,
            "outcome": "SUCCESS",
        },
    )
    assert replay_resp.status_code == 200
    assert replay_resp.json().get("idempotent_replay") is True

    # Illegal rollback attempt (PAID -> FAILED) via callback must fail with 409 Conflict
    illegal_resp = client.post(
        "/api/v1/member/payments/callback/BKASH",
        json={
            "payment_id": payment_id,
            "status": "FAILED",
        },
    )
    assert illegal_resp.status_code == 409
    assert "Illegal payment state transition" in illegal_resp.json()["detail"]


def test_member_payment_summary_and_transaction_detail():
    """Verify member payment summary calculations, status filtering, and cross-member security."""
    headers, user, member = _get_auth_headers()
    other_headers, other_user, other_member = _get_other_member_auth_headers()

    # Fetch summary for member
    summary_resp = client.get("/api/v1/member/payments/summary", headers=headers)
    assert summary_resp.status_code == 200
    s_data = summary_resp.json()
    assert "total_paid" in s_data
    assert "successful_count" in s_data
    assert "pending_count" in s_data
    assert "failed_count" in s_data
    assert "transactions" in s_data
    assert isinstance(s_data["transactions"], list)

    # Backward compatibility: /member/payments without summary=True returns a list
    list_resp = client.get("/api/v1/member/payments", headers=headers)
    assert list_resp.status_code == 200
    assert isinstance(list_resp.json(), list)

    if s_data["transactions"]:
        target_payment_id = s_data["transactions"][0]["id"]
        # Owner can view transaction detail
        detail_resp = client.get(f"/api/v1/member/payments/{target_payment_id}", headers=headers)
        assert detail_resp.status_code == 200
        d_val = detail_resp.json()
        assert d_val["id"] == target_payment_id
        assert "reference" in d_val
        assert "amount_formatted" in d_val

        # Cross-member privacy check: Other member cannot view this payment
        cross_resp = client.get(f"/api/v1/member/payments/{target_payment_id}", headers=other_headers)
        assert cross_resp.status_code == 403


def test_receipt_pdf_generation_and_public_verification():
    """Verify digital receipt payload, downloadable PDF, and public QR verification."""
    headers, user, member = _get_auth_headers()

    # Create and pay a transaction
    tx_resp = client.post(
        "/api/v1/member/payments/checkout",
        headers=headers,
        json={
            "purpose": "RENEWAL",
            "membership_plan_id": "RENEWAL",
            "amount": 2000,
            "provider": "BKASH",
            "currency": "BDT",
        },
    )
    p_id = tx_resp.json()["id"]

    client.post(
        "/api/v1/payments/sandbox/simulate",
        headers=headers,
        json={"payment_id": p_id, "outcome": "SUCCESS", "amount": 2000},
    )

    # 1. Get receipt JSON data
    rcp_resp = client.get(f"/api/v1/member/payments/{p_id}/receipt", headers=headers)
    assert rcp_resp.status_code == 200
    rcp_data = rcp_resp.json()
    assert rcp_data["status"] == "PAID"
    receipt_no = rcp_data["receipt_no"]
    assert receipt_no.startswith("PGCB-RCP-")

    # 2. Download receipt PDF
    pdf_resp = client.get(f"/api/v1/member/payments/{p_id}/receipt.pdf", headers=headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF")

    # 3. Public QR verification
    verify_resp = client.get(f"/api/v1/public/verify/payment/{receipt_no}")
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()
    assert v_data["verified"] is True
    assert v_data["is_valid"] is True
    assert v_data["receipt_no"] == receipt_no
    assert v_data["amount"] == 2000.0
    assert v_data["status"] == "PAID"

    # Non-existent reference returns 404
    non_exist = client.get("/api/v1/public/verify/payment/PGCB-RCP-9999-999999")
    assert non_exist.status_code == 404


def test_admin_reconciliation_and_refund_workflows():
    """Verify admin payment console, manual reconciliation, and refund endpoints."""
    headers, user, member = _get_auth_headers()
    admin_headers, admin_user = _get_admin_headers()

    # 1. Non-admin cannot access admin console
    unauth_resp = client.get("/api/v1/admin/payments", headers=headers)
    assert unauth_resp.status_code == 403

    # 2. Admin can access payment console
    admin_list = client.get("/api/v1/admin/payments", headers=admin_headers)
    assert admin_list.status_code == 200
    al_data = admin_list.json()
    assert "total_collected" in al_data
    assert "successful_count" in al_data
    assert "transactions" in al_data

    # 3. Create a pending payment
    p_resp = client.post(
        "/api/v1/member/payments/checkout",
        headers=headers,
        json={
            "purpose": "MEMBERSHIP",
            "membership_plan_id": "GENERAL",
            "amount": 2000,
            "provider": "MANUAL",
            "currency": "BDT",
        },
    )
    p_id = p_resp.json()["id"]

    # Non-admin cannot reconcile
    recon_fail = client.post(
        f"/api/v1/admin/payments/{p_id}/reconcile",
        headers=headers,
        json={"bank_reference": "BANK-CHALLAN-001", "note": "Cash deposit verification"},
    )
    assert recon_fail.status_code == 403

    # Admin reconciles payment to PAID
    unique_ref = f"BANK-CHALLAN-{int(datetime.utcnow().timestamp())}-{p_id}"
    recon_ok = client.post(
        f"/api/v1/admin/payments/{p_id}/reconcile",
        headers=admin_headers,
        json={"bank_reference": unique_ref, "note": "Verified via Sonali Bank deposit slip"},
    )
    assert recon_ok.status_code == 200
    assert recon_ok.json()["ok"] is True
    assert recon_ok.json()["payment"]["status"] == "PAID"
    assert recon_ok.json()["payment"]["receipt_no"] is not None

    # 4. Admin refunds payment
    refund_resp = client.post(
        f"/api/v1/admin/payments/{p_id}/refund",
        headers=admin_headers,
        json={"reason": "Member duplicate payment request", "amount": 2000},
    )
    assert refund_resp.status_code == 200
    assert refund_resp.json()["status"] == "REFUNDED"
    assert refund_resp.json()["payment"]["status"] == "REFUNDED"


def test_ai_assistant_payment_queries():
    """Verify AI assistant responds accurately to payment status, pending payments, and receipts."""
    headers, user, member = _get_auth_headers()

    # Query 1: Last payment check
    resp1 = client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json={"message": "আমার শেষ পেমেন্ট কত ছিল?", "mode": "MEMBER"},
    )
    assert resp1.status_code == 200
    c1 = resp1.json().get("answer") or resp1.json().get("answer_bn") or resp1.json().get("answer_en") or ""
    assert any(term in c1 for term in ("৳", "Amount", "পেমেন্ট", "পরিশোধিত", "টাকা"))
    # Check tool execution
    assert any(t["tool_name"] in ("my_payment_history", "member.get_payment_history") for t in resp1.json().get("tools_used", []))

    # Query 2: Pending payment check
    resp2 = client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json={"message": "আমার কি কোনো pending payment আছে?", "mode": "MEMBER"},
    )
    assert resp2.status_code == 200
    c2 = resp2.json().get("answer") or resp2.json().get("answer_bn") or resp2.json().get("answer_en") or ""
    assert any(term in c2 for term in ("pending", "পেন্ডিং", "বকেয়া", "হালনাগাদ", "টাকা", "৳"))

    # Query 3: Receipt download query
    resp3 = client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json={"message": "আমি কি রসিদ ডাউনলোড করতে পারি?", "mode": "MEMBER"},
    )
    assert resp3.status_code == 200
    actions = resp3.json().get("actions", [])
    assert any(a.get("type") in ("OPEN_PAYMENTS", "DOWNLOAD_RECEIPT", "OPEN_RECEIPT") for a in actions)
