from datetime import datetime
from pydantic import BaseModel, Field

class MemberProfileUpdate(BaseModel):
    name_bn: str | None = Field(default=None, max_length=200)
    name_en: str | None = None
    phone: str | None = None
    alternate_phone: str | None = None
    email: str | None = None
    father_name: str | None = None
    mother_name: str | None = None
    gender: str | None = None
    blood_group: str | None = None
    designation_bn: str | None = None
    designation_en: str | None = None
    organization: str | None = None
    department: str | None = None
    profession: str | None = None
    academic_qualification: str | None = None
    professional_qualification: str | None = None
    years_of_experience: int | None = Field(default=None, ge=0, le=60)
    employee_id: str | None = None
    diploma_institution: str | None = None
    graduation_year: int | None = Field(default=None, ge=1960, le=2100)
    nid_number: str | None = None
    date_of_birth: datetime | str | None = None
    current_address: str | None = None
    permanent_address: str | None = None
    district: str | None = None
    circle_id: int | None = None
    membership_type: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_relationship: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_address: str | None = None
    preferred_language: str | None = None
    profile_visibility: str | None = None
    directory_visibility: bool | None = None
    contact_visibility: bool | None = None
    directory_visible: bool | None = None
    show_phone_in_directory: bool | None = None
    show_email_in_directory: bool | None = None
    status: str | None = None
    membership_status: str | None = None
    payment_status: str | None = None
    membership_id: str | None = None

class ProfileChangeRequestCreate(BaseModel):
    field_name: str = Field(min_length=2, max_length=80)
    requested_value: str = Field(min_length=1, max_length=2000)
    reason: str | None = None
    supporting_doc_url: str | None = None
    supporting_document_id: int | None = None

class ProfileChangeAdminAction(BaseModel):
    comment: str | None = None
    reviewer_comment: str | None = None

class ProfileChangeRequestResponse(BaseModel):
    id: int
    member_id: int
    field_name: str
    field_label_en: str
    field_label_bn: str
    current_value: str | None = None
    requested_value: str
    reason: str | None = None
    supporting_doc_url: str | None = None
    supporting_document_id: int | None = None
    status: str
    reviewer_id: int | None = None
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    reviewer_comment: str | None = None
    reviewer_note: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class ApplicationResponse(BaseModel):
    id: int
    membership_id: str | None
    status: str
    designation_bn: str | None
    circle_bn: str | None
    application_note: str | None
    issue_date: datetime | None
    validity_date: datetime | None

class MemberDocumentResponse(BaseModel):
    id: int
    document_type: str
    filename: str
    review_status: str
    reviewer_note: str | None = None
    created_at: datetime


class MemberDashboardResponse(BaseModel):
    member: dict
    membership: dict
    application: dict
    profile_completion: int
    payment_summary: dict
    documents: dict
    certificates: list[dict] = []
    upcoming_events: list[dict] = []
    notifications: list[dict] = []
    recent_activity: list[dict] = []


class MembershipSummaryResponse(BaseModel):
    membership_id: str | None = None
    type: str = 'PROFESSIONAL'
    status: str = 'ACTIVE'
    raw_status: str = 'ACTIVE'
    status_indicator: str = 'ACTIVE'
    grid_circle: dict | None = None
    joined_at: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    valid_until_formatted: str | None = None
    days_remaining: int | None = None
    total_validity_days: int | None = None
    progress_percentage: int = 100
    renewal_available: bool = False
    renewal_ineligible_reason: str | None = None
    certificate_available: bool = False
    digital_id_available: bool = False


class MembershipHistoryItem(BaseModel):
    id: int | str
    reference: str
    date: str
    action: str
    action_label_bn: str
    action_label_en: str
    period: str
    old_validity: str | None = None
    new_validity: str | None = None
    status: str
    status_label_bn: str
    payment_reference: str | None = None
    certificate_reference: str | None = None
    performed_by: str | None = None


class MembershipRenewalOption(BaseModel):
    duration_years: int
    fee_bdt: int
    fee_formatted: str
    new_validity: str
    new_validity_formatted: str
    discount_pct: int = 0
    title_bn: str
    title_en: str


class MembershipRenewalOptionsResponse(BaseModel):
    eligible: bool
    ineligible_reason: str | None = None
    current_validity: str | None = None
    plans: list[MembershipRenewalOption] = []


class MembershipRenewalRequest(BaseModel):
    duration_years: int = Field(ge=1, le=5, default=1)
    notes: str | None = None


class MembershipRenewalResponse(BaseModel):
    ok: bool = True
    renewal_id: int
    reference: str
    duration_years: int
    amount: int
    amount_formatted: str
    currency: str = 'BDT'
    new_validity: str
    status: str = 'PENDING'
    transaction_id: str | None = None
    payment_url: str | None = None
    message: str


class ApplicationTimelineStep(BaseModel):
    step_key: str
    title_bn: str
    title_en: str
    status: str
    description: str | None = None
    timestamp: str | None = None
    actor_type: str | None = None


class ApplicationDetailsResponse(BaseModel):
    application_no: str
    membership_type: str
    status: str
    status_label_bn: str
    status_label_en: str
    circle: dict | None = None
    submitted_at: str | None = None
    reviewed_at: str | None = None
    timeline: list[ApplicationTimelineStep] = []
    documents: list[dict] = []
    required_document_types: list[str] = []
    pending_payment: dict | None = None


