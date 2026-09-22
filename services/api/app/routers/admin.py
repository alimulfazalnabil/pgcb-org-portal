from datetime import datetime
from io import StringIO
import csv
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.rbac import require_permission
from app.core.security import hash_password
from app.core.mfa import generate_secret, otpauth_uri, verify_totp, encrypt_secret, decrypt_secret
from app.db.session import get_db
from app.models import (
    AuditLog,
    Circle,
    Circular,
    CommitteeMember,
    ContactMessage,
    Event,
    EventRegistration,
    Journal,
    Member,
    MemberDocument,
    MediaAsset,
    PaymentTransaction,
    Certificate,
    NotificationDelivery,
    SiteSetting,
    User,
)
from app.schemas.admin import AdminUserCreate, AdminUserUpdate, MessageStatusUpdate
from app.schemas.events import CheckInRequest, RegistrationStatusUpdate, PaymentStatusUpdate
from app.schemas.notifications import BroadcastNotification
from app.schemas.content import (
    CircleCreate,
    CircularCreate,
    CircularResponse,
    CommitteeMemberCreate,
    EventCreate,
    JournalCreate,
    MediaCreate,
    SiteSettingUpdate,
)
from app.services import MAX_UPLOAD_BYTES, audit, membership_dates, next_membership_id, notify
from app.integrations.notifications import DeliveryResult, create_in_app, deliver_email, deliver_sms, record_delivery
from app.domain.notifications import queue_delivery
from app.services import BASE_STORAGE
from app.utils.storage import is_local_path, save_bytes, _safe_name, get_file_bytes

router = APIRouter(prefix='/admin', tags=['admin'])
ADMIN_ROLES = ('SUPER_ADMIN', 'CONTENT_EDITOR', 'MEMBERSHIP_OFFICER', 'CIRCLE_ADMIN', 'FINANCE_OFFICER', 'AUDITOR')
VALID_ROLES = {'SUPER_ADMIN', 'CONTENT_EDITOR', 'MEMBERSHIP_OFFICER', 'CIRCLE_ADMIN', 'FINANCE_OFFICER', 'AUDITOR', 'MEMBER'}


def _actor_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _content_dict(x):
    return x

def _crud_router(model, schema, path, perm_prefix, audit_entity, label, order_by=None, id_name=None, archive_field=None):
    # Register the four standard CRUD endpoints for a simple content resource.
    # Builds GET/POST/PUT/DELETE handlers that share the same create, update,
    # archive and audit-logging logic, avoiding per-resource boilerplate.
    id_name = id_name or f'{path.strip("/")[:-1]}_id'
    param = f'{{{id_name}}}'

    @router.get(path)
    def _list(_: User = Depends(require_permission(f'{perm_prefix}.read')), db: Session = Depends(get_db)):
        stmt = select(model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        return db.scalars(stmt).all()

    @router.post(path)
    def _create(payload: schema, request: Request, admin: User = Depends(require_permission(f'{perm_prefix}.write')), db: Session = Depends(get_db)):
        item = model(**payload.model_dump())
        db.add(item)
        db.flush()
        audit(db, admin, 'CREATE', audit_entity, item.id, _actor_ip(request))
        db.commit(); db.refresh(item)
        return item
    @router.put(f'{path}/{param}')
    def _update(payload: schema, request: Request, admin: User = Depends(require_permission(f'{perm_prefix}.write')), db: Session = Depends(get_db), **kwargs):
        item = db.get(model, kwargs[id_name])
        if not item:
            raise HTTPException(404, f'{label} not found')
        for k, v in payload.model_dump().items():
            setattr(item, k, v)
        audit(db, admin, 'UPDATE', audit_entity, item.id, _actor_ip(request))
        db.commit(); db.refresh(item)
        return item
    @router.delete(f'{path}/{param}')
    def _delete(request: Request, admin: User = Depends(require_permission(f'{perm_prefix}.write')), db: Session = Depends(get_db), **kwargs):
        item = db.get(model, kwargs[id_name])
        if not item:
            raise HTTPException(404, f'{label} not found')
        if archive_field:
            setattr(item, archive_field, False)
            action = 'ARCHIVE'
        else:
            db.delete(item)
            action = 'DELETE'
        audit(db, admin, action, audit_entity, item.id, _actor_ip(request)); db.commit()
        return {'ok': True}

    return _list, _create, _update, _delete

def _csv_response(filename: str, headers: list[str], rows) -> StreamingResponse:
    out = StringIO()
    writer = csv.writer(out)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return StreamingResponse(
        iter([out.getvalue()]),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )

@router.get('/exports/members.csv')
def export_members_csv(_: User = Depends(require_permission('member.read')), db: Session = Depends(get_db)):
    rows = db.scalars(select(Member).options(selectinload(Member.user), selectinload(Member.circle)).order_by(Member.id)).all()
    headers = ['membership_id','name_bn','email','phone','designation_bn','circle','status','issue_date','validity_date']
    cells = (
        [m.membership_id or '', m.user.name_bn, m.user.email, m.user.phone or '', m.designation_bn or '', m.circle.name_bn if m.circle else '', m.status, m.issue_date or '', m.validity_date or '']
        for m in rows
    )
    return _csv_response('pgcb-members.csv', headers, cells)

@router.get('/exports/event-registrations.csv')
def export_event_registrations_csv(_: User = Depends(require_permission('events.read')), db: Session = Depends(get_db)):
    rows = db.scalars(select(EventRegistration).order_by(EventRegistration.id)).all()
    headers = ['event_id','name','email','phone','organization','ticket_code','registration_status','attendance_status','payment_status','registered_at']
    cells = (
        [r.event_id, r.name, r.email, r.phone or '', r.organization or '', r.ticket_code, r.registration_status, r.attendance_status, r.payment_status, r.registered_at]
        for r in rows
    )
    return _csv_response('pgcb-event-registrations.csv', headers, cells)

@router.get('/exports/payments.csv')
def export_payments_csv(_: User = Depends(require_permission('finance.read')), db: Session = Depends(get_db)):
    rows = db.scalars(select(PaymentTransaction).order_by(PaymentTransaction.id)).all()
    headers = ['id','user_id','member_id','event_registration_id','purpose','amount','currency','provider','transaction_ref','status','created_at','updated_at']
    cells = (
        [p.id, p.user_id or '', p.member_id or '', p.event_registration_id or '', p.purpose, p.amount, p.currency, p.provider, p.transaction_ref or '', p.status, p.created_at, p.updated_at]
        for p in rows
    )
    return _csv_response('pgcb-payments.csv', headers, cells)


@router.get('/stats')
def stats(_: User = Depends(require_permission('content.read')), db: Session = Depends(get_db)):
    return {
        'members': db.scalar(select(func.count(Member.id))) or 0,
        'active_members': db.scalar(select(func.count(Member.id)).where(Member.status == 'ACTIVE')) or 0,
        'pending_members': db.scalar(select(func.count(Member.id)).where(Member.status.in_(['PENDING', 'SUBMITTED', 'UNDER_REVIEW']))) or 0,
        'circulars': db.scalar(select(func.count(Circular.id))) or 0,
        'published_circulars': db.scalar(select(func.count(Circular.id)).where(Circular.is_published == True)) or 0,
        'events': db.scalar(select(func.count(Event.id))) or 0,
        'journals': db.scalar(select(func.count(Journal.id))) or 0,
        'documents': db.scalar(select(func.count(MemberDocument.id))) or 0,
        'messages': db.scalar(select(func.count(ContactMessage.id)).where(ContactMessage.status == 'NEW')) or 0,
        'users': db.scalar(select(func.count(User.id))) or 0,
        'audit_logs': db.scalar(select(func.count(AuditLog.id))) or 0,
        'circles': db.scalar(select(func.count(Circle.id)).where(Circle.active == True)) or 0,
        'media': db.scalar(select(func.count(MediaAsset.id)).where(MediaAsset.published == True)) or 0,
        'event_registrations': db.scalar(select(func.count(EventRegistration.id))) or 0,
        'checked_in': db.scalar(select(func.count(EventRegistration.id)).where(EventRegistration.attendance_status == 'CHECKED_IN')) or 0,
        'payments_pending': db.scalar(select(func.count(PaymentTransaction.id)).where(PaymentTransaction.status == 'PENDING')) or 0,
        'payments_paid': db.scalar(select(func.count(PaymentTransaction.id)).where(PaymentTransaction.status == 'PAID')) or 0,
    }


@router.get('/permissions')
def permissions(user: User = Depends(require_permission('content.read'))):
    from app.core.rbac import ROLE_PERMISSIONS
    return {'role': user.role, 'permissions': sorted(ROLE_PERMISSIONS.get(user.role, set()))}

def _month_starts(now: datetime, count: int = 6) -> list[datetime]:
    # Return the first day of each of the last `count` months, oldest first.
    months = []
    cursor = datetime(now.year, now.month, 1)
    for _i in range(count):
        months.append(cursor)
        cursor = datetime(cursor.year - (1 if cursor.month == 1 else 0), 12 if cursor.month == 1 else cursor.month - 1, 1)
    months.reverse()
    return months

def _build_series(db: Session, months: list[datetime]) -> tuple[list[dict], list[dict], list[dict]]:
    # Build the member, content and event time series for the given months.
    member_series: list[dict] = []
    content_series: list[dict] = []
    event_series: list[dict] = []
    for start in months:
        if start.month == 12:
            end = datetime(start.year + 1, 1, 1)
        else:
            end = datetime(start.year, start.month + 1, 1)
        member_series.append({
            'label': start.strftime('%Y-%m'),
            'registrations': db.scalar(select(func.count(Member.id)).where(Member.created_at >= start, Member.created_at < end)) or 0,
            'approved': db.scalar(select(func.count(Member.id)).where(Member.created_at >= start, Member.created_at < end, Member.status == 'ACTIVE')) or 0,
        })
        content_series.append({
            'label': start.strftime('%Y-%m'),
            'circulars': db.scalar(select(func.count(Circular.id)).where(Circular.created_at >= start, Circular.created_at < end, Circular.is_published == True)) or 0,
            'journals': db.scalar(select(func.count(Journal.id)).where(Journal.created_at >= start, Journal.created_at < end, Journal.is_published == True)) or 0,
        })
        event_series.append({
            'label': start.strftime('%Y-%m'),
            'registrations': db.scalar(select(func.count(EventRegistration.id)).where(EventRegistration.registered_at >= start, EventRegistration.registered_at < end)) or 0,
        })
    return member_series, content_series, event_series
@router.get('/reports/overview')
def reports_overview(_: User = Depends(require_permission('content.read')), db: Session = Depends(get_db)):
    """Operational dashboard data for the admin console.

    Dates are calculated in application code to remain compatible with both
    the local SQLite development database and PostgreSQL production.
    """
    now = datetime.utcnow()
    months = _month_starts(now)
    member_series, content_series, event_series = _build_series(db, months)

    return {
        'generated_at': now,
        'members': {
            'total': db.scalar(select(func.count(Member.id))) or 0,
            'active': db.scalar(select(func.count(Member.id)).where(Member.status == 'ACTIVE')) or 0,
            'pending': db.scalar(select(func.count(Member.id)).where(Member.status.in_(['PENDING', 'SUBMITTED', 'UNDER_REVIEW']))) or 0,
            'expired': db.scalar(select(func.count(Member.id)).where(Member.status == 'EXPIRED')) or 0,
            'series': member_series,
        },
        'content': {
            'circulars': db.scalar(select(func.count(Circular.id))) or 0,
            'published_circulars': db.scalar(select(func.count(Circular.id)).where(Circular.is_published == True)) or 0,
            'journals': db.scalar(select(func.count(Journal.id))) or 0,
            'published_journals': db.scalar(select(func.count(Journal.id)).where(Journal.is_published == True)) or 0,
            'events': db.scalar(select(func.count(Event.id))) or 0,
            'published_events': db.scalar(select(func.count(Event.id)).where(Event.is_published == True)) or 0,
            'series': content_series,
        },
        'events': {
            'registrations': db.scalar(select(func.count(EventRegistration.id))) or 0,
            'checked_in': db.scalar(select(func.count(EventRegistration.id)).where(EventRegistration.attendance_status == 'CHECKED_IN')) or 0,
            'registered': db.scalar(select(func.count(EventRegistration.id)).where(EventRegistration.registration_status == 'REGISTERED')) or 0,
            'confirmed': db.scalar(select(func.count(EventRegistration.id)).where(EventRegistration.registration_status == 'CONFIRMED')) or 0,
            'series': event_series,
        },
        'messages': {
            'new': db.scalar(select(func.count(ContactMessage.id)).where(ContactMessage.status == 'NEW')) or 0,
            'in_progress': db.scalar(select(func.count(ContactMessage.id)).where(ContactMessage.status == 'IN_PROGRESS')) or 0,
            'resolved': db.scalar(select(func.count(ContactMessage.id)).where(ContactMessage.status == 'RESOLVED')) or 0,
        },
        'system': {
            'users': db.scalar(select(func.count(User.id))) or 0,
            'audit_logs': db.scalar(select(func.count(AuditLog.id))) or 0,
            'media': db.scalar(select(func.count(MediaAsset.id)).where(MediaAsset.published == True)) or 0,
        },
    }


@router.get('/members')
def members(status: str | None = None, q: str | None = None, limit: int = 50, offset: int = 0, _: User = Depends(require_permission('member.read')), db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    stmt = select(Member).options(selectinload(Member.user), selectinload(Member.circle)).order_by(Member.created_at.desc()).limit(limit).offset(max(offset, 0))
    if status:
        stmt = stmt.where(Member.status == status)
    if q:
        like = f'%{q}%'
        stmt = stmt.join(User, Member.user_id == User.id).where(
            (User.name_bn.like(like)) | (User.name_en.like(like)) | (User.email.like(like)) | 
            (User.phone.like(like)) | (Member.membership_id.like(like)) | (Member.employee_id.like(like))
        )
    rows = db.scalars(stmt).all()
    return [
        {
            'id': m.id, 'membership_id': m.membership_id, 'name_bn': m.user.name_bn, 'name_en': m.user.name_en,
            'email': m.user.email, 'phone': m.user.phone, 'employee_id': m.employee_id,
            'designation_bn': m.designation_bn, 'designation_en': m.designation_en,
            'circle_bn': m.circle.name_bn if m.circle else None, 'status': m.status,
            'created_at': m.created_at, 'validity_date': m.validity_date,
        }
        for m in rows
    ]


@router.get('/members/{member_id}')
def member_detail(member_id: int, _: User = Depends(require_permission('member.read')), db: Session = Depends(get_db)):
    m = db.scalar(select(Member).options(selectinload(Member.user), selectinload(Member.circle), selectinload(Member.documents)).where(Member.id == member_id))
    if not m:
        raise HTTPException(404, 'Member not found')
    return {
        'id': m.id, 'user_id': m.user_id, 'membership_id': m.membership_id, 'status': m.status,
        'application_note': m.application_note, 'name_bn': m.user.name_bn, 'name_en': m.user.name_en,
        'email': m.user.email, 'phone': m.user.phone, 'designation_bn': m.designation_bn,
        'designation_en': m.designation_en, 'employee_id': m.employee_id,
        'diploma_institution': m.diploma_institution, 'graduation_year': m.graduation_year,
        'nid_number': m.nid_number, 'date_of_birth': m.date_of_birth,
        'current_address': m.current_address, 'permanent_address': m.permanent_address,
        'circle_id': m.circle_id, 'circle_bn': m.circle.name_bn if m.circle else None,
        'issue_date': m.issue_date, 'validity_date': m.validity_date,
        'documents': [
            {'id': d.id, 'document_type': d.document_type, 'filename': d.filename,
             'review_status': d.review_status, 'created_at': d.created_at}
            for d in m.documents
        ],
    }


@router.post('/members/{member_id}/review')
def review_member(member_id: int, action: str, request: Request, admin: User = Depends(require_permission('member.review')), db: Session = Depends(get_db)):
    if action not in {'APPROVE', 'REJECT', 'REVIEW', 'SUSPEND', 'REACTIVATE'}:
        raise HTTPException(400, 'Invalid member action')
    m = db.scalar(select(Member).options(selectinload(Member.user), selectinload(Member.circle)).where(Member.id == member_id))
    if not m:
        raise HTTPException(404, 'Member not found')
    if action == 'REVIEW':
        m.status, note = 'UNDER_REVIEW', 'Application moved to review.'
    elif action == 'REJECT':
        m.status, note = 'REJECTED', 'Membership application rejected.'
    elif action == 'SUSPEND':
        m.status, note = 'SUSPENDED', 'Membership suspended by an administrator.'
    elif action == 'REACTIVATE':
        m.status, note = 'ACTIVE', 'Membership reactivated.'
    else:
        m.status = 'ACTIVE'
        if not m.membership_id:
            m.membership_id = next_membership_id(db)
        m.issue_date, m.validity_date = membership_dates()
        note = f'Membership approved with ID {m.membership_id}.'
    m.application_note = note
    audit(db, admin, f'{action}_MEMBER', 'MEMBER', m.id, _actor_ip(request))
    notify(db, m.user_id, 'সদস্যতা আপডেট', note, 'MEMBERSHIP')
    db.commit(); db.refresh(m)
    return {'ok': True, 'membership_id': m.membership_id, 'status': m.status, 'issue_date': m.issue_date, 'validity_date': m.validity_date}


@router.post('/documents/{document_id}/review')
def review_document(document_id: int, action: str, request: Request, admin: User = Depends(require_permission('document.review')), db: Session = Depends(get_db)):
    if action not in {'APPROVE', 'REJECT', 'PENDING'}:
        raise HTTPException(400, 'Invalid document action')
    d = db.get(MemberDocument, document_id)
    if not d:
        raise HTTPException(404, 'Document not found')
    d.review_status = action
    audit(db, admin, f'{action}_DOCUMENT', 'MEMBER_DOCUMENT', d.id, _actor_ip(request))
    db.commit()
    return {'ok': True, 'review_status': d.review_status}


@router.get('/documents/{document_id}/download')
def download_document(document_id: int, _: User = Depends(require_permission('document.review')), db: Session = Depends(get_db)):
    d = db.get(MemberDocument, document_id)
    if not d or not d.storage_path:
        raise HTTPException(404, 'Document not available')
    try:
        content = get_file_bytes(d.storage_path)
        return Response(
            content=content,
            media_type=d.content_type or 'application/octet-stream',
            headers={'Content-Disposition': f'attachment; filename="{d.filename}"'},
        )
    except FileNotFoundError:
        raise HTTPException(404, 'Document not found')
    except Exception as exc:
        raise HTTPException(502, f'Failed to retrieve document: {exc}')



@router.post('/uploads/public')
def upload_public_asset(request: Request, file: UploadFile = File(...), admin: User = Depends(require_permission('content.write')), db: Session = Depends(get_db)):
    allowed = {'application/pdf', 'image/jpeg', 'image/png', 'image/webp', 'video/mp4'}
    if file.content_type not in allowed:
        raise HTTPException(400, 'Unsupported public asset type')
    # Read in bounded chunks so an oversized body is rejected as soon as the cap
    # is exceeded instead of being buffered entirely into memory first.
    chunk_size = 1024 * 1024
    buffer = bytearray()
    while True:
        chunk = file.file.read(chunk_size)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, 'Maximum public asset size is 10 MB')
    content = bytes(buffer)
    filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{_safe_name(file.filename or 'asset.bin')}"
    try:
        stored = save_bytes(content, 'public', filename)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    audit(db, admin, 'UPLOAD', 'PUBLIC_ASSET', filename, _actor_ip(request)); db.commit()
    return {'ok': True, 'filename': filename, 'storage': stored, 'url': stored if stored.startswith('http') else f"/api/v1/public/assets/{filename}"}

# ---- Circulars ----
@router.get('/circulars')
def admin_circulars(_: User = Depends(require_permission('content.read')), db: Session = Depends(get_db)):
    rows = db.scalars(select(Circular).order_by(Circular.priority.desc(), Circular.published_at.desc())).all()
    return [CircularResponse.model_validate(x) for x in rows]


@router.post('/circulars', response_model=CircularResponse)
def create_circular(payload: CircularCreate, request: Request, admin: User = Depends(require_permission('content.write')), db: Session = Depends(get_db)):
    item = Circular(**payload.model_dump())
    if item.is_published and not item.published_at:
        item.published_at = datetime.utcnow()
    db.add(item); db.flush(); audit(db, admin, 'CREATE', 'CIRCULAR', item.id, _actor_ip(request)); db.commit(); db.refresh(item)
    return CircularResponse.model_validate(item)


@router.put('/circulars/{circular_id}', response_model=CircularResponse)
def update_circular(circular_id: int, payload: CircularCreate, request: Request, admin: User = Depends(require_permission('content.write')), db: Session = Depends(get_db)):
    item = db.get(Circular, circular_id)
    if not item:
        raise HTTPException(404, 'Circular not found')
    for k, v in payload.model_dump().items():
        setattr(item, k, v)
    if item.is_published and not item.published_at:
        item.published_at = datetime.utcnow()
    audit(db, admin, 'UPDATE', 'CIRCULAR', item.id, _actor_ip(request)); db.commit(); db.refresh(item)
    return CircularResponse.model_validate(item)


@router.delete('/circulars/{circular_id}')
def delete_circular(circular_id: int, request: Request, admin: User = Depends(require_permission('content.write')), db: Session = Depends(get_db)):
    item = db.get(Circular, circular_id)
    if not item:
        raise HTTPException(404, 'Circular not found')
    db.delete(item); audit(db, admin, 'DELETE', 'CIRCULAR', circular_id, _actor_ip(request)); db.commit()
    return {'ok': True}


# ---- Circles / committees ----
@router.get('/circles')
def admin_circles(_: User = Depends(require_permission('circle.read')), db: Session = Depends(get_db)):
    return db.scalars(select(Circle).order_by(Circle.name_bn)).all()


@router.post('/circles')
def create_circle(payload: CircleCreate, request: Request, admin: User = Depends(require_permission('circle.write')), db: Session = Depends(get_db)):
    if db.scalar(select(Circle).where(Circle.name_bn == payload.name_bn)):
        raise HTTPException(409, 'Circle already exists')
    item = Circle(**payload.model_dump()); db.add(item); db.flush(); audit(db, admin, 'CREATE', 'CIRCLE', item.id, _actor_ip(request)); db.commit(); db.refresh(item)
    return item


@router.put('/circles/{circle_id}')
def update_circle(circle_id: int, payload: CircleCreate, request: Request, admin: User = Depends(require_permission('circle.write')), db: Session = Depends(get_db)):
    item = db.get(Circle, circle_id)
    if not item:
        raise HTTPException(404, 'Circle not found')
    for k, v in payload.model_dump().items():
        setattr(item, k, v)
    audit(db, admin, 'UPDATE', 'CIRCLE', item.id, _actor_ip(request)); db.commit(); db.refresh(item)
    return item


@router.delete('/circles/{circle_id}')
def delete_circle(circle_id: int, request: Request, admin: User = Depends(require_permission('circle.write')), db: Session = Depends(get_db)):
    item = db.get(Circle, circle_id)
    if not item:
        raise HTTPException(404, 'Circle not found')
    item.active = False
    audit(db, admin, 'ARCHIVE', 'CIRCLE', item.id, _actor_ip(request)); db.commit()
    return {'ok': True}


@router.get('/committee')
def admin_committee(_: User = Depends(require_permission('content.read')), db: Session = Depends(get_db)):
    rows = db.scalars(select(CommitteeMember).order_by(CommitteeMember.circle_id, CommitteeMember.display_order)).all()
    return rows


@router.post('/committee')
def create_committee_member(payload: CommitteeMemberCreate, request: Request, admin: User = Depends(require_permission('content.write')), db: Session = Depends(get_db)):
    item = CommitteeMember(**payload.model_dump()); db.add(item); db.flush(); audit(db, admin, 'CREATE', 'COMMITTEE_MEMBER', item.id, _actor_ip(request)); db.commit(); db.refresh(item)
    return item


@router.put('/committee/{committee_id}')
def update_committee_member(committee_id: int, payload: CommitteeMemberCreate, request: Request, admin: User = Depends(require_permission('content.write')), db: Session = Depends(get_db)):
    item = db.get(CommitteeMember, committee_id)
    if not item:
        raise HTTPException(404, 'Committee member not found')
    for k, v in payload.model_dump().items():
        setattr(item, k, v)
    audit(db, admin, 'UPDATE', 'COMMITTEE_MEMBER', item.id, _actor_ip(request)); db.commit(); db.refresh(item)
    return item


@router.delete('/committee/{committee_id}')
def delete_committee_member(committee_id: int, request: Request, admin: User = Depends(require_permission('content.write')), db: Session = Depends(get_db)):
    item = db.get(CommitteeMember, committee_id)
    if not item:
        raise HTTPException(404, 'Committee member not found')
    item.active = False
    audit(db, admin, 'ARCHIVE', 'COMMITTEE_MEMBER', item.id, _actor_ip(request)); db.commit()
    return {'ok': True}


# ---- Journals / events / media (registered through the shared CRUD factory) ----
_crud_router(
    model=Journal,
    schema=JournalCreate,
    path='/journals',
    perm_prefix='journal',
    audit_entity='JOURNAL',
    label='Journal',
    order_by=Journal.publication_date.desc(),
    id_name='journal_id',
    archive_field='is_published',
)

_crud_router(
    model=Event,
    schema=EventCreate,
    path='/events',
    perm_prefix='events',
    audit_entity='EVENT',
    label='Event',
    order_by=Event.event_date.desc(),
    id_name='event_id',
    archive_field='is_published',
)

_crud_router(
    model=MediaAsset,
    schema=MediaCreate,
    path='/media',
    perm_prefix='media',
    audit_entity='MEDIA',
    label='Media',
    order_by=MediaAsset.created_at.desc(),
    id_name='media_id',
    archive_field='published',
)


# ---- Contact inbox ----
@router.get('/messages')
def messages(_: User = Depends(require_permission('content.read')), db: Session = Depends(get_db)):
    rows = db.scalars(select(ContactMessage).order_by(ContactMessage.created_at.desc()).limit(200)).all()
    return [
        {'id': x.id, 'name': x.name, 'email': x.email, 'phone': x.phone,
         'subject': x.subject, 'message': x.message, 'status': x.status, 'created_at': x.created_at}
        for x in rows
    ]


@router.patch('/messages/{message_id}')
def update_message(message_id: int, payload: MessageStatusUpdate, request: Request, admin: User = Depends(require_permission('content.write')), db: Session = Depends(get_db)):
    item = db.get(ContactMessage, message_id)
    if not item: raise HTTPException(404, 'Message not found')
    item.status = payload.status
    audit(db, admin, 'UPDATE_STATUS', 'CONTACT_MESSAGE', item.id, _actor_ip(request)); db.commit()
    return {'ok': True, 'status': item.status}


# ---- Users ----
@router.get('/users')
def admin_users(_: User = Depends(require_permission('user.read')), db: Session = Depends(get_db)):
    rows = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return [
        {'id': u.id, 'email': u.email, 'name_bn': u.name_bn, 'phone': u.phone,
         'role': u.role, 'is_active': u.is_active, 'created_at': u.created_at}
        for u in rows
    ]


@router.post('/users')
def create_user(payload: AdminUserCreate, request: Request, admin: User = Depends(require_permission('user.write')), db: Session = Depends(get_db)):
    if payload.role not in VALID_ROLES:
        raise HTTPException(400, 'Invalid role')
    email = payload.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, 'Email already registered')
    user = User(email=email, password_hash=hash_password(payload.password), name_bn=payload.name_bn,
                name_en=payload.name_en, phone=payload.phone, role=payload.role, is_active=payload.is_active)
    db.add(user); db.flush()
    if payload.role == 'MEMBER':
        db.add(Member(user_id=user.id))
    audit(db, admin, 'CREATE', 'USER', user.id, _actor_ip(request)); db.commit(); db.refresh(user)
    return {'id': user.id, 'email': user.email, 'role': user.role}


@router.patch('/users/{user_id}')
def update_user(user_id: int, payload: AdminUserUpdate, request: Request, admin: User = Depends(require_permission('user.write')), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user: raise HTTPException(404, 'User not found')
    if user.id == admin.id and payload.is_active is False:
        raise HTTPException(400, 'You cannot deactivate your own account')
    if payload.role is not None:
        if payload.role not in VALID_ROLES: raise HTTPException(400, 'Invalid role')
        user.role = payload.role
    for field in ('name_bn', 'name_en', 'phone', 'is_active'):
        value = getattr(payload, field)
        if value is not None: setattr(user, field, value)
    audit(db, admin, 'UPDATE', 'USER', user.id, _actor_ip(request)); db.commit(); db.refresh(user)
    return {'id': user.id, 'email': user.email, 'role': user.role, 'is_active': user.is_active}


# ---- Administrator MFA ----
@router.get('/mfa/status')
def mfa_status(admin: User = Depends(require_permission('settings.read'))):
    return {'enabled': bool(admin.mfa_enabled)}


@router.post('/mfa/setup')
def mfa_setup(admin: User = Depends(require_permission('settings.write')), db: Session = Depends(get_db)):
    secret = generate_secret()
    uri = otpauth_uri(secret, admin.email)
    try:
        import base64
        import io
        import qrcode
        image = qrcode.make(uri)
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        qr_data_url = 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()
    except Exception:
        qr_data_url = None
    admin.mfa_secret = None
    admin.mfa_secret_enc = encrypt_secret(secret)
    admin.mfa_enabled = False
    audit(db, admin, 'PREPARE_MFA', 'USER', admin.id)
    db.commit()
    return {'secret': secret, 'otpauth_url': uri, 'qr_data_url': qr_data_url, 'enabled': False}


@router.post('/mfa/enable')
def mfa_enable(code: str, request: Request, admin: User = Depends(require_permission('settings.write')), db: Session = Depends(get_db)):
    secret = decrypt_secret(admin.mfa_secret_enc) or admin.mfa_secret
    if not secret:
        raise HTTPException(400, 'MFA setup has not been started')
    if not verify_totp(secret, code):
        raise HTTPException(400, 'Invalid authenticator code')
    admin.mfa_enabled = True
    audit(db, admin, 'ENABLE_MFA', 'USER', admin.id, _actor_ip(request))
    db.commit()
    return {'ok': True, 'enabled': True}


@router.post('/mfa/disable')
def mfa_disable(code: str, request: Request, admin: User = Depends(require_permission('settings.write')), db: Session = Depends(get_db)):
    if not admin.mfa_enabled:
        raise HTTPException(400, 'MFA is not enabled')
    secret = decrypt_secret(admin.mfa_secret_enc) or admin.mfa_secret
    if not secret or not verify_totp(secret, code):
        raise HTTPException(400, 'Invalid authenticator code')
    admin.mfa_enabled = False
    admin.mfa_secret = None
    admin.mfa_secret_enc = None
    audit(db, admin, 'DISABLE_MFA', 'USER', admin.id, _actor_ip(request))
    db.commit()
    return {'ok': True, 'enabled': False}




# ---- Notifications ----
@router.post('/notifications/broadcast')
def broadcast_notification(payload: BroadcastNotification, request: Request, admin: User = Depends(require_permission('notification.write')), db: Session = Depends(get_db)):
    stmt = select(User).where(User.is_active == True).order_by(User.id).limit(10000)
    if payload.role: stmt = stmt.where(User.role == payload.role)
    users = db.scalars(stmt).all()
    deliveries = 0
    for user in users:
        notification = create_in_app(db, user, payload.title_bn, payload.body_bn, payload.notification_type) if payload.channel in {'IN_APP', 'ALL'} else None
        if notification:
            deliveries += 1
            record_delivery(db, notification.id, 'IN_APP', user.email, DeliveryResult('SENT', 'IN_APP'))
        if payload.channel in {'EMAIL', 'ALL'}:
            queue_delivery(db, notification.id if notification else None, 'EMAIL', user.email)
            deliveries += 1
        if payload.channel in {'SMS', 'ALL'} and user.phone:
            queue_delivery(db, notification.id if notification else None, 'SMS', user.phone)
            deliveries += 1
    audit(db, admin, 'BROADCAST', 'NOTIFICATION', None, _actor_ip(request)); db.commit()
    return {'ok': True, 'recipients': len(users), 'deliveries_recorded': deliveries, 'channel': payload.channel}

# ---- Event registration + attendance ----
@router.get('/event-registrations')
def event_registrations(event_id: int | None = None, status: str | None = None, limit: int = 100, _: User = Depends(require_permission('events.read')), db: Session = Depends(get_db)):
    limit = max(1, min(limit, 500))
    stmt = select(EventRegistration).order_by(EventRegistration.registered_at.desc()).limit(limit)
    if event_id: stmt = stmt.where(EventRegistration.event_id == event_id)
    if status: stmt = stmt.where(EventRegistration.registration_status == status)
    rows = db.scalars(stmt).all()
    return [{'id': r.id, 'event_id': r.event_id, 'user_id': r.user_id, 'name': r.name, 'email': r.email, 'phone': r.phone, 'organization': r.organization, 'ticket_code': r.ticket_code, 'registration_status': r.registration_status, 'attendance_status': r.attendance_status, 'payment_status': r.payment_status, 'registered_at': r.registered_at} for r in rows]

@router.patch('/event-registrations/{registration_id}')
def update_event_registration(registration_id: int, payload: RegistrationStatusUpdate, request: Request, admin: User = Depends(require_permission('events.write')), db: Session = Depends(get_db)):
    allowed = {'REGISTERED', 'WAITLISTED', 'CANCELLED', 'CONFIRMED'}
    if payload.status not in allowed: raise HTTPException(400, 'Invalid registration status')
    item = db.get(EventRegistration, registration_id)
    if not item: raise HTTPException(404, 'Registration not found')
    item.registration_status = payload.status
    audit(db, admin, 'UPDATE_REGISTRATION', 'EVENT_REGISTRATION', item.id, _actor_ip(request))
    db.commit()
    return {'ok': True, 'status': item.registration_status}

def _apply_check_in(db: Session, admin: User, item: EventRegistration, request: Request, prefix: str) -> dict:
    # Validate and apply a check-in, returning the shared response payload.
    if item.registration_status == 'CANCELLED':
        raise HTTPException(409, 'Cancelled registration cannot be checked in')
    if item.payment_status in {'REQUIRED', 'PENDING', 'FAILED'}:
        raise HTTPException(409, 'Payment must be completed before check-in')
    already_checked = item.attendance_status == 'CHECKED_IN'
    item.attendance_status = 'CHECKED_IN'; item.checked_in_at = item.checked_in_at or datetime.utcnow(); item.checked_in_by = item.checked_in_by or admin.id
    audit(db, admin, prefix if not already_checked else f'{prefix}_REPEAT', 'EVENT_REGISTRATION', item.id, _actor_ip(request))
    db.commit()
    return {'ok': True, 'already_checked_in': already_checked, 'attendance_status': item.attendance_status}

@router.post('/event-registrations/{registration_id}/check-in')
def check_in_event_registration(registration_id: int, request: Request, admin: User = Depends(require_permission('events.write')), db: Session = Depends(get_db)):
    item = db.get(EventRegistration, registration_id)
    if not item: raise HTTPException(404, 'Registration not found')
    result = _apply_check_in(db, admin, item, request, 'CHECK_IN')
    result['checked_in_at'] = item.checked_in_at
    return result
@router.post('/event-registrations/check-in-by-ticket')
def check_in_by_ticket(payload: CheckInRequest, request: Request, admin: User = Depends(require_permission('events.write')), db: Session = Depends(get_db)):
    item = db.scalar(select(EventRegistration).where(EventRegistration.ticket_code == payload.ticket_code))
    if not item: raise HTTPException(404, 'Ticket not found')
    result = _apply_check_in(db, admin, item, request, 'CHECK_IN_TICKET')
    result.update({'registration_id': item.id, 'name': item.name, 'ticket_code': item.ticket_code})
    return result

@router.get('/payments')
def payments(status: str | None = None, purpose: str | None = None, limit: int = 100, _: User = Depends(require_permission('finance.read')), db: Session = Depends(get_db)):
    limit = max(1, min(limit, 500))
    stmt = select(PaymentTransaction).order_by(PaymentTransaction.created_at.desc()).limit(limit)
    if status: stmt = stmt.where(PaymentTransaction.status == status)
    if purpose: stmt = stmt.where(PaymentTransaction.purpose == purpose)
    rows = db.scalars(stmt).all()
    return [{'id': p.id, 'user_id': p.user_id, 'member_id': p.member_id, 'event_registration_id': p.event_registration_id, 'purpose': p.purpose, 'amount': p.amount, 'currency': p.currency, 'provider': p.provider, 'transaction_ref': p.transaction_ref, 'status': p.status, 'created_at': p.created_at, 'updated_at': p.updated_at} for p in rows]

@router.patch('/payments/{payment_id}')
def update_payment(payment_id: int, payload: PaymentStatusUpdate, request: Request, admin: User = Depends(require_permission('finance.write')), db: Session = Depends(get_db)):
    allowed = {'PENDING', 'PAID', 'FAILED', 'REFUNDED', 'CANCELLED'}
    if payload.status not in allowed: raise HTTPException(400, 'Invalid payment status')
    item = db.get(PaymentTransaction, payment_id)
    if not item: raise HTTPException(404, 'Payment not found')
    item.status = payload.status
    if payload.transaction_ref is not None: item.transaction_ref = payload.transaction_ref
    if payload.status == 'PAID' and item.purpose == 'MEMBERSHIP' and item.member_id:
        from app.models import MembershipRenewal
        from app.domain.membership import renew_membership
        existing_renewal = db.scalar(select(MembershipRenewal).where(MembershipRenewal.payment_id == item.id))
        if not existing_renewal:
            member = db.get(Member, item.member_id)
            if not member:
                raise HTTPException(409, 'Member not found for renewal')
            renew_membership(db, member, item.id, item.amount, item.currency)
    if item.event_registration_id:
        reg = db.get(EventRegistration, item.event_registration_id)
        if reg:
            if payload.status == 'PAID': reg.payment_status = 'PAID'
            elif payload.status == 'FAILED': reg.payment_status = 'FAILED'
            elif payload.status == 'REFUNDED': reg.payment_status = 'REFUNDED'
    audit(db, admin, 'UPDATE_PAYMENT', 'PAYMENT', item.id, _actor_ip(request)); db.commit()
    return {'ok': True, 'status': item.status}

@router.get('/notification-deliveries')
def notification_deliveries(limit: int = 100, _: User = Depends(require_permission('notification.write')), db: Session = Depends(get_db)):
    rows = db.scalars(select(NotificationDelivery).order_by(NotificationDelivery.created_at.desc()).limit(max(1, min(limit, 500)))).all()
    return [{'id': d.id, 'notification_id': d.notification_id, 'channel': d.channel, 'recipient': d.recipient, 'status': d.status, 'provider': d.provider, 'error_message': d.error_message, 'sent_at': d.sent_at, 'created_at': d.created_at} for d in rows]

# ---- Certificates ----
@router.get('/certificates')
def certificates(limit: int = 100, _: User = Depends(require_permission('certificate.write')), db: Session = Depends(get_db)):
    rows = db.scalars(select(Certificate).order_by(Certificate.created_at.desc()).limit(max(1, min(limit, 500)))).all()
    return [{'id': c.id, 'certificate_no': c.certificate_no, 'recipient_name': c.recipient_name, 'title_bn': c.title_bn, 'issue_date': c.issue_date, 'event_registration_id': c.event_registration_id, 'member_id': c.member_id} for c in rows]

# ---- Site settings + audit ----
@router.get('/settings')
def settings(_: User = Depends(require_permission('settings.read')), db: Session = Depends(get_db)):
    rows = db.scalars(select(SiteSetting).order_by(SiteSetting.category, SiteSetting.key)).all()
    return [{'id': s.id, 'key': s.key, 'value': s.value, 'category': s.category, 'updated_at': s.updated_at} for s in rows]


@router.put('/settings')
def upsert_setting(payload: SiteSettingUpdate, request: Request, admin: User = Depends(require_permission('settings.write')), db: Session = Depends(get_db)):
    item = db.scalar(select(SiteSetting).where(SiteSetting.key == payload.key))
    if item:
        item.value, item.category = payload.value, payload.category
        action = 'UPDATE'
    else:
        item = SiteSetting(**payload.model_dump()); db.add(item); action = 'CREATE'
    db.flush(); audit(db, admin, action, 'SITE_SETTING', item.id, _actor_ip(request)); db.commit(); db.refresh(item)
    return {'id': item.id, 'key': item.key, 'value': item.value, 'category': item.category}


@router.get('/audit-logs')
def audit_logs(limit: int = 100, _: User = Depends(require_permission('audit.read')), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(max(limit, 1), 300))).all()
    return [{'id': x.id, 'user_id': x.user_id, 'action': x.action, 'entity': x.entity, 'entity_id': x.entity_id, 'ip_address': x.ip_address, 'created_at': x.created_at} for x in rows]


# ---- Member CSV Import (Batch Processing) ----
@router.post('/imports/members/preview')
async def preview_members_csv(
    file: UploadFile = File(...),
    _: User = Depends(require_permission('member.import')),
    db: Session = Depends(get_db),
):
    """Parse and validate uploaded members CSV without writing to the database."""
    content = await file.read()
    try:
        text_data = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        text_data = content.decode('latin-1')

    reader = csv.DictReader(StringIO(text_data))
    rows = []
    seen_emails: set[str] = set()
    valid_count = 0
    error_count = 0

    # Cache existing circles and users for fast validation
    existing_circles = {c.name_bn.strip(): c.id for c in db.scalars(select(Circle)).all()}
    existing_circles.update({c.name_en.strip(): c.id for c in db.scalars(select(Circle)).all() if c.name_en})
    existing_users = set(db.scalars(select(User.email)).all())

    for idx, row in enumerate(reader, start=2):
        errors: list[str] = []
        name_bn = (row.get('name_bn') or row.get('full_name_bn') or row.get('name') or '').strip()
        name_en = (row.get('name_en') or row.get('full_name_en') or '').strip() or None
        email = (row.get('email') or '').strip().lower()
        phone = (row.get('phone') or '').strip() or None
        employee_id = (row.get('employee_id') or '').strip() or None
        designation_bn = (row.get('designation_bn') or row.get('designation') or '').strip() or None
        circle_val = (row.get('circle') or row.get('circle_id') or '').strip()

        if not name_bn:
            errors.append('নাম (Bangla name) আবশ্যক (required)')
        if not email:
            errors.append('ইমেইল (Email) আবশ্যক (required)')
        elif '@' not in email or '.' not in email.split('@')[-1]:
            errors.append('সঠিক ইমেইল ফরম্যাট দিন (Invalid email format)')
        elif email in seen_emails:
            errors.append('একই ফাইলে ইমেইল একাধিকবার রয়েছে (Duplicate email in file)')
        elif email in existing_users:
            errors.append('ইমেইলটি ইতোমধ্যে নিবন্ধিত (Email already exists in database)')

        circle_id = None
        if circle_val:
            if circle_val.isdigit():
                circle_id = int(circle_val)
            elif circle_val in existing_circles:
                circle_id = existing_circles[circle_val]

        is_valid = len(errors) == 0
        if is_valid:
            valid_count += 1
            seen_emails.add(email)
        else:
            error_count += 1

        rows.append({
            'row_number': idx,
            'name_bn': name_bn,
            'name_en': name_en,
            'email': email,
            'phone': phone,
            'employee_id': employee_id,
            'designation_bn': designation_bn,
            'circle_id': circle_id,
            'valid': is_valid,
            'errors': errors,
        })

    return {
        'total_rows': len(rows),
        'valid_count': valid_count,
        'error_count': error_count,
        'rows': rows,
    }


@router.post('/imports/members/commit')
async def commit_members_csv(
    payload: dict,
    request: Request,
    admin: User = Depends(require_permission('member.import')),
    db: Session = Depends(get_db),
):
    """Commit valid member rows from preview into the system."""
    rows_data = payload.get('rows', [])
    if not rows_data:
        raise HTTPException(400, 'No rows to import')

    imported = 0
    skipped = 0
    now, expires = membership_dates()

    for item in rows_data:
        email = (item.get('email') or '').strip().lower()
        if not email or db.scalar(select(User).where(User.email == email)):
            skipped += 1
            continue

        name_bn = (item.get('name_bn') or '').strip()
        if not name_bn:
            skipped += 1
            continue

        temp_password = hash_password('Pgcb@2026!')
        user = User(
            email=email,
            password_hash=temp_password,
            name_bn=name_bn,
            name_en=item.get('name_en'),
            phone=item.get('phone'),
            role='MEMBER',
            is_active=True,
            email_verified=True,
        )
        db.add(user)
        db.flush()

        member = Member(
            user_id=user.id,
            membership_id=next_membership_id(db),
            employee_id=item.get('employee_id'),
            designation_bn=item.get('designation_bn'),
            designation_en=item.get('designation_en') or item.get('designation_bn'),
            circle_id=item.get('circle_id'),
            status='ACTIVE',
            membership_type=item.get('membership_type', 'GENERAL'),
            issue_date=now,
            validity_date=expires,
        )
        db.add(member)
        imported += 1

    audit(db, admin, 'IMPORT_MEMBERS_CSV', 'MEMBER', None, _actor_ip(request))
    db.commit()

    return {
        'ok': True,
        'imported_count': imported,
        'skipped_count': skipped,
        'message': f'সফলভাবে {imported} জন সদস্য অন্তর্ভুক্ত করা হয়েছে।'
    }

