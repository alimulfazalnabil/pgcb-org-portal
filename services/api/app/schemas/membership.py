from datetime import datetime
from pydantic import BaseModel, Field

class MemberProfileUpdate(BaseModel):
    name_bn: str = Field(min_length=2, max_length=200)
    name_en: str | None = None
    phone: str | None = None
    designation_bn: str | None = None
    designation_en: str | None = None
    employee_id: str | None = None
    diploma_institution: str | None = None
    graduation_year: int | None = Field(default=None, ge=1960, le=2100)
    nid_number: str | None = None
    date_of_birth: datetime | None = None
    current_address: str | None = None
    permanent_address: str | None = None
    circle_id: int | None = None

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
    created_at: datetime
