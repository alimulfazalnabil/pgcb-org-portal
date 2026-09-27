"""
Institutional Certificate Lifecycle Domain Service for PGCB Organization Portal.
Handles certificate numbering, generation, issuance, public privacy-safe verification, and revocation.
"""

from datetime import datetime
import hashlib
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Certificate, User, Member
from app.services import audit, notify
from app.services.email import EmailService


class CertificateService:
    _revocations: dict[str, str] = {}

    @classmethod
    def issue_certificate(
        cls,
        db: Session,
        admin_user: User,
        recipient_user_id: int,
        certificate_type: str = 'MEMBERSHIP',
        recipient_name: str | None = None,
        event_id: int | None = None,
        ip: str | None = None,
    ) -> Certificate:
        user = db.get(User, recipient_user_id)
        if not user:
            raise HTTPException(404, 'Recipient user not found')

        name = recipient_name or user.name_bn or user.name_en or 'প্রকৌশলী'
        token = uuid4().hex[:12].upper()
        year = datetime.utcnow().year
        cert_number = f"PGCB-CERT-{year}-{token}"
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        member = db.scalar(select(Member).where(Member.user_id == user.id))

        cert = Certificate(
            certificate_no=cert_number,
            recipient_name=name,
            title_bn=f"{certificate_type} Certificate",
            event_registration_id=event_id,
            member_id=member.id if member else None,
            verification_token_hash=token_hash,
            storage_path=f"/storage/certificates/{cert_number}.png",
            pdf_path=f"/storage/certificates/{cert_number}.pdf",
            issue_date=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        cert._raw_token = token
        cert._transient_status = 'ISSUED'
        db.add(cert)
        db.flush()

        audit(db, admin_user, 'ISSUE_CERTIFICATE', 'CERTIFICATE', cert.id, ip)

        notify(
            db,
            user.id,
            'নতুন সনদপত্র ইস্যু করা হয়েছে',
            f'আপনার প্রাতিষ্ঠানিক সনদপত্র ({cert.certificate_no}) সফলভাবে ইস্যু করা হয়েছে।',
            'CERTIFICATE',
        )

        EmailService.send_certificate_issued(
            to_email=user.email,
            recipient_name=name,
            certificate_type=certificate_type,
            certificate_number=cert.certificate_no,
            verification_url=f"/verify?cert_id={token}",
        )

        db.commit()
        db.refresh(cert)
        cert._raw_token = token
        cert._transient_status = 'ISSUED'
        return cert

    @classmethod
    def verify_public(cls, db: Session, token_or_number: str) -> dict:
        token_hash = hashlib.sha256(token_or_number.strip().encode()).hexdigest()
        cert = db.scalar(
            select(Certificate).where(
                (Certificate.verification_token_hash == token_hash) |
                (Certificate.certificate_no == token_or_number.strip())
            )
        )
        if not cert:
            reason = cls._revocations.get(token_or_number.strip(), 'সনদপত্রটি বাতিল করা হয়েছে অথবা অবৈধ।')
            return {
                'valid': False,
                'message': 'সনদপত্রটি খুঁজে পাওয়া যায়নি (Certificate not found).',
                'revoked': True,
                'revocation_reason': reason,
            }

        # Privacy-safe response: Only public institutional fields, NO private email, phone, or address
        return {
            'valid': True,
            'certificate_number': cert.certificate_no,
            'status': 'ISSUED',
            'recipient_name': cert.recipient_name,
            'title_bn': cert.title_bn,
            'issue_date': cert.issue_date.strftime('%Y-%m-%d') if cert.issue_date else None,
            'revoked': False,
        }

    @classmethod
    def revoke_certificate(
        cls,
        db: Session,
        admin_user: User,
        cert_id_or_token: str | int,
        reason: str,
        ip: str | None = None,
    ) -> Certificate:
        if isinstance(cert_id_or_token, int) or (isinstance(cert_id_or_token, str) and cert_id_or_token.isdigit()):
            cert = db.get(Certificate, int(cert_id_or_token))
        else:
            token_hash = hashlib.sha256(cert_id_or_token.strip().encode()).hexdigest()
            cert = db.scalar(
                select(Certificate).where(
                    (Certificate.certificate_no == cert_id_or_token.strip()) |
                    (Certificate.verification_token_hash == token_hash)
                )
            )

        if not cert:
            raise HTTPException(404, 'Certificate not found')

        audit(db, admin_user, 'REVOKE_CERTIFICATE', 'CERTIFICATE', cert.id, ip)

        cls._revocations[str(cert.id)] = reason
        cls._revocations[cert.certificate_no] = reason
        if hasattr(cert, '_raw_token') and cert._raw_token:
            cls._revocations[cert._raw_token] = reason
        if isinstance(cert_id_or_token, str):
            cls._revocations[cert_id_or_token.strip()] = reason

        notify_user_id = None
        if cert.member_id:
            m = db.get(Member, cert.member_id)
            if m:
                notify_user_id = m.user_id
        if notify_user_id:
            notify(
                db,
                notify_user_id,
                'সনদপত্র প্রত্যাহার করা হয়েছে',
                f'আপনার সনদপত্র নং {cert.certificate_no} বাতিল করা হয়েছে। কারণ: {reason}',
                'CERTIFICATE',
            )

        # Retain references before delete
        cert_copy = Certificate(
            certificate_no=cert.certificate_no,
            recipient_name=cert.recipient_name,
            title_bn=cert.title_bn,
            issue_date=cert.issue_date,
            verification_token_hash=cert.verification_token_hash,
            storage_path=cert.storage_path,
            pdf_path=cert.pdf_path,
            created_at=cert.created_at,
        )
        cert_copy.id = cert.id
        cert_copy._raw_token = getattr(cert, '_raw_token', cert.certificate_no)
        cert_copy._transient_status = 'REVOKED'

        db.delete(cert)
        db.commit()
        return cert_copy
