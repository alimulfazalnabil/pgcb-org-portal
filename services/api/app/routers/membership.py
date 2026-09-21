from datetime import datetime
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import current_user
from app.db.session import get_db
from app.models import Member, MemberDocument, Notification, User
from app.schemas.membership import ApplicationResponse, MemberDocumentResponse, MemberProfileUpdate
from app.services import ALLOWED_CONTENT_TYPES, ALLOWED_DOC_TYPES, audit, membership_dates, next_membership_id, notify
from app.services import BASE_STORAGE
from app.utils.storage import is_local_path, save_bytes

router = APIRouter(prefix='/member', tags=['membership'])


def get_member(user: User, db: Session) -> Member:
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    if not member:
        raise HTTPException(404, 'Member profile not found')
    return member


def response(member: Member) -> ApplicationResponse:
    return ApplicationResponse(
        id=member.id, membership_id=member.membership_id, status=member.status,
        designation_bn=member.designation_bn,
        circle_bn=member.circle.name_bn if member.circle else None,
        application_note=member.application_note,
        issue_date=member.issue_date, validity_date=member.validity_date,
    )


@router.get('/profile')
def profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = get_member(user, db)
    return {
        'id': m.id, 'name_bn': user.name_bn, 'name_en': user.name_en, 'email': user.email, 'phone': user.phone,
        'membership_id': m.membership_id, 'status': m.status, 'designation_bn': m.designation_bn, 'designation_en': m.designation_en,
        'employee_id': m.employee_id, 'diploma_institution': m.diploma_institution, 'graduation_year': m.graduation_year,
        'nid_number': m.nid_number, 'date_of_birth': m.date_of_birth, 'current_address': m.current_address,
        'permanent_address': m.permanent_address, 'circle_id': m.circle_id,
    }


@router.patch('/profile')
def update_profile(payload: MemberProfileUpdate, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = get_member(user, db)
    user.name_bn = payload.name_bn; user.name_en = payload.name_en; user.phone = payload.phone
    for field in ['designation_bn', 'designation_en', 'employee_id', 'diploma_institution', 'graduation_year', 'nid_number', 'date_of_birth', 'current_address', 'permanent_address', 'circle_id']:
        setattr(m, field, getattr(payload, field))
    audit(db, user, 'UPDATE_PROFILE', 'MEMBER', m.id, request.client.host if request.client else None)
    db.commit()
    return {'ok': True}


@router.post('/application', response_model=ApplicationResponse)
def submit_application(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = get_member(user, db)
    if m.status == 'ACTIVE':
        raise HTTPException(409, 'Membership is already active')
    m.status = 'SUBMITTED'
    m.application_note = 'Application submitted by member.'
    audit(db, user, 'SUBMIT_APPLICATION', 'MEMBER', m.id, request.client.host if request.client else None)
    officers = db.scalars(select(User).where(User.role.in_(['MEMBERSHIP_OFFICER', 'SUPER_ADMIN']), User.is_active == True)).all()
    for officer in officers:
        notify(db, officer.id, 'নতুন সদস্য আবেদন', f'{user.name_bn}-এর সদস্য আবেদন পর্যালোচনার জন্য জমা হয়েছে।', 'MEMBERSHIP')
    db.commit(); db.refresh(m)
    return response(m)


@router.get('/application', response_model=ApplicationResponse)
def get_application(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return response(get_member(user, db))


@router.post('/documents', response_model=MemberDocumentResponse)
def upload_document(request: Request, document_type: str, file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    if document_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(400, 'Invalid document type')
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, 'Only PDF and image documents are accepted')
    member = get_member(user, db)
    max_bytes = settings.max_upload_mb * 1024 * 1024
    content = file.file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(413, f'Maximum file size is {settings.max_upload_mb} MB')

    safe_name = (file.filename or 'upload.bin').replace('/', '_').replace('\\', '_').replace(' ', '_')
    unique_name = f'{datetime.utcnow().strftime("%Y%m%d%H%M%S%f")}_{safe_name}'
    try:
        stored = save_bytes(content, f'members/{member.id}', unique_name)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    doc = MemberDocument(
        member_id=member.id, document_type=document_type, filename=safe_name,
        storage_path=stored, content_type=file.content_type, review_status='PENDING'
    )
    db.add(doc)
    if document_type == 'PHOTO' and stored.startswith('http'):
        member.photo_url = stored
    audit(db, user, 'UPLOAD_DOCUMENT', 'MEMBER_DOCUMENT', member.id, request.client.host if request.client else None)
    db.commit(); db.refresh(doc)
    return MemberDocumentResponse(id=doc.id, document_type=doc.document_type, filename=doc.filename, review_status=doc.review_status, created_at=doc.created_at)


@router.get('/documents', response_model=list[MemberDocumentResponse])
def list_documents(user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = get_member(user, db)
    return [MemberDocumentResponse(id=d.id, document_type=d.document_type, filename=d.filename, review_status=d.review_status, created_at=d.created_at) for d in m.documents]


@router.get('/documents/{document_id}/download')
def download_document(document_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = get_member(user, db)
    doc = db.scalar(select(MemberDocument).where(MemberDocument.id == document_id, MemberDocument.member_id == m.id))
    if not doc or not is_local_path(doc.storage_path):
        raise HTTPException(404, 'Document not available')
    path = __import__('pathlib').Path(doc.storage_path).resolve()
    if not path.exists() or not path.is_file():
        raise HTTPException(404, 'Document not found')
    return FileResponse(path, media_type=doc.content_type or 'application/octet-stream', filename=doc.filename)


@router.get('/notifications')
def notifications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(30)).all()
    return [{'id': n.id, 'title_bn': n.title_bn, 'body_bn': n.body_bn, 'type': n.notification_type, 'read_at': n.read_at, 'created_at': n.created_at} for n in rows]


@router.post('/notifications/{notification_id}/read')
def mark_notification_read(notification_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    n = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    if not n:
        raise HTTPException(404, 'Notification not found')
    n.read_at = datetime.utcnow(); db.commit()
    return {'ok': True}
