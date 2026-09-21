from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name_bn: str | None = None
    name_en: str | None = None
    phone: str | None = None
    fullNameBn: str | None = None
    fullNameEn: str | None = None
    employeeId: str | None = None
    designation: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: str | None = Field(default=None, pattern=r'^\d{6}$')


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=8, max_length=128)


class MeResponse(BaseModel):
    id: int
    email: EmailStr
    name_bn: str
    name_en: str | None
    role: str
    membership_id: str | None = None
    membership_status: str | None = None
    designation_bn: str | None = None
    circle_bn: str | None = None


class RegisterResponse(MeResponse):
    verification_required: bool = False
    verification_token: str | None = None


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
