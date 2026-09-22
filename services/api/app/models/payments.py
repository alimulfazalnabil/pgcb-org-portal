import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum, Boolean, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base

JSON_VARIANT = JSON().with_variant(JSONB, "postgresql")

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

class PaymentProviderType(str, enum.Enum):
    MANUAL = "MANUAL"
    TEST = "TEST"
    BKASH = "BKASH"
    NAGAD = "NAGAD"
    SSLCOMMERZ = "SSLCOMMERZ"

class PaymentTransaction(Base):
    __tablename__ = "gateway_payment_transactions"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="SET NULL"), nullable=True)
    
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="BDT")
    
    provider = Column(Enum(PaymentProviderType), nullable=False)
    provider_transaction_id = Column(String, unique=True, index=True, nullable=True)
    
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    reference = Column(String, index=True, nullable=True) # E.g., Membership Year or Event ID
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class PaymentWebhook(Base):
    __tablename__ = "payment_webhooks"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(Enum(PaymentProviderType), nullable=False)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("gateway_payment_transactions.id"), nullable=True)
    
    payload = Column(JSON_VARIANT, nullable=False) # Store the raw payload for audit/replay
    is_processed = Column(Boolean, default=False)
    
    received_at = Column(DateTime, default=datetime.utcnow)
