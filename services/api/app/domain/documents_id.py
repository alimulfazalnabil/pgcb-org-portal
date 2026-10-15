from __future__ import annotations

import hashlib
import hmac
import os
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.core import (
    Certificate,
    CertificateVerificationRecord,
    DigitalMemberId,
    DocumentVerificationEvent,
    DocumentVersion,
    Member,
    MemberDocument,
    Notification,
    User,
)
from app.schemas.documents_id import (
    CONTROLLED_DOCUMENT_TYPES,
    DigitalMemberIdResponse,
    DocumentVerificationEventItem,
    DocumentVersionItem,
    MemberCertificateItem,
    MemberDocumentDetail,
    MemberDocumentListItem,
    PublicCertificateVerificationResponse,
    PublicMemberVerificationResponse,
)
from app.services import BASE_STORAGE, audit, notify

MAX_PDF_SIZE_BYTES = int(os.getenv("MAX_DOCUMENT_PDF_BYTES", str(10 * 1024 * 1024)))  # 10 MB
MAX_IMAGE_SIZE_BYTES = int(os.getenv("MAX_DOCUMENT_IMAGE_BYTES", str(5 * 1024 * 1024)))  # 5 MB

SUPPORTED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def _validate_magic_bytes(content: bytes, ext: str) -> str:
    """Validate content using magic bytes and return canonical mime type."""
    if ext == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file signature: Not a valid PDF document.",
            )
        return "application/pdf"
    elif ext in (".jpg", ".jpeg"):
        if not (content.startswith(b"\xff\xd8\xff") or (len(content) > 3 and content[:2] == b"\xff\xd8")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file signature: Not a valid JPEG image.",
            )
        return "image/jpeg"
    elif ext == ".png":
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file signature: Not a valid PNG image.",
            )
        return "image/png"
    elif ext == ".webp":
        if not (content.startswith(b"RIFF") and len(content) > 12 and content[8:12] == b"WEBP"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file signature: Not a valid WebP image.",
            )
        return "image/webp"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: {ext}. Allowed: PDF, JPG, PNG, WEBP.",
        )


def _get_document_storage_dir() -> Path:
    target = BASE_STORAGE / "member_documents"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _generate_opaque_qr_token(member: Member) -> str:
    seed = f"{member.membership_id}:{member.id}:{settings.jwt_secret}"
    sig = hmac.new(settings.jwt_secret.encode(), seed.encode(), hashlib.sha256).hexdigest()[:24].upper()
    return f"DID-{member.id}-{sig}"


def validate_and_save_upload(file_bytes: bytes, original_filename: str) -> tuple[str, str, int, str]:
    """Validates size, magic bytes and saves to random key on disk."""
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    clean_name = os.path.basename(original_filename or "document.pdf")
    ext = os.path.splitext(clean_name)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Only PDF, JPG, PNG, and WEBP are accepted.",
        )

    file_size = len(file_bytes)
    if ext == ".pdf" and file_size > MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF file size exceeds maximum limit of {MAX_PDF_SIZE_BYTES // (1024 * 1024)}MB.",
        )
    elif ext != ".pdf" and file_size > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image file size exceeds maximum limit of {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB.",
        )

    mime_type = _validate_magic_bytes(file_bytes, ext)

    # Generate random storage key avoiding any directory traversal
    storage_filename = f"doc_{uuid.uuid4().hex[:16]}{ext}"
    storage_path = _get_document_storage_dir() / storage_filename

    with open(storage_path, "wb") as f:
        f.write(file_bytes)

    return clean_name, str(storage_path), file_size, mime_type


def create_member_document(
    db: Session,
    member: Member,
    document_type: str,
    file_bytes: bytes,
    original_filename: str,
    title: str | None = None,
    user: User | None = None,
) -> MemberDocument:
    doc_type = document_type.strip().upper()
    if doc_type not in CONTROLLED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document category '{document_type}'. Controlled categories: {', '.join(CONTROLLED_DOCUMENT_TYPES)}",
        )

    clean_name, storage_path, file_size, mime_type = validate_and_save_upload(file_bytes, original_filename)
    display_title = title.strip() if title and title.strip() else clean_name

    now = datetime.utcnow()
    doc = MemberDocument(
        member_id=member.id,
        document_type=doc_type,
        title=display_title,
        filename=clean_name,
        storage_path=storage_path,
        content_type=mime_type,
        file_size=file_size,
        version=1,
        review_status="UNDER_REVIEW",
        reviewer_note=None,
        created_at=now,
    )
    db.add(doc)
    db.flush()

    # Create initial version
    version_row = DocumentVersion(
        document_id=doc.id,
        version_number=1,
        filename=clean_name,
        storage_path=storage_path,
        content_type=mime_type,
        file_size=file_size,
        review_status="UNDER_REVIEW",
        reviewer_note=None,
        uploaded_at=now,
        created_at=now,
    )
    db.add(version_row)

    # Create audit/verification event
    event = DocumentVerificationEvent(
        document_id=doc.id,
        action="UPLOAD",
        actor_id=user.id if user else None,
        previous_status=None,
        new_status="UNDER_REVIEW",
        note="Initial document upload",
        created_at=now,
    )
    db.add(event)
    db.commit()
    db.refresh(doc)
    return doc


def replace_member_document(
    db: Session,
    document: MemberDocument,
    file_bytes: bytes,
    original_filename: str,
    user: User | None = None,
) -> MemberDocument:
    clean_name, storage_path, file_size, mime_type = validate_and_save_upload(file_bytes, original_filename)
    new_version_num = (document.version or 1) + 1
    previous_status = document.review_status

    now = datetime.utcnow()
    # Update current document record
    document.version = new_version_num
    document.filename = clean_name
    document.storage_path = storage_path
    document.content_type = mime_type
    document.file_size = file_size
    document.review_status = "UNDER_REVIEW"
    document.reviewer_note = None
    document.verified_at = None

    # Add new immutable version row
    version_row = DocumentVersion(
        document_id=document.id,
        version_number=new_version_num,
        filename=clean_name,
        storage_path=storage_path,
        content_type=mime_type,
        file_size=file_size,
        review_status="UNDER_REVIEW",
        reviewer_note=None,
        uploaded_at=now,
        created_at=now,
    )
    db.add(version_row)

    # Add event
    event = DocumentVerificationEvent(
        document_id=document.id,
        action="REPLACE",
        actor_id=user.id if user else None,
        previous_status=previous_status,
        new_status="UNDER_REVIEW",
        note=f"Member submitted revision (Version {new_version_num})",
        created_at=now,
    )
    db.add(event)
    db.commit()
    db.refresh(document)
    return document


def verify_document_by_admin(
    db: Session,
    document: MemberDocument,
    admin_user: User,
    notes: str | None = None,
) -> MemberDocument:
    prev_status = document.review_status
    now = datetime.utcnow()
    document.review_status = "VERIFIED"
    document.reviewer_note = notes
    document.verified_at = now

    event = DocumentVerificationEvent(
        document_id=document.id,
        action="VERIFY",
        actor_id=admin_user.id,
        previous_status=prev_status,
        new_status="VERIFIED",
        note=notes or "Document verified and approved by admin",
        created_at=now,
    )
    db.add(event)

    # Notify member
    if document.member and document.member.user_id:
        notify(
            db,
            document.member.user_id,
            "ডকুমেন্ট যাচাইকরণ সম্পন্ন (Document Verified)",
            f"আপনার জমা দেওয়া '{document.title or document.document_type}' নথিটি সফলভাবে অনুমোদিত হয়েছে।",
            "DOCUMENT_VERIFIED",
        )

    db.commit()
    db.refresh(document)
    return document


def reject_document_by_admin(
    db: Session,
    document: MemberDocument,
    admin_user: User,
    reason: str,
) -> MemberDocument:
    if not reason or not reason.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason is required.",
        )

    prev_status = document.review_status
    now = datetime.utcnow()
    document.review_status = "REJECTED"
    document.reviewer_note = reason.strip()

    event = DocumentVerificationEvent(
        document_id=document.id,
        action="REJECT",
        actor_id=admin_user.id,
        previous_status=prev_status,
        new_status="REJECTED",
        note=reason.strip(),
        created_at=now,
    )
    db.add(event)

    # Notify member
    if document.member and document.member.user_id:
        notify(
            db,
            document.member.user_id,
            "ডকুমেন্ট সংশোধন প্রয়োজন (Document Rejected)",
            f"আপনার জমা দেওয়া '{document.title or document.document_type}' নথিটি প্রত্যাখ্যাত হয়েছে। কারণ: {reason.strip()}",
            "DOCUMENT_REJECTED",
        )

    db.commit()
    db.refresh(document)
    return document


def serialize_member_document_list_item(doc: MemberDocument) -> MemberDocumentListItem:
    return MemberDocumentListItem(
        id=doc.id,
        type=doc.document_type,
        title=doc.title or doc.filename or doc.document_type,
        status=doc.review_status or "UNDER_REVIEW",
        uploaded_at=doc.created_at.isoformat() if doc.created_at else datetime.utcnow().isoformat(),
        verified_at=doc.verified_at.isoformat() if doc.verified_at else None,
        expires_at=doc.expires_at.isoformat() if doc.expires_at else None,
        version=doc.version or 1,
        file_size=doc.file_size or 0,
        mime_type=doc.content_type,
        reviewer_note=doc.reviewer_note,
        download_url=f"/api/v1/member/documents/{doc.id}/download",
        preview_url=f"/api/v1/member/documents/{doc.id}/preview",
    )


def serialize_member_document_detail(doc: MemberDocument) -> MemberDocumentDetail:
    versions = [
        DocumentVersionItem(
            id=v.id,
            version_number=v.version_number,
            filename=v.filename,
            file_size=v.file_size,
            content_type=v.content_type,
            review_status=v.review_status,
            reviewer_note=v.reviewer_note,
            uploaded_at=v.uploaded_at.isoformat() if v.uploaded_at else v.created_at.isoformat(),
        )
        for v in (doc.versions or [])
    ]
    timeline = [
        DocumentVerificationEventItem(
            id=e.id,
            action=e.action,
            previous_status=e.previous_status,
            new_status=e.new_status,
            note=e.note,
            actor_name=(e.actor.name_en or e.actor.name_bn) if e.actor else "System",
            created_at=e.created_at.isoformat() if e.created_at else datetime.utcnow().isoformat(),
        )
        for e in (doc.verification_events or [])
    ]

    return MemberDocumentDetail(
        id=doc.id,
        type=doc.document_type,
        title=doc.title or doc.filename or doc.document_type,
        status=doc.review_status or "UNDER_REVIEW",
        uploaded_at=doc.created_at.isoformat() if doc.created_at else datetime.utcnow().isoformat(),
        verified_at=doc.verified_at.isoformat() if doc.verified_at else None,
        expires_at=doc.expires_at.isoformat() if doc.expires_at else None,
        version=doc.version or 1,
        file_size=doc.file_size or 0,
        mime_type=doc.content_type,
        reviewer_note=doc.reviewer_note,
        download_url=f"/api/v1/member/documents/{doc.id}/download",
        preview_url=f"/api/v1/member/documents/{doc.id}/preview",
        versions=versions,
        verification_timeline=timeline,
    )


def get_or_create_digital_id(db: Session, member: Member) -> DigitalMemberId:
    """Retrieves or provisions an authoritative digital member ID for the given member."""
    did = db.scalar(select(DigitalMemberId).where(DigitalMemberId.member_id == member.id))
    now = datetime.utcnow()
    token = _generate_opaque_qr_token(member)

    # Determine real-time status:
    # If member suspended / cancelled / revoked, overrides date
    member_status = (member.status or "PENDING").upper()
    if member_status in ("SUSPENDED", "CANCELLED", "REVOKED"):
        live_status = member_status
    elif member.validity_date and member.validity_date < now:
        live_status = "EXPIRED"
    elif member_status == "ACTIVE":
        live_status = "ACTIVE"
    else:
        live_status = member_status

    if not did:
        did = DigitalMemberId(
            member_id=member.id,
            identifier=f"DID-{member.membership_id or member.id}",
            qr_token=token,
            version=1,
            issued_at=member.issue_date or now,
            valid_from=member.issue_date or now,
            valid_until=member.validity_date,
            status=live_status,
            created_at=now,
            updated_at=now,
        )
        db.add(did)
        db.commit()
        db.refresh(did)
    else:
        # Keep real-time synchronized status
        if did.status != live_status or did.valid_until != member.validity_date:
            did.status = live_status
            did.valid_until = member.validity_date
            did.updated_at = now
            db.commit()
            db.refresh(did)

    return did


def serialize_digital_member_id(db: Session, member: Member, user: User) -> DigitalMemberIdResponse:
    did = get_or_create_digital_id(db, member)
    now = datetime.utcnow()

    # Authoritative days remaining
    days_rem = None
    if member.validity_date:
        days_rem = (member.validity_date - now).days

    is_valid = did.status == "ACTIVE" and (days_rem is None or days_rem >= 0)
    verify_url = f"{settings.frontend_url.rstrip('/')}/verify/member/{did.qr_token}"

    return DigitalMemberIdResponse(
        identifier=did.identifier,
        membership_id=member.membership_id or f"PGCB-{member.id:06d}",
        name_en=user.name_en or user.name_bn,
        name_bn=user.name_bn,
        membership_type=member.membership_type or "General",
        circle_en=member.circle.name_en if member.circle else "Central",
        circle_bn=member.circle.name_bn if member.circle else "কেন্দ্রীয়",
        designation_en=member.designation_en or member.designation_bn,
        designation_bn=member.designation_bn,
        photo_url=member.photo_url,
        status=did.status,
        issue_date=did.issued_at.isoformat() if did.issued_at else None,
        valid_until=did.valid_until.isoformat() if did.valid_until else None,
        valid_until_formatted=did.valid_until.strftime("%d %B %Y") if did.valid_until else None,
        days_remaining=days_rem,
        is_valid=is_valid,
        qr_code_data=verify_url,
        verification_url=verify_url,
        pdf_download_url="/api/v1/member/digital-id/pdf",
        image_download_url="/api/v1/member/card?side=front",
    )


def verify_member_public(db: Session, reference: str) -> PublicMemberVerificationResponse:
    clean_ref = reference.strip()

    # Lookup either by qr_token or membership_id or identifier
    did = db.scalar(
        select(DigitalMemberId)
        .options(selectinload(DigitalMemberId.member).selectinload(Member.circle), selectinload(DigitalMemberId.member).selectinload(Member.user))
        .where(
            or_(
                DigitalMemberId.qr_token == clean_ref,
                DigitalMemberId.identifier == clean_ref,
            )
        )
    )

    member = did.member if did else None
    if not member:
        member = db.scalar(
            select(Member)
            .options(selectinload(Member.circle), selectinload(Member.user))
            .where(Member.membership_id == clean_ref)
        )
        if member:
            did = get_or_create_digital_id(db, member)

    if not member or not member.user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member verification record not found.",
        )

    # ANTI-FRAUD ENGINE:
    # Status calculation MUST be authoritative real-time from the database
    now = datetime.utcnow()
    raw_status = (member.status or "PENDING").upper()

    if raw_status in ("SUSPENDED", "CANCELLED", "REVOKED"):
        auth_status = raw_status
        is_valid = False
    elif member.validity_date and member.validity_date < now:
        auth_status = "EXPIRED"
        is_valid = False
    elif raw_status == "ACTIVE":
        auth_status = "ACTIVE"
        is_valid = True
    else:
        auth_status = raw_status
        is_valid = False

    return PublicMemberVerificationResponse(
        is_valid=is_valid,
        membership_id=member.membership_id or f"PGCB-{member.id:06d}",
        member_name=member.user.name_en or member.user.name_bn,
        membership_type=member.membership_type or "General",
        grid_circle=member.circle.name_en if member.circle else "Central Secretariat",
        status=auth_status,
        valid_until=member.validity_date.strftime("%d %B %Y") if member.validity_date else None,
        verified_at=now.isoformat(),
        verification_reference=clean_ref,
    )


def serialize_member_certificate(cert: Certificate) -> MemberCertificateItem:
    cert_no = cert.certificate_no or f"PGCB-CERT-{cert.id:06d}"
    return MemberCertificateItem(
        id=cert.id,
        certificate_no=cert_no,
        certificate_number=cert_no,
        title_bn=cert.title_bn,
        title_en=cert.title_en or cert.title_bn,
        certificate_type=cert.certificate_type or "MEMBERSHIP",
        recipient_name=cert.recipient_name,
        issue_date=cert.issue_date.strftime("%d %b %Y") if cert.issue_date else "N/A",
        status=cert.status or "VALID",
        revoked_at=cert.revoked_at.isoformat() if cert.revoked_at else None,
        revocation_reason=cert.revocation_reason,
        download_url=f"/api/v1/member/certificates/{cert.id}/download",
        preview_url=f"/api/v1/certificates/{cert_no}.png",
        verify_url=f"/api/v1/public/verify/certificate/{cert_no}",
    )


def verify_certificate_public(db: Session, reference: str) -> PublicCertificateVerificationResponse:
    clean_ref = reference.strip()
    token_hash = hashlib.sha256(clean_ref.encode()).hexdigest()

    cert = db.scalar(
        select(Certificate).where(
            or_(
                Certificate.certificate_no == clean_ref,
                Certificate.verification_token_hash == token_hash,
            )
        )
    )

    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate verification record not found.",
        )

    now = datetime.utcnow()
    is_revoked = cert.status == "REVOKED" or cert.revoked_at is not None

    return PublicCertificateVerificationResponse(
        is_valid=not is_revoked,
        certificate_no=cert.certificate_no,
        recipient_name=cert.recipient_name,
        certificate_type=cert.certificate_type or "MEMBERSHIP",
        issue_date=cert.issue_date.strftime("%d %B %Y") if cert.issue_date else None,
        status="REVOKED" if is_revoked else "VALID",
        revoked_at=cert.revoked_at.isoformat() if cert.revoked_at else None,
        revocation_reason=cert.revocation_reason if is_revoked else None,
        verified_at=now.isoformat(),
    )


def revoke_certificate_by_admin(
    db: Session,
    cert: Certificate,
    admin_user: User,
    reason: str,
) -> Certificate:
    if not reason or not reason.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Revocation reason is required.")

    now = datetime.utcnow()
    cert.status = "REVOKED"
    cert.revoked_at = now
    cert.revocation_reason = reason.strip()
    cert.revoked_by_id = admin_user.id

    rec = CertificateVerificationRecord(
        certificate_id=cert.id,
        action="REVOKED",
        actor_id=admin_user.id,
        reason=reason.strip(),
        created_at=now,
    )
    db.add(rec)

    # Notify recipient member if associated
    if cert.member_id:
        member = db.get(Member, cert.member_id)
        if member and member.user_id:
            notify(
                db,
                member.user_id,
                "সনদপত্র প্রত্যাহার করা হয়েছে (Certificate Revoked)",
                f"আপনার সনদপত্রটি ({cert.certificate_no}) প্রত্যাহার করা হয়েছে। কারণ: {reason.strip()}",
                "CERTIFICATE_REVOKED",
            )

    db.commit()
    db.refresh(cert)
    return cert
