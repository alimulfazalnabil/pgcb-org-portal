from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from PIL import Image
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.deps import current_user, require_roles
from app.db.session import get_db
from app.models.core import Certificate, Circle, DocumentVerificationEvent, Member, MemberDocument, User
from app.domain.documents_id import (
    create_member_document,
    get_or_create_digital_id,
    reject_document_by_admin,
    replace_member_document,
    revoke_certificate_by_admin,
    serialize_digital_member_id,
    serialize_member_certificate,
    serialize_member_document_detail,
    serialize_member_document_list_item,
    verify_certificate_public,
    verify_document_by_admin,
    verify_member_public,
)
from app.routers.card import build_card, build_card_back
from app.schemas.documents_id import (
    AdminCertificateRevokeRequest,
    AdminDocumentRejectRequest,
    AdminDocumentVerifyRequest,
    DigitalMemberIdResponse,
    MemberCertificateItem,
    MemberDocumentDetail,
    MemberDocumentListItem,
    MemberDocumentSummaryResponse,
    PublicCertificateVerificationResponse,
    PublicMemberVerificationResponse,
)
from app.services.certificate_service import CertificateService

router = APIRouter(tags=["documents-digital-id"])


# ─────────────────────────────────────────────────────────────────────────────
# 1. MEMBER DOCUMENT CENTER
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/member/documents", response_model=MemberDocumentSummaryResponse)
def list_my_documents(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member profile not found.")

    stmt = (
        select(MemberDocument)
        .options(selectinload(MemberDocument.versions), selectinload(MemberDocument.verification_events))
        .where(MemberDocument.member_id == member.id, MemberDocument.deleted_at.is_(None))
        .order_by(desc(MemberDocument.id))
    )
    docs = list(db.scalars(stmt).all())

    # Calculate status counts across all member documents
    total_count = len(docs)
    verified_count = sum(1 for d in docs if (d.review_status or "").upper() == "VERIFIED")
    pending_count = sum(1 for d in docs if (d.review_status or "").upper() in ("PENDING", "UNDER_REVIEW"))
    rejected_count = sum(1 for d in docs if (d.review_status or "").upper() == "REJECTED")
    expired_count = sum(1 for d in docs if (d.review_status or "").upper() == "EXPIRED")

    # Apply filter if specified
    if status_filter and status_filter.upper() != "ALL":
        target = status_filter.upper()
        if target == "PENDING":
            filtered = [d for d in docs if (d.review_status or "").upper() in ("PENDING", "UNDER_REVIEW")]
        else:
            filtered = [d for d in docs if (d.review_status or "").upper() == target]
    else:
        filtered = docs

    return MemberDocumentSummaryResponse(
        total_count=total_count,
        verified_count=verified_count,
        pending_count=pending_count,
        rejected_count=rejected_count,
        expired_count=expired_count,
        documents=[serialize_member_document_list_item(d) for d in filtered],
    )


@router.post("/member/documents", response_model=MemberDocumentDetail)
async def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    document_type_query: Optional[str] = Query(None, alias="document_type"),
    title: Optional[str] = Form(None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    resolved_type = document_type or document_type_query
    if not resolved_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="document_type is required.")

    member = db.scalar(select(Member).where(Member.user_id == user.id))
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member profile not found.")

    content = await file.read()
    doc = create_member_document(
        db=db,
        member=member,
        document_type=resolved_type,
        file_bytes=content,
        original_filename=file.filename or "document.pdf",
        title=title,
        user=user,
    )
    return serialize_member_document_detail(doc)


@router.get("/member/documents/{document_id}", response_model=MemberDocumentDetail)
def get_my_document_detail(
    document_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member profile not found.")

    doc = db.scalar(
        select(MemberDocument)
        .options(
            selectinload(MemberDocument.versions),
            selectinload(MemberDocument.verification_events).selectinload(DocumentVerificationEvent.actor),
        )
        .where(MemberDocument.id == document_id, MemberDocument.deleted_at.is_(None))
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Strict ownership check
    if doc.member_id != member.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to view another member's document.",
        )

    return serialize_member_document_detail(doc)


@router.get("/member/documents/{document_id}/download")
def download_my_document(
    document_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member profile not found.")

    doc = db.get(MemberDocument, document_id)
    if not doc or doc.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Strict ownership check
    if doc.member_id != member.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to download another member's document.",
        )

    file_path = Path(doc.storage_path).resolve()
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found on disk.")

    media_type = doc.content_type or "application/octet-stream"
    headers = {"X-Content-Type-Options": "nosniff"}
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=doc.filename,
        headers=headers,
    )


@router.get("/member/documents/{document_id}/preview")
def preview_my_document(
    document_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member profile not found.")

    doc = db.get(MemberDocument, document_id)
    if not doc or doc.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if doc.member_id != member.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to preview another member's document.",
        )

    file_path = Path(doc.storage_path).resolve()
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found on disk.")

    media_type = doc.content_type or "application/pdf"
    headers = {
        "X-Content-Type-Options": "nosniff",
        "Content-Disposition": f'inline; filename="{doc.filename}"',
    }
    return FileResponse(path=file_path, media_type=media_type, headers=headers)


@router.post("/member/documents/{document_id}/replace", response_model=MemberDocumentDetail)
async def replace_document(
    document_id: int,
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member profile not found.")

    doc = db.get(MemberDocument, document_id)
    if not doc or doc.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if doc.member_id != member.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot replace another member's document.",
        )

    content = await file.read()
    replaced = replace_member_document(
        db=db,
        document=doc,
        file_bytes=content,
        original_filename=file.filename or "replacement.pdf",
        user=user,
    )
    return serialize_member_document_detail(replaced)


# ─────────────────────────────────────────────────────────────────────────────
# 2. DIGITAL MEMBER ID
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/member/digital-id", response_model=DigitalMemberIdResponse)
def get_digital_id(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    member = db.scalar(
        select(Member)
        .options(selectinload(Member.circle), selectinload(Member.user))
        .where(Member.user_id == user.id)
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member profile not found.")

    return serialize_digital_member_id(db, member, user)


@router.get("/member/digital-id/pdf")
def download_digital_id_pdf(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    member = db.scalar(
        select(Member)
        .options(selectinload(Member.circle), selectinload(Member.user), selectinload(Member.documents))
        .where(Member.user_id == user.id)
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member profile not found.")

    # Front and back cards
    front_path = build_card(member, user)
    back_path = build_card_back(member)
    pdf_path = front_path.with_name(f"digital_id_{member.membership_id or member.id}.pdf")

    with Image.open(front_path) as im_front, Image.open(back_path) as im_back:
        with open(pdf_path, "wb") as f:
            im_front.convert("RGB").save(
                f,
                "PDF",
                resolution=300.0,
                save_all=True,
                append_images=[im_back.convert("RGB")],
            )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"PGCB_Digital_ID_{member.membership_id or member.id}.pdf",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. CERTIFICATE CENTER
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/member/certificates", response_model=list[MemberCertificateItem])
def list_my_certificates(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member profile not found.")

    # Ensure member wallet certificate is provisioned if active
    CertificateService.ensure_member_wallet_certificates(db, user, member)

    certs = db.scalars(
        select(Certificate)
        .where(Certificate.member_id == member.id)
        .order_by(desc(Certificate.issue_date), desc(Certificate.id))
    ).all()

    return [serialize_member_certificate(c) for c in certs]


@router.get("/member/certificates/{certificate_id}", response_model=MemberCertificateItem)
def get_my_certificate_detail(
    certificate_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member profile not found.")

    cert = db.get(Certificate, certificate_id)
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found.")

    if cert.member_id != member.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot access another member's certificate.",
        )

    return serialize_member_certificate(cert)


@router.get("/member/certificates/{certificate_id}/download")
def download_my_certificate(
    certificate_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member profile not found.")

    cert = db.get(Certificate, certificate_id)
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found.")

    if cert.member_id != member.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot download another member's certificate.",
        )

    path = Path(cert.pdf_path).resolve() if cert.pdf_path else None
    if not path or not path.exists() or not path.is_file():
        _, path = CertificateService.render_certificate_files(cert)
        db.commit()

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"{cert.certificate_no or 'certificate'}.pdf",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. PUBLIC VERIFICATION
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/public/verify/member/{reference}", response_model=PublicMemberVerificationResponse)
def public_verify_member(reference: str, db: Session = Depends(get_db)):
    return verify_member_public(db, reference)


@router.get("/public/verify/certificate/{reference}", response_model=PublicCertificateVerificationResponse)
def public_verify_certificate(reference: str, db: Session = Depends(get_db)):
    return verify_certificate_public(db, reference)


# ─────────────────────────────────────────────────────────────────────────────
# 5. ADMIN DOCUMENT & CERTIFICATE MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

ADMIN_ROLES = ["SUPER_ADMIN", "MEMBERSHIP_OFFICER", "CENTRAL_ADMIN", "CONTENT_EDITOR", "CIRCLE_ADMIN"]


@router.get("/admin/documents")
def admin_list_documents(
    member_id: Optional[int] = Query(default=None),
    q: Optional[str] = Query(default=None),
    document_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    circle_id: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit
    stmt = (
        select(MemberDocument)
        .join(Member, MemberDocument.member_id == Member.id)
        .options(selectinload(MemberDocument.member).selectinload(Member.user), selectinload(MemberDocument.member).selectinload(Member.circle))
        .where(MemberDocument.deleted_at.is_(None))
        .order_by(desc(MemberDocument.id))
    )

    if member_id:
        stmt = stmt.where(MemberDocument.member_id == member_id)
    if document_type:
        stmt = stmt.where(MemberDocument.document_type == document_type.upper())
    if status and status.upper() != "ALL":
        target_st = status.upper()
        if target_st in ("UNDER_REVIEW", "PENDING"):
            stmt = stmt.where(MemberDocument.review_status.in_(["UNDER_REVIEW", "PENDING"]))
        else:
            stmt = stmt.where(MemberDocument.review_status == target_st)
    if circle_id:
        stmt = stmt.where(Member.circle_id == circle_id)
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                MemberDocument.title.ilike(like),
                MemberDocument.filename.ilike(like),
                Member.membership_id.ilike(like),
            )
        )

    total_count = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    docs = list(db.scalars(stmt.offset(offset).limit(limit)).all())

    items = []
    for d in docs:
        m = d.member
        u = m.user if m else None
        items.append({
            "id": d.id,
            "document_type": d.document_type,
            "title": d.title or d.filename,
            "filename": d.filename,
            "status": "UNDER_REVIEW" if (d.review_status in ("UNDER_REVIEW", "PENDING") or not d.review_status) else d.review_status,
            "review_status": d.review_status,
            "version": d.version,
            "file_size": d.file_size,
            "uploaded_at": d.created_at.isoformat() if d.created_at else None,
            "verified_at": d.verified_at.isoformat() if d.verified_at else None,
            "reviewer_note": d.reviewer_note,
            "member_id": d.member_id,
            "membership_id": m.membership_id if m else None,
            "member_name": (u.name_en or u.name_bn) if u else "Unknown",
            "circle_name": m.circle.name_en if m and m.circle else "N/A",
            "download_url": f"/api/v1/member/documents/{d.id}/download",
            "preview_url": f"/api/v1/member/documents/{d.id}/preview",
        })

    return {"total": total_count, "page": page, "limit": limit, "items": items}


@router.get("/admin/documents/{document_id}")
def admin_get_document(
    document_id: int,
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    doc = db.scalar(
        select(MemberDocument)
        .options(
            selectinload(MemberDocument.versions),
            selectinload(MemberDocument.verification_events).selectinload(DocumentVerificationEvent.actor),
            selectinload(MemberDocument.member).selectinload(Member.user),
            selectinload(MemberDocument.member).selectinload(Member.circle),
        )
        .where(MemberDocument.id == document_id, MemberDocument.deleted_at.is_(None))
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    m = doc.member
    u = m.user if m else None

    detail = serialize_member_document_detail(doc).model_dump()
    detail["member"] = {
        "id": m.id if m else None,
        "membership_id": m.membership_id if m else None,
        "name_en": u.name_en if u else None,
        "name_bn": u.name_bn if u else None,
        "email": u.email if u else None,
        "circle": m.circle.name_en if m and m.circle else None,
    }
    return detail


@router.post("/admin/documents/{document_id}/verify")
def admin_verify_document(
    document_id: int,
    payload: AdminDocumentVerifyRequest = None,
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    doc = db.get(MemberDocument, document_id)
    if not doc or doc.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    verified = verify_document_by_admin(
        db=db,
        document=doc,
        admin_user=user,
        notes=payload.notes if payload else None,
    )
    return serialize_member_document_detail(verified)


@router.post("/admin/documents/{document_id}/reject")
def admin_reject_document(
    document_id: int,
    payload: AdminDocumentRejectRequest,
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    doc = db.get(MemberDocument, document_id)
    if not doc or doc.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    rejected = reject_document_by_admin(
        db=db,
        document=doc,
        admin_user=user,
        reason=payload.reason,
    )
    return serialize_member_document_detail(rejected)


@router.get("/admin/certificates")
def admin_list_certificates(
    member_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
    certificate_type: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit
    stmt = (
        select(Certificate)
        .options(selectinload(Certificate.member).selectinload(Member.user))
        .order_by(desc(Certificate.id))
    )

    if member_id:
        stmt = stmt.where(Certificate.member_id == member_id)
    if status and status.upper() != "ALL":
        stmt = stmt.where(Certificate.status == status.upper())
    if certificate_type:
        stmt = stmt.where(Certificate.certificate_type == certificate_type.upper())
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Certificate.certificate_no.ilike(like),
                Certificate.recipient_name.ilike(like),
                Certificate.title_bn.ilike(like),
            )
        )

    total_count = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    certs = list(db.scalars(stmt.offset(offset).limit(limit)).all())

    items = []
    for c in certs:
        items.append({
            "id": c.id,
            "certificate_no": c.certificate_no,
            "certificate_type": c.certificate_type or "MEMBERSHIP",
            "recipient_name": c.recipient_name,
            "title_bn": c.title_bn,
            "title_en": c.title_en,
            "issue_date": c.issue_date.isoformat() if c.issue_date else None,
            "status": c.status or "VALID",
            "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None,
            "revocation_reason": c.revocation_reason,
            "member_id": c.member_id,
            "download_url": f"/api/v1/certificates/{c.certificate_no}.pdf",
            "preview_url": f"/api/v1/certificates/{c.certificate_no}.png",
        })

    return {"total": total_count, "page": page, "limit": limit, "items": items}


@router.post("/admin/certificates/{certificate_id}/revoke")
def admin_revoke_certificate(
    certificate_id: int,
    payload: AdminCertificateRevokeRequest,
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    cert = db.get(Certificate, certificate_id)
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found.")

    revoked = revoke_certificate_by_admin(
        db=db,
        cert=cert,
        admin_user=user,
        reason=payload.reason,
    )
    return serialize_member_certificate(revoked)
