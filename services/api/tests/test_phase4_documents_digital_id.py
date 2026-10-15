from __future__ import annotations

import io
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.core import Certificate, Member, MemberDocument, User

client = TestClient(app)


def _get_auth_headers(email: str = "member@pgcb.org.bd") -> tuple[dict[str, str], User, Member]:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                email=email,
                name_en="Engr. Test Member",
                name_bn="প্রকৌশলী টেস্ট মেম্বার",
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
                membership_id="PGCB-001245",
                membership_type="Professional",
                status="ACTIVE",
                issue_date=datetime.utcnow() - timedelta(days=365),
                validity_date=datetime.utcnow() + timedelta(days=457),
            )
            db.add(member)
            db.commit()
            db.refresh(member)
        else:
            member.status = "ACTIVE"
            member.validity_date = datetime.utcnow() + timedelta(days=457)
            db.commit()
            db.refresh(member)

        token = create_access_token(user.id, roles=[user.role])
        return {"Authorization": f"Bearer {token}"}, user, member
    finally:
        db.close()


def _get_other_member_auth_headers() -> tuple[dict[str, str], User, Member]:
    db = SessionLocal()
    try:
        email = "other_member@pgcb.org.bd"
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                email=email,
                name_en="Engr. Other Member",
                name_bn="প্রকৌশলী অন্য মেম্বার",
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
                membership_id="PGCB-009999",
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


def _get_admin_auth_headers() -> tuple[dict[str, str], User]:
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.role == "SUPER_ADMIN"))
        if not user:
            user = User(
                email="admin@pgcb.org.bd",
                name_en="System Administrator",
                name_bn="সিস্টেম অ্যাডমিনিস্ট্রেটর",
                password_hash="fakehash",
                role="SUPER_ADMIN",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        token = create_access_token(user.id, roles=[user.role])
        return {"Authorization": f"Bearer {token}"}, user
    finally:
        db.close()


VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"


def test_document_secure_upload_and_magic_byte_validation():
    headers, user, member = _get_auth_headers()

    # 1. Valid PDF upload
    files = {"file": ("national_id.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    data = {"document_type": "NATIONAL_ID", "title": "My National ID Card"}
    res = client.post("/api/v1/member/documents", headers=headers, files=files, data=data)
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["type"] == "NATIONAL_ID"
    assert payload["title"] == "My National ID Card"
    assert payload["status"] == "UNDER_REVIEW"
    assert payload["version"] == 1
    assert "versions" in payload
    assert len(payload["versions"]) == 1
    assert "/storage/" not in payload["download_url"]
    doc_id = payload["id"]

    # 2. Spoofed extension with invalid magic bytes (Text file pretending to be PDF)
    fake_files = {"file": ("malicious.pdf", io.BytesIO(b"Hello world, I am not a real PDF"), "application/pdf")}
    res_fake = client.post("/api/v1/member/documents", headers=headers, files=fake_files, data=data)
    assert res_fake.status_code == 400
    assert "Invalid file signature" in res_fake.text

    # 3. Invalid / arbitrary document category rejected
    bad_data = {"document_type": "ARBITRARY_UNKNOWN_TYPE"}
    res_bad = client.post(
        "/api/v1/member/documents",
        headers=headers,
        files={"file": ("cert.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")},
        data=bad_data,
    )
    assert res_bad.status_code == 400
    assert "Invalid document category" in res_bad.text


def test_document_versioning_and_replacement():
    headers, user, member = _get_auth_headers()

    # Initial upload
    files = {"file": ("academic_v1.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    res = client.post(
        "/api/v1/member/documents",
        headers=headers,
        files=files,
        data={"document_type": "ACADEMIC_CERTIFICATE", "title": "B.Sc. Certificate"},
    )
    assert res.status_code == 200
    doc_id = res.json()["id"]

    # Member replaces document (Version 2)
    replace_files = {"file": ("academic_v2.png", io.BytesIO(VALID_PNG_BYTES), "image/png")}
    res_rep = client.post(f"/api/v1/member/documents/{doc_id}/replace", headers=headers, files=replace_files)
    assert res_rep.status_code == 200, res_rep.text
    rep_data = res_rep.json()
    assert rep_data["version"] == 2
    assert rep_data["status"] == "UNDER_REVIEW"
    assert len(rep_data["versions"]) == 2
    # Verify version 1 is preserved
    version_numbers = [v["version_number"] for v in rep_data["versions"]]
    assert 1 in version_numbers and 2 in version_numbers


def test_cross_member_document_authorization_security():
    headers_a, user_a, member_a = _get_auth_headers()
    headers_b, user_b, member_b = _get_other_member_auth_headers()

    # Member A uploads document
    files = {"file": ("confidential_nid.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    res = client.post(
        "/api/v1/member/documents",
        headers=headers_a,
        files=files,
        data={"document_type": "NATIONAL_ID", "title": "Confidential NID"},
    )
    assert res.status_code == 200
    doc_id = res.json()["id"]

    # 1. Member A can view and download own document
    assert client.get(f"/api/v1/member/documents/{doc_id}", headers=headers_a).status_code == 200
    res_dl_a = client.get(f"/api/v1/member/documents/{doc_id}/download", headers=headers_a)
    assert res_dl_a.status_code == 200
    assert res_dl_a.headers.get("x-content-type-options") == "nosniff"

    # 2. Member B CANNOT view Member A's document (403 Forbidden)
    res_view_b = client.get(f"/api/v1/member/documents/{doc_id}", headers=headers_b)
    assert res_view_b.status_code == 403

    # 3. Member B CANNOT download Member A's document (403 Forbidden)
    res_dl_b = client.get(f"/api/v1/member/documents/{doc_id}/download", headers=headers_b)
    assert res_dl_b.status_code == 403

    # 4. Member B CANNOT replace Member A's document (403 Forbidden)
    rep_files = {"file": ("attack.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    res_rep_b = client.post(f"/api/v1/member/documents/{doc_id}/replace", headers=headers_b, files=rep_files)
    assert res_rep_b.status_code == 403

    # 5. Unauthenticated request rejected (401 Unauthorized)
    assert client.get(f"/api/v1/member/documents/{doc_id}").status_code == 401
    assert client.get(f"/api/v1/member/documents/{doc_id}/download").status_code == 401


def test_admin_document_verification_and_rejection_workflow():
    headers_member, user, member = _get_auth_headers()
    headers_admin, admin_user = _get_admin_auth_headers()

    # Member uploads document
    files = {"file": ("employment_letter.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    res = client.post(
        "/api/v1/member/documents",
        headers=headers_member,
        files=files,
        data={"document_type": "EMPLOYMENT_DOCUMENT", "title": "PGCB Employment Letter"},
    )
    assert res.status_code == 200
    doc_id = res.json()["id"]

    # 1. Admin views document list
    res_list = client.get("/api/v1/admin/documents?status=UNDER_REVIEW", headers=headers_admin)
    assert res_list.status_code == 200
    assert any(d["id"] == doc_id for d in res_list.json()["items"])

    # 2. Admin rejects with mandatory reason
    res_rej_no_reason = client.post(f"/api/v1/admin/documents/{doc_id}/reject", headers=headers_admin, json={"reason": ""})
    assert res_rej_no_reason.status_code in (400, 422)

    reason_msg = "The uploaded certificate is not readable. Please upload a clearer copy."
    res_rej = client.post(f"/api/v1/admin/documents/{doc_id}/reject", headers=headers_admin, json={"reason": reason_msg})
    assert res_rej.status_code == 200
    assert res_rej.json()["status"] == "REJECTED"
    assert res_rej.json()["reviewer_note"] == reason_msg

    # Member checks list and sees rejected state
    res_member_docs = client.get("/api/v1/member/documents", headers=headers_member)
    assert res_member_docs.status_code == 200
    member_doc = next(d for d in res_member_docs.json()["documents"] if d["id"] == doc_id)
    assert member_doc["status"] == "REJECTED"
    assert member_doc["reviewer_note"] == reason_msg

    # 3. Admin verifies document
    res_ver = client.post(f"/api/v1/admin/documents/{doc_id}/verify", headers=headers_admin, json={"notes": "All verified"})
    assert res_ver.status_code == 200
    assert res_ver.json()["status"] == "VERIFIED"
    assert res_ver.json()["verified_at"] is not None


def test_digital_member_id_and_realtime_anti_fraud_verification():
    headers, user, member = _get_auth_headers()

    # 1. Member views Digital ID
    res = client.get("/api/v1/member/digital-id", headers=headers)
    assert res.status_code == 200, res.text
    did_data = res.json()
    assert did_data["is_valid"] is True
    assert did_data["status"] == "ACTIVE"
    assert did_data["membership_id"] == "PGCB-001245"
    assert "/verify/member/" in did_data["verification_url"]
    qr_token = did_data["verification_url"].split("/verify/member/")[1]

    # 2. Public verification for active member
    res_pub = client.get(f"/api/v1/public/verify/member/{qr_token}")
    assert res_pub.status_code == 200
    pub_data = res_pub.json()
    assert pub_data["is_valid"] is True
    assert pub_data["status"] == "ACTIVE"
    assert pub_data["member_name"] == user.name_en

    # 3. ANTI-FRAUD ENGINE TEST: Member suspended in database
    db = SessionLocal()
    try:
        m = db.get(Member, member.id)
        m.status = "SUSPENDED"
        db.commit()
    finally:
        db.close()

    # Public verification MUST immediately reflect SUSPENDED regardless of pre-existing dates
    res_pub_suspended = client.get(f"/api/v1/public/verify/member/{qr_token}")
    assert res_pub_suspended.status_code == 200
    pub_sus = res_pub_suspended.json()
    assert pub_sus["is_valid"] is False
    assert pub_sus["status"] == "SUSPENDED"

    # Restore member status to ACTIVE
    db = SessionLocal()
    try:
        m = db.get(Member, member.id)
        m.status = "ACTIVE"
        db.commit()
    finally:
        db.close()


def test_certificate_center_and_revocation():
    headers, user, member = _get_auth_headers()
    headers_other, user_other, _ = _get_other_member_auth_headers()
    headers_admin, admin_user = _get_admin_auth_headers()

    # 1. Member lists certificates
    res = client.get("/api/v1/member/certificates", headers=headers)
    assert res.status_code == 200, res.text
    certs = res.json()
    assert len(certs) >= 1
    cert = certs[0]
    cert_id = cert["id"]
    cert_no = cert["certificate_no"]

    # 2. Cross-member access blocked
    res_other = client.get(f"/api/v1/member/certificates/{cert_id}", headers=headers_other)
    assert res_other.status_code == 403

    # 3. Public verification before revocation
    res_verify = client.get(f"/api/v1/public/verify/certificate/{cert_no}")
    assert res_verify.status_code == 200
    assert res_verify.json()["is_valid"] is True
    assert res_verify.json()["status"] == "VALID"

    # 4. Admin revokes certificate
    revoke_reason = "Administrative disciplinary review decision."
    res_revoke = client.post(
        f"/api/v1/admin/certificates/{cert_id}/revoke",
        headers=headers_admin,
        json={"reason": revoke_reason},
    )
    assert res_revoke.status_code == 200
    assert res_revoke.json()["status"] == "REVOKED"

    # 5. Public verification immediately reflects REVOKED
    res_verify_rev = client.get(f"/api/v1/public/verify/certificate/{cert_no}")
    assert res_verify_rev.status_code == 200
    data_rev = res_verify_rev.json()
    assert data_rev["is_valid"] is False
    assert data_rev["status"] == "REVOKED"
    assert data_rev["revocation_reason"] == revoke_reason


def test_ai_assistant_documents_and_digital_id_queries():
    headers, user, member = _get_auth_headers()

    # Create one document under review
    files = {"file": ("degree.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
    client.post(
        "/api/v1/member/documents",
        headers=headers,
        files=files,
        data={"document_type": "ACADEMIC_CERTIFICATE", "title": "B.Sc. Engineering Degree"},
    )

    # 1. Ask about pending documents in Bangla
    res_ai_docs = client.post(
        "/api/v1/ai/ask",
        headers=headers,
        json={"message": "আমার কোন documents এখনও pending?", "mode": "MEMBER", "language": "bn"},
    )
    assert res_ai_docs.status_code == 200
    ai_text_docs = res_ai_docs.json().get("answer", "")
    assert "review-এ আছে" in ai_text_docs or "Under Review" in ai_text_docs or "document" in ai_text_docs.lower()

    # 2. Ask about digital ID validity
    res_ai_did = client.post(
        "/api/v1/ai/ask",
        headers=headers,
        json={"message": "আমার digital ID valid আছে?", "mode": "MEMBER", "language": "bn"},
    )
    assert res_ai_did.status_code == 200
    ai_text_did = res_ai_did.json().get("answer", "")
    assert "ACTIVE" in ai_text_did or "Digital ID" in ai_text_did
