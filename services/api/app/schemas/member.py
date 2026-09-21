from pydantic import BaseModel

class VerificationResponse(BaseModel):
    verified: bool
    name_bn: str
    name_en: str | None = None
    membership_id: str
    employee_id: str | None = None
    designation_bn: str | None = None
    circle_bn: str | None = None
    status: str
    validity_date: str | None = None
    verified_at: str | None = None
