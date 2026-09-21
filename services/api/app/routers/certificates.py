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

router = APIRouter(prefix='/certificates', tags=['certificates'])

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
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    cert = db.scalar(select(Certificate).where(Certificate.verification_token_hash == token_hash))
    if not cert:
        raise HTTPException(404, 'Certificate not found')
    return {'verified': True, 'certificate_no': cert.certificate_no, 'recipient_name': cert.recipient_name, 'title_bn': cert.title_bn, 'issue_date': cert.issue_date}

@router.get('/{certificate_no}/download')
def download_certificate(certificate_no: str, _: User = Depends(current_user), db: Session = Depends(get_db)):
    cert = db.scalar(select(Certificate).where(Certificate.certificate_no == certificate_no))
    if not cert or not cert.pdf_path:
        raise HTTPException(404, 'Certificate file not found')
    path = Path(cert.pdf_path).resolve()
    if not path.exists() or not path.is_file():
        raise HTTPException(404, 'Certificate file not found')
    return FileResponse(path, media_type='application/pdf', filename=f'{certificate_no}.pdf')
