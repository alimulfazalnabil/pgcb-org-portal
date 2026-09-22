from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CircularCreate(BaseModel):
    category: str = 'GENERAL'
    reference_no: str | None = None
    title_bn: str = Field(min_length=3, max_length=500)
    title_en: str | None = None
    summary_bn: str | None = None
    document_url: str | None = None
    published_at: datetime | None = None
    is_published: bool = False
    priority: int = 0


class CircularResponse(CircularCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class CircleCreate(BaseModel):
    name_bn: str = Field(min_length=2, max_length=120)
    name_en: str = Field(min_length=2, max_length=120)
    description_bn: str | None = None
    active: bool = True


class CommitteeMemberCreate(BaseModel):
    name_bn: str = Field(min_length=2, max_length=200)
    name_en: str | None = None
    designation_bn: str = Field(min_length=2, max_length=200)
    designation_en: str | None = None
    message_bn: str | None = None
    photo_url: str | None = None
    circle_id: int | None = None
    term_start: int | None = None
    term_end: int | None = None
    display_order: int = 0
    active: bool = True


class JournalCreate(BaseModel):
    category: str = 'JOURNAL'
    title_bn: str = Field(min_length=3, max_length=500)
    title_en: str | None = None
    author: str | None = None
    edition: str | None = None
    publication_date: datetime | None = None
    abstract_bn: str | None = None
    cover_image_url: str | None = None
    document_url: str | None = None
    is_published: bool = False


class EventCreate(BaseModel):
    title_bn: str = Field(min_length=3, max_length=500)
    title_en: str | None = None
    description_bn: str | None = None
    event_date: datetime | None = None
    location_bn: str | None = None
    cover_image_url: str | None = None
    registration_enabled: bool = False
    capacity: int | None = Field(default=None, ge=1)
    registration_deadline: datetime | None = None
    fee_amount: int = Field(default=0, ge=0)
    fee_currency: str = Field(default='BDT', min_length=3, max_length=10)
    is_published: bool = False

class MediaCreate(BaseModel):
    media_type: str = 'PHOTO'
    title_bn: str = Field(min_length=2, max_length=500)
    description_bn: str | None = None
    url: str = Field(min_length=1, max_length=1000)
    thumbnail_url: str | None = None
    event_id: int | None = None
    published: bool = True


class ContactCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone: str | None = None
    subject: str = Field(min_length=2, max_length=300)
    message: str = Field(min_length=2, max_length=10000)


class SiteSettingUpdate(BaseModel):
    key: str = Field(min_length=2, max_length=120)
    value: str | None = None
    category: str = Field(default='GENERAL', max_length=80)


class NoticeCreate(BaseModel):
    title_bn: str = Field(min_length=2, max_length=300)
    title_en: str | None = None
    content_bn: str = Field(min_length=2)
    content_en: str | None = None
    priority: str = Field(default='NORMAL')
    category: str = Field(default='GENERAL')
    attachment_url: str | None = None
    is_pinned: bool = False
    is_published: bool = True
    published_at: datetime | None = None
    expires_at: datetime | None = None


class NoticeUpdate(BaseModel):
    title_bn: str | None = None
    title_en: str | None = None
    content_bn: str | None = None
    content_en: str | None = None
    priority: str | None = None
    category: str | None = None
    attachment_url: str | None = None
    is_pinned: bool | None = None
    is_published: bool | None = None
    expires_at: datetime | None = None


class NoticeResponse(NoticeCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class DocumentCreate(BaseModel):
    title_bn: str = Field(min_length=2, max_length=300)
    title_en: str | None = None
    category: str = Field(default='FORM')
    description_bn: str | None = None
    file_path: str = Field(min_length=1, max_length=500)
    file_size: int | None = None
    content_type: str | None = None
    version: str = Field(default='1.0')
    is_published: bool = True


class DocumentUpdate(BaseModel):
    title_bn: str | None = None
    title_en: str | None = None
    category: str | None = None
    description_bn: str | None = None
    file_path: str | None = None
    version: str | None = None
    is_published: bool | None = None


class DocumentResponse(DocumentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    download_count: int
    created_at: datetime
    updated_at: datetime

