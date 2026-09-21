from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class EventRegistrationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    organization: str | None = Field(default=None, max_length=250)

class EventRegistrationResponse(BaseModel):
    id: int
    event_id: int
    name: str
    email: EmailStr
    phone: str | None
    organization: str | None
    ticket_code: str
    ticket_token: str | None = None
    registration_status: str
    attendance_status: str
    payment_status: str
    registered_at: datetime

class CheckInRequest(BaseModel):
    ticket_code: str = Field(min_length=8, max_length=80)

class RegistrationStatusUpdate(BaseModel):
    status: str

class PaymentCreate(BaseModel):
    amount: int = Field(gt=0)
    currency: str = Field(default='BDT', min_length=3, max_length=10)
    purpose: str = Field(default='MEMBERSHIP', max_length=50)
    provider: str = Field(default='MANUAL', max_length=40)
    event_registration_id: int | None = None
    transaction_ref: str | None = Field(default=None, max_length=120)

class PaymentStatusUpdate(BaseModel):
    status: str = Field(min_length=3, max_length=30)
    transaction_ref: str | None = Field(default=None, max_length=120)
