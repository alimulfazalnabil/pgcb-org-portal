from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Circle(Base, TimestampMixin):
    __tablename__ = 'circles'
    id: Mapped[int] = mapped_column(primary_key=True)
    name_bn: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name_en: Mapped[str] = mapped_column(String(120))
    description_bn: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name_bn: Mapped[str] = mapped_column(String(200))
    name_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(40), default='MEMBER', index=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    mfa_secret: Mapped[str | None] = mapped_column(String(256), nullable=True)
    mfa_secret_enc: Mapped[str | None] = mapped_column(String(512), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    member = relationship('Member', back_populates='user', uselist=False, cascade='all,delete-orphan')

class Member(Base):
    __tablename__ = 'members'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), unique=True, index=True)
    membership_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True, index=True)
    designation_bn: Mapped[str | None] = mapped_column(String(200), nullable=True)
    designation_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    employee_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    diploma_institution: Mapped[str | None] = mapped_column(String(250), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nid_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    date_of_birth: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    permanent_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    circle_id: Mapped[int | None] = mapped_column(ForeignKey('circles.id'), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default='PENDING', index=True)
    application_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    issue_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    validity_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship('User', back_populates='member')
    circle = relationship('Circle')
    documents = relationship('MemberDocument', back_populates='member', cascade='all,delete-orphan')

class MemberDocument(Base):
    __tablename__ = 'member_documents'
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey('members.id', ondelete='CASCADE'), index=True)
    document_type: Mapped[str] = mapped_column(String(50))
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(1000))
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    review_status: Mapped[str] = mapped_column(String(30), default='PENDING', index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    member = relationship('Member', back_populates='documents')

class CommitteeMember(Base):
    __tablename__ = 'committee_members'
    id: Mapped[int] = mapped_column(primary_key=True)
    name_bn: Mapped[str] = mapped_column(String(200))
    name_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    designation_bn: Mapped[str] = mapped_column(String(200))
    designation_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    message_bn: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    circle_id: Mapped[int | None] = mapped_column(ForeignKey('circles.id'), nullable=True, index=True)
    term_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    term_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Circular(Base):
    __tablename__ = 'circulars'
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(40), default='GENERAL', index=True)
    reference_no: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    title_bn: Mapped[str] = mapped_column(String(500), index=True)
    title_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary_bn: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Journal(Base):
    __tablename__ = 'journals'
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(80), default='JOURNAL', index=True)
    title_bn: Mapped[str] = mapped_column(String(500), index=True)
    title_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    author: Mapped[str | None] = mapped_column(String(300), nullable=True)
    edition: Mapped[str | None] = mapped_column(String(100), nullable=True)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    abstract_bn: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    document_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Event(Base):
    __tablename__ = 'events'
    id: Mapped[int] = mapped_column(primary_key=True)
    title_bn: Mapped[str] = mapped_column(String(500), index=True)
    title_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description_bn: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    location_bn: Mapped[str | None] = mapped_column(String(300), nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    registration_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    registration_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fee_amount: Mapped[int] = mapped_column(Integer, default=0)
    fee_currency: Mapped[str] = mapped_column(String(10), default='BDT')
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class MediaAsset(Base):
    __tablename__ = 'media_assets'
    id: Mapped[int] = mapped_column(primary_key=True)
    media_type: Mapped[str] = mapped_column(String(20), default='PHOTO', index=True)
    title_bn: Mapped[str] = mapped_column(String(500))
    description_bn: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(1000))
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey('events.id'), nullable=True, index=True)
    published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ContactMessage(Base):
    __tablename__ = 'contact_messages'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject: Mapped[str] = mapped_column(String(300))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default='NEW', index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = 'notifications'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    title_bn: Mapped[str] = mapped_column(String(300))
    body_bn: Mapped[str] = mapped_column(Text)
    notification_type: Mapped[str] = mapped_column(String(50), default='GENERAL')
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class SiteSetting(Base):
    __tablename__ = 'site_settings'
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(80), default='GENERAL', index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PasswordResetToken(Base):
    __tablename__ = 'password_reset_tokens'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EmailVerificationToken(Base):
    __tablename__ = 'email_verification_tokens'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserSession(Base):
    __tablename__ = 'user_sessions'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class EventRegistration(Base):
    __tablename__ = 'event_registrations'
    __table_args__ = (UniqueConstraint('event_id', 'email', name='uq_event_registration_email'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey('events.id', ondelete='CASCADE'), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(250), nullable=True)
    ticket_code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    registration_status: Mapped[str] = mapped_column(String(30), default='REGISTERED', index=True)
    attendance_status: Mapped[str] = mapped_column(String(30), default='NOT_CHECKED_IN', index=True)
    payment_status: Mapped[str] = mapped_column(String(30), default='NOT_REQUIRED', index=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    checked_in_by: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)

class PaymentTransaction(Base):
    __tablename__ = 'payment_transactions'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    member_id: Mapped[int | None] = mapped_column(ForeignKey('members.id', ondelete='SET NULL'), nullable=True, index=True)
    event_registration_id: Mapped[int | None] = mapped_column(ForeignKey('event_registrations.id', ondelete='SET NULL'), nullable=True, index=True)
    purpose: Mapped[str] = mapped_column(String(50), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default='BDT')
    provider: Mapped[str] = mapped_column(String(40), default='MANUAL')
    transaction_ref: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default='PENDING', index=True)
    provider_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NotificationDelivery(Base):
    __tablename__ = 'notification_deliveries'
    id: Mapped[int] = mapped_column(primary_key=True)
    notification_id: Mapped[int | None] = mapped_column(ForeignKey('notifications.id', ondelete='CASCADE'), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)
    recipient: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default='QUEUED', index=True)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(180), unique=True, nullable=True, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class PaymentWebhookEvent(Base):
    __tablename__ = 'payment_webhook_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(40), index=True)
    event_id: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    signature_valid: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(30), default='RECEIVED', index=True)
    payment_id: Mapped[int | None] = mapped_column(ForeignKey('payment_transactions.id', ondelete='SET NULL'), nullable=True, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class MembershipRenewal(Base):
    __tablename__ = 'membership_renewals'
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey('members.id', ondelete='CASCADE'), index=True)
    payment_id: Mapped[int | None] = mapped_column(ForeignKey('payment_transactions.id', ondelete='SET NULL'), nullable=True, index=True)
    previous_validity_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    new_validity_date: Mapped[datetime] = mapped_column(DateTime)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(10), default='BDT')
    status: Mapped[str] = mapped_column(String(30), default='COMPLETED', index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class MembershipReminder(Base):
    __tablename__ = 'membership_reminders'
    __table_args__ = (UniqueConstraint('member_id', 'validity_date', 'reminder_type', name='uq_membership_reminder'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey('members.id', ondelete='CASCADE'), index=True)
    validity_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    reminder_type: Mapped[str] = mapped_column(String(30), index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class Certificate(Base):
    __tablename__ = 'certificates'
    id: Mapped[int] = mapped_column(primary_key=True)
    certificate_no: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    recipient_name: Mapped[str] = mapped_column(String(250))
    title_bn: Mapped[str] = mapped_column(String(500))
    issue_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    event_registration_id: Mapped[int | None] = mapped_column(ForeignKey('event_registrations.id', ondelete='SET NULL'), nullable=True, index=True)
    member_id: Mapped[int | None] = mapped_column(ForeignKey('members.id', ondelete='SET NULL'), nullable=True, index=True)
    verification_token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    storage_path: Mapped[str] = mapped_column(String(1000))
    pdf_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class ContentWorkflow(Base):
    __tablename__ = 'content_workflows'
    __table_args__ = (UniqueConstraint('entity_type', 'entity_id', name='uq_content_workflow_entity'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(30), default='DRAFT', index=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    published_by: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
