from pydantic import BaseModel, EmailStr, Field


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name_bn: str = Field(min_length=2, max_length=200)
    name_en: str | None = None
    phone: str | None = None
    role: str = 'MEMBER'
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    name_bn: str | None = None
    name_en: str | None = None
    phone: str | None = None
    role: str | None = None
    is_active: bool | None = None


class MessageStatusUpdate(BaseModel):
    status: str = Field(pattern='^(NEW|IN_PROGRESS|RESOLVED|ARCHIVED)$')
