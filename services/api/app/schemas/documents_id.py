from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

CONTROLLED_DOCUMENT_TYPES = [
    "NATIONAL_ID",
    "PASSPORT",
    "PHOTOGRAPH",
    "ACADEMIC_CERTIFICATE",
    "PROFESSIONAL_CERTIFICATE",
    "EMPLOYMENT_DOCUMENT",
    "MEMBERSHIP_CERTIFICATE",
    "PAYMENT_RECEIPT",
    "EVENT_CERTIFICATE",
    "OTHER_APPROVED",
    "NID",
    "CERTIFICATE",
    "PHOTO",
    "PHOTO_ID",
    "RECEIPT",
]


class DocumentVersionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    version_number: int
    filename: str
    file_size: int
    content_type: str | None = None
    review_status: str
    reviewer_note: str | None = None
    uploaded_at: str


class DocumentVerificationEventItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    action: str
    previous_status: str | None = None
    new_status: str
    note: str | None = None
    actor_name: str | None = None
    created_at: str


class MemberDocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    document_type: str | None = None
    title: str
    status: str
    review_status: str | None = None
    filename: str | None = None
    uploaded_at: str
    verified_at: str | None = None
    expires_at: str | None = None
    version: int = 1
    file_size: int = 0
    mime_type: str | None = None
    reviewer_note: str | None = None
    download_url: str
    preview_url: str


class MemberDocumentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    document_type: str | None = None
    title: str
    status: str
    review_status: str | None = None
    filename: str | None = None
    uploaded_at: str
    verified_at: str | None = None
    expires_at: str | None = None
    version: int = 1
    file_size: int = 0
    mime_type: str | None = None
    reviewer_note: str | None = None
    download_url: str
    preview_url: str
    versions: list[DocumentVersionItem] = Field(default_factory=list)
    verification_timeline: list[DocumentVerificationEventItem] = Field(default_factory=list)


class MemberDocumentSummaryResponse(BaseModel):
    total_count: int
    verified_count: int
    pending_count: int
    rejected_count: int
    expired_count: int
    documents: list[MemberDocumentListItem]


class AdminDocumentRejectRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


class AdminDocumentVerifyRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)


class DigitalMemberIdResponse(BaseModel):
    identifier: str
    membership_id: str
    name_en: str
    name_bn: str
    membership_type: str
    circle_en: str
    circle_bn: str
    designation_en: str | None = None
    designation_bn: str | None = None
    photo_url: str | None = None
    status: str
    issue_date: str | None = None
    valid_until: str | None = None
    valid_until_formatted: str | None = None
    days_remaining: int | None = None
    is_valid: bool
    qr_code_data: str
    verification_url: str
    pdf_download_url: str
    image_download_url: str


class MemberCertificateItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    certificate_no: str
    certificate_number: str
    title_bn: str
    title_en: str | None = None
    certificate_type: str
    recipient_name: str
    issue_date: str
    status: str
    revoked_at: str | None = None
    revocation_reason: str | None = None
    download_url: str
    preview_url: str
    view_url: str | None = None
    verify_url: str


class AdminCertificateRevokeRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


class PublicMemberVerificationResponse(BaseModel):
    is_valid: bool
    membership_id: str
    member_name: str
    membership_type: str
    grid_circle: str
    status: str
    valid_until: str | None = None
    verified_at: str
    verification_reference: str


class PublicCertificateVerificationResponse(BaseModel):
    is_valid: bool
    certificate_no: str
    recipient_name: str
    certificate_type: str
    issue_date: str | None = None
    status: str
    revoked_at: str | None = None
    revocation_reason: str | None = None
    verified_at: str
