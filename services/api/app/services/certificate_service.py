"""
Institutional Certificate Lifecycle Domain Service for PGCB Organization Portal.
Handles certificate numbering, generation, issuance, public privacy-safe verification, and revocation.
"""

from datetime import datetime
import hashlib
from pathlib import Path
from uuid import uuid4
from PIL import Image, ImageDraw, ImageFont
import qrcode
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.config import settings
from app.models import Certificate, User, Member
from app.services import BASE_STORAGE, audit, notify
from app.services.email import EmailService


def _cert_font(size: int, bold: bool = False):
    candidates = (
        [
            'C:/Windows/Fonts/arialbd.ttf',
            'C:/Windows/Fonts/segoeuib.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf',
        ]
        if bold
        else [
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/segoeui.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
        ]
    )
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


class CertificateService:
    _revocations: dict[str, str] = {}

    @classmethod
    def render_certificate_files(cls, cert: Certificate, verify_token: str | None = None) -> tuple[Path, Path]:
        folder = BASE_STORAGE / 'certificates'
        folder.mkdir(parents=True, exist_ok=True)
        safe_no = "".join(c for c in (cert.certificate_no or 'PGCB-CERT') if c.isalnum() or c in ('-', '_'))
        png_path = folder / f'{safe_no}.png'
        pdf_path = folder / f'{safe_no}.pdf'

        canvas = Image.new('RGB', (1600, 1120), '#FFFFFF')
        draw = ImageDraw.Draw(canvas)

        # Institutional border & header
        draw.rectangle((36, 36, 1564, 1084), outline='#0B132B', width=8)
        draw.rectangle((56, 56, 1544, 1064), outline='#F59E0B', width=3)
        draw.rectangle((56, 56, 1544, 210), fill='#0B132B')

        draw.text((800, 110), 'POWER GRID DIPLOMA ENGINEERS ASSOCIATION (PGDEA)', anchor='mm', font=_cert_font(34, bold=True), fill='#F59E0B')
        draw.text((800, 162), 'POWER GRID COMPANY OF BANGLADESH PLC • CENTRAL EXECUTIVE COUNCIL', anchor='mm', font=_cert_font(20, bold=False), fill='#93C5FD')

        is_membership = 'MEMBERSHIP' in (cert.title_bn or '').upper()
        heading = 'OFFICIAL CERTIFICATE OF MEMBERSHIP' if is_membership else 'OFFICIAL CERTIFICATE OF ACHIEVEMENT'
        draw.text((800, 300), heading, anchor='mm', font=_cert_font(46, bold=True), fill='#0B132B')
        draw.text((800, 380), 'This institutional credential is proudly awarded to', anchor='mm', font=_cert_font(26), fill='#475569')

        recipient_display = cert.recipient_name or 'PGCB Engineer'
        draw.text((800, 470), recipient_display, anchor='mm', font=_cert_font(52, bold=True), fill='#047857')
        draw.line((400, 515, 1200, 515), fill='#CBD5E1', width=2)

        subtitle = (
            'In recognition of active institutional standing as a verified member of PGDEA / PGCB.'
            if is_membership
            else f'In recognition of successful completion & participation: {cert.title_bn}'
        )
        draw.text((800, 580), subtitle, anchor='mm', font=_cert_font(24), fill='#334155')

        issue_dt = cert.issue_date or datetime.utcnow()
        issue_str = issue_dt.strftime('%d %B %Y') if hasattr(issue_dt, 'strftime') else str(issue_dt)[:10]
        draw.text((140, 760), f'Certificate No: {cert.certificate_no}', font=_cert_font(24, bold=True), fill='#0B132B')
        draw.text((140, 805), f'Issue Date: {issue_str}', font=_cert_font(22), fill='#334155')
        draw.text((140, 848), 'Issuer: PGDEA Central Secretariat, Dhaka', font=_cert_font(22), fill='#334155')
        draw.text((140, 890), 'Status: ISSUED & CRYPTOGRAPHICALLY VERIFIABLE', font=_cert_font(20, bold=True), fill='#059669')

        # QR Verification Code
        qr_target = f"{settings.frontend_url.rstrip('/')}/certificates/verify?cert={verify_token or cert.certificate_no}"
        qr = qrcode.QRCode(box_size=5, border=2)
        qr.add_data(qr_target)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color='#0B132B', back_color='#FFFFFF').convert('RGB').resize((200, 200))
        canvas.paste(qr_img, (1260, 730))
        draw.text((1360, 950), 'SCAN TO VERIFY', anchor='mm', font=_cert_font(16, bold=True), fill='#0B132B')

        canvas.save(png_path, format='PNG', optimize=True)
        canvas.save(pdf_path, format='PDF', resolution=150.0)
        cert.storage_path = str(png_path)
        cert.pdf_path = str(pdf_path)
        return png_path, pdf_path

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

        name = recipient_name or user.name_en or user.name_bn or 'প্রকৌশলী'
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
        cls.render_certificate_files(cert, verify_token=token)
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

        is_revoked = (
            cert.id in cls._revocations
            or str(cert.id) in cls._revocations
            or cert.certificate_no in cls._revocations
        )
        if is_revoked:
            reason = (
                cls._revocations.get(cert.certificate_no)
                or cls._revocations.get(str(cert.id))
                or cls._revocations.get(cert.id)  # type: ignore[arg-type]
                or 'সনদপত্রটি প্রাতিষ্ঠানিক সিদ্ধান্তে প্রত্যাহার করা হয়েছে।'
            )
            return {
                'valid': False,
                'certificate_number': cert.certificate_no,
                'status': 'REVOKED',
                'recipient_name': cert.recipient_name,
                'title_bn': cert.title_bn,
                'issue_date': cert.issue_date.strftime('%Y-%m-%d') if cert.issue_date else None,
                'issuer': 'PGDEA Central Secretariat, Dhaka',
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
            'issuer': 'PGDEA Central Secretariat, Dhaka',
            'revoked': False,
            'revocation_reason': None,
        }

    @classmethod
    def serialize_certificate(cls, cert: Certificate) -> dict:
        rev_reason = (
            cls._revocations.get(cert.certificate_no)
            or cls._revocations.get(str(cert.id))
            or cls._revocations.get(cert.id)  # type: ignore[arg-type]
        )
        is_revoked = bool(rev_reason) or getattr(cert, '_transient_status', None) == 'REVOKED'
        is_membership = 'MEMBERSHIP' in (cert.title_bn or '').upper() and not cert.event_registration_id
        issue_dt = cert.issue_date or cert.created_at or datetime.utcnow()
        issue_str = issue_dt.strftime('%Y-%m-%d') if hasattr(issue_dt, 'strftime') else str(issue_dt)[:10]
        issue_year = issue_dt.year if hasattr(issue_dt, 'year') else datetime.utcnow().year
        return {
            'id': cert.id,
            'certificate_no': cert.certificate_no,
            'certificate_number': cert.certificate_no,
            'recipient_name': cert.recipient_name,
            'title_bn': cert.title_bn,
            'category': 'MEMBERSHIP' if is_membership else 'TRAINING_EVENT',
            'category_label_bn': 'সদস্যপদ সনদপত্র' if is_membership else 'প্রশিক্ষণ / ইভেন্ট সনদপত্র',
            'issue_date': issue_str,
            'issued_year': issue_year,
            'issuer': 'PGDEA Central Secretariat, Dhaka',
            'issuer_bn': 'কেন্দ্রীয় কার্যনির্বাহী পরিষদ, পিজিডিইএ',
            'status': 'REVOKED' if is_revoked else 'ISSUED',
            'revoked': is_revoked,
            'revocation_reason': rev_reason,
            'event_registration_id': cert.event_registration_id,
            'member_id': cert.member_id,
            'preview_url': f'/api/v1/certificates/{cert.certificate_no}/preview',
            'download_url': f'/api/v1/certificates/{cert.certificate_no}/download',
            'verify_url': f'/certificates/verify?cert={cert.certificate_no}',
            'api_verify_url': f'/api/v1/certificates/verify/{cert.certificate_no}',
        }

    @classmethod
    def ensure_member_wallet_certificates(cls, db: Session, user: User, member: Member) -> list[dict]:
        from app.models import EventRegistration

        reg_ids = list(
            db.scalars(select(EventRegistration.id).where(EventRegistration.user_id == user.id)).all()
        )
        cond = Certificate.member_id == member.id
        if reg_ids:
            cond = (Certificate.member_id == member.id) | (Certificate.event_registration_id.in_(reg_ids))

        certs = list(
            db.scalars(select(Certificate).where(cond).order_by(Certificate.issue_date.desc())).all()
        )

        has_membership_cert = any(
            'MEMBERSHIP' in (c.title_bn or '').upper() and not c.event_registration_id for c in certs
        )
        if member.status == 'ACTIVE' and member.membership_id and not has_membership_cert:
            year = (member.issue_date or datetime.utcnow()).year
            clean_mid = "".join(ch for ch in member.membership_id if ch.isalnum())[-6:].upper()
            cert_no = f'PGCB-CERT-{year}-MEM{clean_mid}'
            if cert_no not in cls._revocations and not db.scalar(select(Certificate).where(Certificate.certificate_no == cert_no)):
                token_hash = hashlib.sha256(cert_no.encode()).hexdigest()
                cert = Certificate(
                    certificate_no=cert_no,
                    recipient_name=user.name_en or user.name_bn or 'PGCB Member',
                    title_bn='Membership Certificate (সদস্যপদ সনদপত্র)',
                    member_id=member.id,
                    verification_token_hash=token_hash,
                    storage_path=f'/storage/certificates/{cert_no}.png',
                    pdf_path=f'/storage/certificates/{cert_no}.pdf',
                    issue_date=member.issue_date or datetime.utcnow(),
                    created_at=datetime.utcnow(),
                )
                cls.render_certificate_files(cert, verify_token=cert_no)
                db.add(cert)
                db.commit()
                db.refresh(cert)
                certs.insert(0, cert)

        return [cls.serialize_certificate(c) for c in certs]

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

        cls._revocations[cert.id] = reason  # type: ignore[index]
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


_revoked_certs = CertificateService._revocations

