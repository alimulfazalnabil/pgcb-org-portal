from sqlalchemy.orm import Session
from fastapi import Request
from app.models.core import User
from app.db.session import Base
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime

JSON_VARIANT = JSON().with_variant(JSONB, "postgresql")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True) # Nullable for anonymous actions (e.g. failed login)
    role = Column(String, nullable=True)
    
    action = Column(String, index=True, nullable=False) # e.g., "APPROVE_MEMBER", "PUBLISH_CIRCULAR"
    entity = Column(String, index=True) # e.g., "MEMBER", "CIRCULAR"
    entity_id = Column(String, index=True, nullable=True)
    
    old_value = Column(JSON_VARIANT, nullable=True)
    new_value = Column(JSON_VARIANT, nullable=True)
    
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

def log_audit_action(
    db: Session,
    request: Request | None = None,
    action: str = "ACTION",
    entity: str = "SYSTEM",
    entity_id: str | int | None = None,
    user: User | None = None,
    old_value: dict | None = None,
    new_value: dict | None = None
):
    """Centralized service to record security and administrative events."""
    
    # Strip sensitive data (passwords, tokens) before logging
    if old_value and isinstance(old_value, dict):
        old_value = {k: v for k, v in old_value.items() if k not in ("password", "password_hash", "token", "secret", "mfa_secret")}
    if new_value and isinstance(new_value, dict):
        new_value = {k: v for k, v in new_value.items() if k not in ("password", "password_hash", "token", "secret", "mfa_secret")}

    role_str = "PUBLIC"
    if user:
        if hasattr(user, 'roles') and user.roles:
            role_str = ",".join([getattr(r, 'name', str(r)) for r in user.roles])
        elif hasattr(user, 'role') and user.role:
            role_str = str(user.role)

    ip_address = None
    user_agent = None
    if request:
        if getattr(request, 'client', None):
            ip_address = request.client.host
        if hasattr(request, 'headers'):
            user_agent = request.headers.get("user-agent")

    log_entry = AuditLog(
        user_id=getattr(user, 'id', None),
        role=role_str,
        action=action,
        entity=entity,
        entity_id=str(entity_id) if entity_id is not None else None,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.utcnow()
    )
    
    db.add(log_entry)
    db.commit()
