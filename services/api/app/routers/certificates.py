from __future__ import annotations

import hashlib
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import current_user
from app.core.rbac import require_permission
from app.db.session import get_db
from app.models import Certificate, Event, EventRegistration, Member, User
from app.domain.certificates import generate_event_certificate
from app.services.certificate_service import CertificateService

router = APIRouter(prefix='/certificates', tags=['certificates'])


@router.get('/me')
def list_my_certificates(user: User = Depends(current_user), db: Session = Depends(get_db)):
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    if not member:
        raise HTTPException(404, 'Member profile not found')
    return CertificateService.ensure_member_wallet_certificates(db, user, member)


@router.post('/event-registrations/{registration_id}', dependencies=[Depends(require_permission('certificate.write'))])
def create_event_certificate(registration_id: int, db: Session = Depends(get_db)):
    registration = db.get(EventRegistration, registration_id)
    if not registration:
        raise HTTPException(404, 'Registration not found')
    if registration.attendance_status != 'CHECKED_IN':
        raise HTTPException(409, 'Participant must be checked in before certificate generation')
    event = db.get(Event, registration.event_id)
    if not event:
        raise HTTPException(404, 'Event not found')
    existing = db.scalar(select(Certificate).where(Certificate.event_registration_id == registration.id))
    if existing:
        return {'certificate_no': existing.certificate_no, 'already_exists': True}
    member = db.scalar(select(Member).where(Member.user_id == registration.user_id)) if registration.user_id else None
    cert, raw_token = generate_event_certificate(db, registration, event.title_bn, member)
    db.commit()
    return {'certificate_no': cert.certificate_no, 'verification_token': raw_token, 'download_url': f'/api/v1/certificates/{cert.certificate_no}/download'}


@router.get('/verify/{token}')
def verify_certificate(token: str, db: Session = Depends(get_db)):
    clean = token.strip()
    token_hash = hashlib.sha256(clean.encode()).hexdigest()
    cert = db.scalar(
        select(Certificate).where(
            (Certificate.verification_token_hash == token_hash)
            | (Certificate.certificate_no == clean)
        )
    )
    if not cert:
        rev_reason = CertificateService._revocations.get(clean)
        if rev_reason:
            return {
                'verified': False,
                'valid': False,
                'certificate_no': clean,
                'status': 'REVOKED',
                'revoked': True,
                'revocation_reason': rev_reason,
            }
        raise HTTPException(404, 'Certificate not found')

    serialized = CertificateService.serialize_certificate(cert)
    return {
        'verified': not serialized['revoked'],
        'valid': not serialized['revoked'],
        'certificate_no': cert.certificate_no,
        'certificate_number': cert.certificate_no,
        'recipient_name': cert.recipient_name,
        'title_bn': cert.title_bn,
        'issue_date': cert.issue_date,
        'issuer': serialized['issuer'],
        'issuer_bn': serialized['issuer_bn'],
        'status': serialized['status'],
        'revoked': serialized['revoked'],
        'revocation_reason': serialized['revocation_reason'],
    }


@router.get('/{certificate_no}.png')
@router.get('/{certificate_no}/preview')
def preview_certificate(certificate_no: str, db: Session = Depends(get_db)):
    clean_no = certificate_no[:-4] if certificate_no.lower().endswith('.png') else certificate_no
    cert = db.scalar(select(Certificate).where(Certificate.certificate_no == clean_no))
    if not cert:
        raise HTTPException(404, 'Certificate not found')
    png_path = Path(cert.storage_path).resolve() if cert.storage_path else None
    if not png_path or not png_path.exists() or not png_path.is_file():
        png_path, _ = CertificateService.render_certificate_files(cert)
        db.commit()
    return FileResponse(png_path, media_type='image/png', filename=f'{clean_no}.png')


@router.get('/{certificate_no}.pdf')
@router.get('/{certificate_no}/download')
def download_certificate(certificate_no: str, db: Session = Depends(get_db)):
    clean_no = certificate_no[:-4] if certificate_no.lower().endswith('.pdf') else certificate_no
    cert = db.scalar(select(Certificate).where(Certificate.certificate_no == clean_no))
    if not cert:
        raise HTTPException(404, 'Certificate file not found')
    path = Path(cert.pdf_path).resolve() if cert.pdf_path else None
    if not path or not path.exists() or not path.is_file():
        _, path = CertificateService.render_certificate_files(cert)
        db.commit()
    return FileResponse(path, media_type='application/pdf', filename=f'{clean_no}.pdf')

