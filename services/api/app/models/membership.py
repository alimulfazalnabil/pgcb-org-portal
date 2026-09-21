import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base

class ApplicationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    DOCUMENT_VERIFICATION = "DOCUMENT_VERIFICATION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"

class DocumentType(str, enum.Enum):
    NID = "NID"
    CERTIFICATE = "CERTIFICATE"
    PHOTO = "PHOTO"
    SIGNATURE = "SIGNATURE"
    OTHER = "OTHER"

class Member(Base):
    __tablename__ = "members"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=True)
    member_id = Column(String, unique=True, index=True, nullable=True) # Generated upon approval
    
    # Personal Information
    full_name_en = Column(String, nullable=False)
    full_name_bn = Column(String, nullable=False)
    father_name = Column(String)
    mother_name = Column(String)
    date_of_birth = Column(Date)
    gender = Column(String(20))
    national_id = Column(String, unique=True, index=True)
    
    # Professional Information
    employee_id = Column(String, unique=True, index=True)
    designation = Column(String)
    organization = Column(String, default="PGCB")
    department = Column(String)
    grid_circle_id = Column(UUID(as_uuid=True), ForeignKey("circles.id"))
    
    # Educational Information
    educational_institution = Column(String)
    graduation_year = Column(String(4))
    
    # Contact Information
    current_address = Column(Text)
    permanent_address = Column(Text)
    phone = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    
    # Status & Audit
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.DRAFT, index=True)
    is_active = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("MemberDocument", back_populates="member", cascade="all, delete-orphan")

class MemberDocument(Base):
    __tablename__ = "member_documents"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"))
    document_type = Column(Enum(DocumentType), nullable=False)
    file_url = Column(String, nullable=False) # S3 Path
    file_name = Column(String)
    mime_type = Column(String)
    is_verified = Column(Boolean, default=False)
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    member = relationship("Member", back_populates="documents")
