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

