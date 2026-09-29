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
    name_bn: Mapped[str] = mapped_column(String(200), index=True)
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
    membership_type: Mapped[str] = mapped_column(String(50), default='GENERAL', index=True)
    application_no: Mapped[str | None] = mapped_column(String(60), unique=True, nullable=True, index=True)
    designation_bn: Mapped[str | None] = mapped_column(String(200), nullable=True)
    designation_en: Mapped[str | None] = mapped_column(String(200), nullable=True)
    employee_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    diploma_institution: Mapped[str | None] = mapped_column(String(250), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nid_number: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    date_of_birth: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    permanent_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    circle_id: Mapped[int | None] = mapped_column(ForeignKey('circles.id'), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default='PENDING', index=True)
    application_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    issue_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    validity_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
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
    membership_plan_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default='BDT')
    provider: Mapped[str] = mapped_column(String(40), default='MANUAL')
    transaction_ref: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True, index=True)
    provider_transaction_id_col: Mapped[str | None] = mapped_column('provider_transaction_id', String(160), unique=True, nullable=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(180), unique=True, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default='PENDING', index=True)
    provider_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def transaction_id(self) -> str | None:
        return self.transaction_ref

    @transaction_id.setter
    def transaction_id(self, val: str | None):
        self.transaction_ref = val

    @property
    def payment_method(self) -> str:
        return self.provider

    @payment_method.setter
    def payment_method(self, val: str):
        self.provider = val

    @property
    def provider_transaction_id(self) -> str | None:
        if self.provider_transaction_id_col:
            return self.provider_transaction_id_col
        if self.provider_payload and isinstance(self.provider_payload, dict):
            return self.provider_payload.get('trxID') or self.provider_payload.get('issuer_trx_id') or self.provider_payload.get('challan_no')
        return None

    @provider_transaction_id.setter
    def provider_transaction_id(self, val: str | None):
        self.provider_transaction_id_col = val


    @property
    def completed_at(self) -> datetime | None:
        return self.updated_at if self.status in ('PAID', 'SUCCESS', 'COMPLETED') else None

    @property
    def receipt_no(self) -> str | None:
        if self.provider_payload and isinstance(self.provider_payload, dict) and self.provider_payload.get('receipt_no'):
            return str(self.provider_payload['receipt_no'])
        if self.status in ('PAID', 'SUCCESS', 'COMPLETED') and self.id:
            year = (self.updated_at or self.created_at or datetime.utcnow()).year
            return f'PGCB-RCP-{year}-{int(self.id):06d}'
        return None

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

    @property
    def certificate_number(self) -> str:
        return self.certificate_no

    @certificate_number.setter
    def certificate_number(self, val: str):
        self.certificate_no = val

    @property
    def token(self) -> str:
        return getattr(self, '_raw_token', self.certificate_no)

    @token.setter
    def token(self, val: str):
        self._raw_token = val

    @property
    def status(self) -> str:
        return getattr(self, '_transient_status', 'ISSUED')

    @status.setter
    def status(self, val: str):
        self._transient_status = val

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


class Notice(Base):
    __tablename__ = 'notices'
    id: Mapped[int] = mapped_column(primary_key=True)
    title_bn: Mapped[str] = mapped_column(String(500), index=True)
    title_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_bn: Mapped[str] = mapped_column(Text)
    content_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default='NORMAL', index=True)  # NORMAL, IMPORTANT, URGENT
    category: Mapped[str] = mapped_column(String(60), default='GENERAL', index=True)
    attachment_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[int] = mapped_column(primary_key=True)
    title_bn: Mapped[str] = mapped_column(String(500), index=True)
    title_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(String(60), default='POLICIES', index=True)  # POLICIES, REPORTS, FORMS, GUIDELINES, ANNUAL_REPORTS, MEETINGS
    description_bn: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(String(1000))
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    version: Mapped[str] = mapped_column(String(30), default='1.0')
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class News(Base):
    __tablename__ = 'news_articles'
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    title_bn: Mapped[str] = mapped_column(String(500), index=True)
    title_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary_bn: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_bn: Mapped[str] = mapped_column(Text)
    content_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(80), default='GENERAL', index=True)
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    gallery_urls: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    author_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default='DRAFT', index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    meta_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    seo_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    og_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    robots: Mapped[str] = mapped_column(String(60), default='index,follow')
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContentRevision(Base):
    __tablename__ = 'content_revisions'
    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default='DRAFT', index=True)
    title_bn: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    change_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    changed_by: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    published_by: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    @property
    def version_number(self) -> int:
        return self.version_no

    @version_number.setter
    def version_number(self, val: int) -> None:
        self.version_no = val

    @property
    def workflow_status(self) -> str:
        return self.status

    @workflow_status.setter
    def workflow_status(self, val: str) -> None:
        self.status = val

    @property
    def snapshot(self) -> str | None:
        return self.content_snapshot

    @snapshot.setter
    def snapshot(self, val: object) -> None:
        import json
        self.content_snapshot = json.dumps(val, ensure_ascii=False, default=str) if isinstance(val, dict) else (str(val) if val is not None else None)

    @property
    def change_summary(self) -> str | None:
        return self.change_note

    @change_summary.setter
    def change_summary(self, val: str | None) -> None:
        self.change_note = val


class Announcement(Base):
    __tablename__ = 'announcements'
    id: Mapped[int] = mapped_column(primary_key=True)
    title_bn: Mapped[str] = mapped_column(String(500), index=True)
    title_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body_bn: Mapped[str] = mapped_column(Text)
    body_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_scope: Mapped[str] = mapped_column(String(40), default='ALL_MEMBERS', index=True)  # ALL_MEMBERS, CIRCLE, STATUS, ADMINS, COMMITTEE
    target_circle_id: Mapped[int | None] = mapped_column(ForeignKey('circles.id', ondelete='SET NULL'), nullable=True, index=True)
    target_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(60), nullable=True)
    channels: Mapped[str | None] = mapped_column(String(160), default='IN_APP')
    priority: Mapped[str] = mapped_column(String(20), default='NORMAL', index=True)
    is_banner: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    recipients_count: Mapped[int] = mapped_column(Integer, default=0)
    deliveries_count: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, nullable=True, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SEOMetadata(Base):
    __tablename__ = 'seo_metadata'
    __table_args__ = (UniqueConstraint('entity_type', 'entity_id', name='uq_seo_metadata_entity'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    slug: Mapped[str | None] = mapped_column(String(240), nullable=True, index=True)
    meta_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    seo_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    og_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    robots: Mapped[str] = mapped_column(String(60), default='index,follow')
    schema_type: Mapped[str] = mapped_column(String(80), default='WebPage')
    structured_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContactInquiryMeta(Base):
    __tablename__ = 'contact_inquiry_meta'
    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey('contact_messages.id', ondelete='CASCADE'), unique=True, index=True)
    ticket_no: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default='NEW', index=True)  # NEW, ASSIGNED, IN_PROGRESS, WAITING, RESOLVED, CLOSED
    assigned_to: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_by: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeDocument(Base):
    __tablename__ = 'knowledge_documents'
    id: Mapped[int] = mapped_column(primary_key=True)
    title_bn: Mapped[str] = mapped_column(String(500), index=True)
    title_en: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(80), default='MEMBERSHIP_GUIDELINES', index=True)
    version: Mapped[str] = mapped_column(String(40), default='2026.1', index=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    supersedes_id: Mapped[int | None] = mapped_column(ForeignKey('knowledge_documents.id', ondelete='SET NULL'), nullable=True)
    superseded_by_id: Mapped[int | None] = mapped_column(ForeignKey('knowledge_documents.id', ondelete='SET NULL'), nullable=True)
    publication_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    effective_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), default='PGCB Secretariat', nullable=True)
    approval_status: Mapped[str] = mapped_column(String(30), default='PUBLISHED', index=True)  # DRAFT, REVIEW, APPROVED, PUBLISHED, SUPERSEDED, ARCHIVED
    source_type: Mapped[str] = mapped_column(String(40), default='PDF')  # PDF, DOCX, TEXT, DOCUMENT, NOTICE, CIRCULAR
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    access_level: Mapped[str] = mapped_column(String(40), default='PUBLIC', index=True)  # PUBLIC, MEMBER, CIRCLE_ADMIN, CENTRAL_ADMIN, SUPER_ADMIN
    circle_id: Mapped[int | None] = mapped_column(ForeignKey('circles.id', ondelete='SET NULL'), nullable=True, index=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    cleaned_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeChunk(Base):
    __tablename__ = 'knowledge_chunks'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('knowledge_documents.id', ondelete='CASCADE'), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    section_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    page_number: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text)
    tokens_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class KnowledgeFAQ(Base):
    __tablename__ = 'knowledge_faqs'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey('knowledge_documents.id', ondelete='SET NULL'), nullable=True, index=True)
    question_bn: Mapped[str] = mapped_column(String(500), index=True)
    question_en: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    answer_bn: Mapped[str] = mapped_column(Text)
    answer_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(80), default='MEMBERSHIP_GUIDELINES', index=True)
    section_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    page_ref: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='DRAFT', index=True)  # DRAFT, REVIEW, APPROVED, PUBLISHED, ARCHIVED
    approved_by: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AIQueryLog(Base):
    __tablename__ = 'ai_query_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    user_role: Mapped[str] = mapped_column(String(60), default='PUBLIC', index=True)
    assistant_mode: Mapped[str] = mapped_column(String(30), default='PUBLIC', index=True)  # PUBLIC, MEMBER, ADMIN
    question: Mapped[str] = mapped_column(Text)
    question_category: Mapped[str] = mapped_column(String(80), default='GENERAL', index=True)
    answer_preview: Mapped[str | None] = mapped_column(String(500), nullable=True)
    confidence: Mapped[float] = mapped_column(default=0.0)
    unanswered: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    security_flagged: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    documents_searched: Mapped[int] = mapped_column(Integer, default=0)
    sources_cited: Mapped[str | None] = mapped_column(Text, nullable=True)
    tools_called: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    @property
    def mode(self) -> str:
        return self.assistant_mode

    @property
    def intent(self) -> str:
        return self.question_category

    @property
    def tools_used(self) -> str | None:
        return self.tools_called

    @property
    def documents_used(self) -> str | None:
        return self.sources_cited

    @property
    def response(self) -> str | None:
        return self.answer_preview

    @property
    def blocked(self) -> bool:
        return self.security_flagged

    @property
    def latency(self) -> int:
        return self.response_time_ms


class AIConversation(Base):
    __tablename__ = 'ai_conversations'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    session_id: Mapped[str] = mapped_column(String(120), default='', index=True)
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    mode: Mapped[str] = mapped_column(String(30), default='PUBLIC', index=True)
    language: Mapped[str] = mapped_column(String(10), default='bn')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AIMessage(Base):
    __tablename__ = 'ai_messages'
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey('ai_conversations.id', ondelete='CASCADE'), index=True)
    role: Mapped[str] = mapped_column(String(20), default='user', index=True)  # user, assistant
    content: Mapped[str] = mapped_column(Text)
    content_bn: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    intent: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    confidence_state: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sources: Mapped[str | None] = mapped_column(Text, nullable=True)
    tools_used: Mapped[str | None] = mapped_column(Text, nullable=True)
    actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)



class Role(Base, TimestampMixin):
    __tablename__ = 'roles'
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name_bn: Mapped[str] = mapped_column(String(120))
    name_en: Mapped[str] = mapped_column(String(120))
    permissions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class Permission(Base, TimestampMixin):
    __tablename__ = 'permissions'
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    module: Mapped[str] = mapped_column(String(60), default='CORE', index=True)
    description_en: Mapped[str | None] = mapped_column(String(300), nullable=True)
    description_bn: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class GridCircle(Base, TimestampMixin):
    __tablename__ = 'grid_circles'
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name_bn: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name_en: Mapped[str] = mapped_column(String(120), index=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class Membership(Base, TimestampMixin):
    __tablename__ = 'memberships'
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey('members.id', ondelete='CASCADE'), index=True)
    membership_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    membership_type: Mapped[str] = mapped_column(String(50), default='GENERAL', index=True)
    status: Mapped[str] = mapped_column(String(30), default='ACTIVE', index=True)
    issue_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    validity_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class MembershipApplication(Base, TimestampMixin):
    __tablename__ = 'membership_applications'
    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey('members.id', ondelete='CASCADE'), index=True)
    application_no: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    membership_type: Mapped[str] = mapped_column(String(50), default='GENERAL', index=True)
    circle_id: Mapped[int | None] = mapped_column(ForeignKey('circles.id', ondelete='SET NULL'), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default='PENDING', index=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class ApplicationReview(Base, TimestampMixin):
    __tablename__ = 'application_reviews'
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey('membership_applications.id', ondelete='CASCADE'), nullable=True, index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey('members.id', ondelete='CASCADE'), index=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(40), index=True)
    previous_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class Payment(Base, TimestampMixin):
    __tablename__ = 'payments'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    member_id: Mapped[int | None] = mapped_column(ForeignKey('members.id', ondelete='SET NULL'), nullable=True, index=True)
    transaction_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    receipt_no: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), default='BKASH', index=True)
    purpose: Mapped[str] = mapped_column(String(50), default='MEMBERSHIP', index=True)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(10), default='BDT')
    status: Mapped[str] = mapped_column(String(30), default='PENDING', index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class NewsEntry(Base, TimestampMixin):
    __tablename__ = 'news'
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    title_bn: Mapped[str] = mapped_column(String(500), index=True)
    title_en: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary_bn: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_bn: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80), default='GENERAL', index=True)
    status: Mapped[str] = mapped_column(String(30), default='PUBLISHED', index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, nullable=True, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class NotificationTemplate(Base, TimestampMixin):
    __tablename__ = 'notification_templates'
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    channel: Mapped[str] = mapped_column(String(30), default='EMAIL', index=True)
    subject_bn: Mapped[str] = mapped_column(String(300))
    subject_en: Mapped[str | None] = mapped_column(String(300), nullable=True)
    body_bn: Mapped[str] = mapped_column(Text)
    body_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

