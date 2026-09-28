from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.audit import log_audit_action
from app.core.config import settings
from app.core.deps import current_user
from app.db.session import get_db
from app.domain.membership import RENEWAL_PERIODS, resolve_renewal_days
from app.integrations.payments import create_checkout, normalize_provider
from app.models import (
    Certificate,
    Circular,
    EventRegistration,
    Member,
    MemberDocument,
    MembershipRenewal,
    Notice,
    Notification,
    PaymentTransaction,
    User,
)
from app.schemas.membership import ApplicationResponse, MemberDocumentResponse, MemberProfileUpdate
from app.services import ALLOWED_CONTENT_TYPES, ALLOWED_DOC_TYPES, audit, membership_dates, next_membership_id, notify
from app.services import BASE_STORAGE
from app.services.receipt_service import get_fee_schedule, resolve_plan_amount
from app.utils.storage import get_file_bytes, is_local_path, save_bytes, validate_upload_bytes

router = APIRouter(prefix='/member', tags=['membership'])


def get_member(user: User, db: Session) -> Member:
    member = db.scalar(
        select(Member)
        .options(selectinload(Member.circle), selectinload(Member.documents))
        .where(Member.user_id == user.id)
    )
    if not member:
        raise HTTPException(404, 'Member profile not found')
    return member


def _compute_expiry_info(member: Member, now: datetime | None = None) -> dict:
    now = now or datetime.utcnow()
    status = (member.status or 'PENDING').upper()
    if status in ('REVOKED', 'SUSPENDED', 'REJECTED'):
        return {
            'days_until_expiry': None,
            'expiry_indicator': status,
            'is_expiring_soon': False,
            'is_expired': status == 'EXPIRED',
            'valid_until_formatted': member.validity_date.strftime('%d %b %Y') if member.validity_date else None,
            'valid_years': None,
        }
    if not member.validity_date:
        return {
            'days_until_expiry': None,
            'expiry_indicator': 'ACTIVE' if status == 'ACTIVE' else status,
            'is_expiring_soon': False,
            'is_expired': status == 'EXPIRED',
            'valid_until_formatted': None,
            'valid_years': None,
        }
    delta_days = (member.validity_date.date() - now.date()).days
    iss_year = (member.issue_date or now).year
    val_year = member.validity_date.year
    if delta_days < 0 or status == 'EXPIRED':
        indicator = 'EXPIRED'
    elif delta_days <= 60:
        indicator = 'EXPIRING_SOON'
    else:
        indicator = 'VALID'
    return {
        'days_until_expiry': delta_days,
        'expiry_indicator': indicator,
        'is_expiring_soon': 0 <= delta_days <= 60,
        'is_expired': delta_days < 0 or status == 'EXPIRED',
        'valid_until_formatted': member.validity_date.strftime('%d %b %Y'),
        'valid_years': f'{iss_year}–{val_year}',
    }


def _relative_time(dt: datetime | None, now: datetime | None = None) -> tuple[str, str]:
    if not dt:
        return ('Just now', 'এইমাত্র')
    now = now or datetime.utcnow()
    diff = max(0, int((now - dt).total_seconds()))
    if diff < 60:
        return ('Just now', 'এইমাত্র')
    if diff < 3600:
        mins = diff // 60
        return (f'{mins} min ago', f'{mins} মিনিট আগে')
    if diff < 86400:
        hrs = diff // 3600
        return (f'{hrs} hour{"s" if hrs > 1 else ""} ago', f'{hrs} ঘণ্টা আগে')
    days = diff // 86400
    if days == 1:
        return ('Yesterday', 'গতকাল')
    return (f'{days} days ago', f'{days} দিন আগে')


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
    exp = _compute_expiry_info(m)
    return {
        'id': m.id,
        'name_bn': user.name_bn,
        'name_en': user.name_en,
        'email': user.email,
        'phone': user.phone,
        'membership_id': m.membership_id,
        'membership_type': m.membership_type or 'GENERAL',
        'status': m.status,
        'designation_bn': m.designation_bn,
        'designation_en': m.designation_en,
        'employee_id': m.employee_id,
        'diploma_institution': m.diploma_institution,
        'graduation_year': m.graduation_year,
        'nid_number': m.nid_number,
        'date_of_birth': m.date_of_birth,
        'current_address': m.current_address,
        'permanent_address': m.permanent_address,
        'circle_id': m.circle_id,
        'circle_bn': m.circle.name_bn if m.circle else None,
        'circle_en': m.circle.name_en if m.circle else None,
        'issue_date': m.issue_date,
        'validity_date': m.validity_date,
        'photo_url': m.photo_url,
        **exp,
    }


@router.get('/dashboard')
def member_dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Comprehensive Member Dashboard 2.0 summary: membership status, quick stats, and recent activity feed."""
    m = get_member(user, db)
    now = datetime.utcnow()
    exp = _compute_expiry_info(m, now)

    unread_count = db.scalar(
        select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.read_at.is_(None))
    ) or 0
    certs_count = db.scalar(
        select(func.count(Certificate.id)).where(Certificate.member_id == m.id)
    ) or 0
    if m.status == 'ACTIVE' and m.membership_id and certs_count == 0:
        certs_count = 1
    docs_count = len(m.documents or [])
    payments_count = db.scalar(
        select(func.count(PaymentTransaction.id)).where(
            (PaymentTransaction.member_id == m.id) | (PaymentTransaction.user_id == user.id)
        )
    ) or 0
    events_count = db.scalar(
        select(func.count(EventRegistration.id)).where(EventRegistration.user_id == user.id)
    ) or 0

    activities: list[dict] = []

    # 1. Membership approval / status milestone
    if m.status == 'ACTIVE' and m.membership_id:
        activities.append({
            'id': f'mem-{m.id}',
            'type': 'MEMBERSHIP',
            'title_en': 'Membership approved',
            'title_bn': f'সদস্যপদ অনুমোদিত ({m.membership_id})',
            'subtitle_bn': f'বৈধতা: {exp["valid_until_formatted"] or "সক্রিয়"}',
            'timestamp': (m.issue_date or m.updated_at or m.created_at or now).isoformat(),
            'relative_time_en': _relative_time(m.issue_date or m.updated_at, now)[0],
            'relative_time_bn': _relative_time(m.issue_date or m.updated_at, now)[1],
        })

    # 2. Recent certificates
    recent_certs = db.scalars(
        select(Certificate).where(Certificate.member_id == m.id).order_by(Certificate.issue_date.desc()).limit(3)
    ).all()
    for c in recent_certs:
        activities.append({
            'id': f'cert-{c.id}',
            'type': 'CERTIFICATE',
            'title_en': 'Certificate issued',
            'title_bn': f'সনদপত্র ইস্যু হয়েছে ({c.certificate_no})',
            'subtitle_bn': c.title_bn,
            'timestamp': (c.issue_date or c.created_at or now).isoformat(),
            'relative_time_en': _relative_time(c.issue_date or c.created_at, now)[0],
            'relative_time_bn': _relative_time(c.issue_date or c.created_at, now)[1],
        })

    # 3. Recent paid payments
    recent_payments = db.scalars(
        select(PaymentTransaction)
        .where(
            ((PaymentTransaction.member_id == m.id) | (PaymentTransaction.user_id == user.id)),
            PaymentTransaction.status.in_(['PAID', 'SUCCESS', 'COMPLETED']),
        )
        .order_by(PaymentTransaction.created_at.desc())
        .limit(3)
    ).all()
    for p in recent_payments:
        activities.append({
            'id': f'pay-{p.id}',
            'type': 'PAYMENT',
            'title_en': 'Payment successful',
            'title_bn': f'পেমেন্ট সফল হয়েছে (৳{int(p.amount):,})',
            'subtitle_bn': f'রসিদ: {p.receipt_no or p.transaction_ref or p.id}',
            'timestamp': (p.updated_at or p.created_at or now).isoformat(),
            'relative_time_en': _relative_time(p.updated_at or p.created_at, now)[0],
            'relative_time_bn': _relative_time(p.updated_at or p.created_at, now)[1],
        })

    # 4. Recent published circulars & notices
    recent_circulars = db.scalars(
        select(Circular).where(Circular.is_published == True).order_by(Circular.created_at.desc()).limit(2)
    ).all()
    for cir in recent_circulars:
        activities.append({
            'id': f'cir-{cir.id}',
            'type': 'CIRCULAR',
            'title_en': 'New circular published',
            'title_bn': f'নতুন সার্কুলার প্রকাশিত: {cir.title_bn}',
            'subtitle_bn': cir.reference_no or cir.category,
            'timestamp': (cir.published_at or cir.created_at or now).isoformat(),
            'relative_time_en': _relative_time(cir.published_at or cir.created_at, now)[0],
            'relative_time_bn': _relative_time(cir.published_at or cir.created_at, now)[1],
        })

    activities.sort(key=lambda item: item.get('timestamp') or '', reverse=True)

    membership_info = {
        'id': m.id,
        'membership_id': m.membership_id,
        'membership_type': m.membership_type or 'GENERAL',
        'status': m.status,
        'designation_bn': m.designation_bn,
        'designation_en': m.designation_en,
        'circle_id': m.circle_id,
        'circle_bn': m.circle.name_bn if m.circle else None,
        'circle_en': m.circle.name_en if m.circle else None,
        'issue_date': m.issue_date,
        'validity_date': m.validity_date,
        **exp,
    }
    quick_actions = [
        {'id': 'DIGITAL_ID', 'label_bn': 'ডিজিটাল আইডি', 'label_en': 'Digital ID', 'href': '/portal/id-card'},
        {'id': 'RENEW_MEMBERSHIP', 'label_bn': 'সদস্যপদ নবায়ন', 'label_en': 'Renew Membership', 'href': '/portal?tab=renewal'},
        {'id': 'CERTIFICATES', 'label_bn': 'সনদপত্র ওয়ালেট', 'label_en': 'Certificates', 'href': '/portal?tab=certificates'},
        {'id': 'DOCUMENTS', 'label_bn': 'ডকুমেন্টস', 'label_en': 'Documents', 'href': '/portal?tab=documents'},
        {'id': 'PAYMENTS', 'label_bn': 'পেমেন্ট ও রসিদ', 'label_en': 'Payments', 'href': '/portal?tab=payments'},
        {'id': 'EVENTS', 'label_bn': 'ইভেন্ট নিবন্ধন', 'label_en': 'Events', 'href': '/events'},
    ]

    return {
        'user': {
            'id': user.id,
            'name_bn': user.name_bn,
            'name_en': user.name_en,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
        },
        'hero_card': membership_info,
        'membership': membership_info,
        'quick_actions': quick_actions,
        'quick_stats': {
            'unread_notifications': unread_count,
            'certificates_count': certs_count,
            'documents_count': docs_count,
            'payments_count': payments_count,
            'events_count': events_count,
        },
        'recent_activity': activities[:8],
    }


@router.get('/renewal-options')
def get_renewal_options(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Return available membership renewal periods, server-calculated fees, and projected expiry dates."""
    m = get_member(user, db)
    now = datetime.utcnow()
    exp = _compute_expiry_info(m, now)
    schedule = get_fee_schedule(db)
    base_date = m.validity_date if (m.validity_date and m.validity_date > now) else now

    annual_fee = int(schedule.get('RENEWAL', 2000))
    life_fee = int(schedule.get('LIFE', 10000))

    periods = [
        {
            'plan_id': 'RENEWAL_1YR',
            'code': 'RENEWAL_1YR',
            'period': '1YR',
            'title_bn': '১ বছর মেয়াদী বার্ষিক নবায়ন',
            'title_en': '1 Year Annual Membership Renewal',
            'years': 1,
            'days': 365,
            'amount': annual_fee,
            'amount_bdt': annual_fee,
            'amount_formatted': f'৳{annual_fee:,}',
            'currency': 'BDT',
            'projected_validity_date': (base_date + timedelta(days=365)).strftime('%Y-%m-%d'),
            'projected_validity_formatted': (base_date + timedelta(days=365)).strftime('%d %b %Y'),
        },
        {
            'plan_id': 'RENEWAL_2YR',
            'code': 'RENEWAL_2YR',
            'period': '2YR',
            'title_bn': '২ বছর মেয়াদী বর্ধিত নবায়ন',
            'title_en': '2 Years Extended Membership Renewal',
            'years': 2,
            'days': 730,
            'amount': annual_fee * 2,
            'amount_bdt': annual_fee * 2,
            'amount_formatted': f'৳{annual_fee * 2:,}',
            'currency': 'BDT',
            'projected_validity_date': (base_date + timedelta(days=730)).strftime('%Y-%m-%d'),
            'projected_validity_formatted': (base_date + timedelta(days=730)).strftime('%d %b %Y'),
        },
        {
            'plan_id': 'LIFE',
            'code': 'LIFE',
            'period': 'LIFE',
            'title_bn': 'আজীবন সদস্যপদ আপগ্রেড',
            'title_en': 'Lifetime Membership Upgrade',
            'years': 50,
            'days': 18250,
            'amount': life_fee,
            'amount_bdt': life_fee,
            'amount_formatted': f'৳{life_fee:,}',
            'currency': 'BDT',
            'projected_validity_date': (base_date + timedelta(days=18250)).strftime('%Y-%m-%d'),
            'projected_validity_formatted': (base_date + timedelta(days=18250)).strftime('%d %b %Y'),
        },
    ]

    return {
        'member_id': m.id,
        'membership_id': m.membership_id,
        'status': m.status,
        'current_validity_date': m.validity_date,
        **exp,
        'reminder_schedule_days': [60, 30, 7, 0],
        'options': periods,
        'periods': periods,
    }


@router.get('/renewals')
def list_member_renewals(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Return chronological history of membership renewals for the authenticated member."""
    m = get_member(user, db)
    rows = db.scalars(
        select(MembershipRenewal)
        .where(MembershipRenewal.member_id == m.id)
        .order_by(MembershipRenewal.created_at.desc())
    ).all()
    result = []
    for r in rows:
        payment = db.get(PaymentTransaction, r.payment_id) if r.payment_id else None
        result.append({
            'id': r.id,
            'payment_id': r.payment_id,
            'previous_validity_date': r.previous_validity_date,
            'new_validity_date': r.new_validity_date,
            'new_validity_formatted': r.new_validity_date.strftime('%d %b %Y') if r.new_validity_date else None,
            'amount': float(r.amount),
            'amount_formatted': f'৳{int(r.amount):,}',
            'currency': r.currency,
            'status': r.status,
            'receipt_no': payment.receipt_no if payment else None,
            'receipt_pdf_url': f'/api/v1/member/payments/{payment.id}/receipt.pdf' if payment else None,
            'created_at': r.created_at,
        })
    return {'renewals': result, 'items': result, 'count': len(result)}


@router.post('/renewal/initiate')
def initiate_membership_renewal(
    payload: dict,
    request: Request,
    x_idempotency_key: str | None = Header(default=None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Initiate the complete membership renewal workflow:
    Select membership period -> Create payment transaction -> Gateway checkout ->
    Callback verification -> Membership renewed -> New expiry date -> Receipt.
    """
    m = get_member(user, db)
    raw_period = (
        payload.get('period_code')
        or payload.get('membership_plan_id')
        or payload.get('period')
        or 'RENEWAL_1YR'
    ).strip().upper()
    period_alias_map = {
        '1YR': 'RENEWAL_1YR',
        '1_YEAR': 'RENEWAL_1YR',
        'RENEWAL_1YR': 'RENEWAL_1YR',
        '2YR': 'RENEWAL_2YR',
        '2_YEAR': 'RENEWAL_2YR',
        'RENEWAL_2YR': 'RENEWAL_2YR',
        'LIFE': 'LIFE',
        'LIFETIME': 'LIFE',
    }
    period_code = period_alias_map.get(raw_period, raw_period)
    if period_code not in RENEWAL_PERIODS:
        raise HTTPException(400, f'Unsupported renewal period: {raw_period}')

    try:
        provider = normalize_provider(payload.get('provider') or 'SSLCOMMERZ')
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    idem_key = (payload.get('idempotency_key') or x_idempotency_key or '').strip() or None
    if idem_key:
        existing = db.scalar(select(PaymentTransaction).where(PaymentTransaction.idempotency_key == idem_key))
        if existing:
            now = datetime.utcnow()
            base_date = m.validity_date if (m.validity_date and m.validity_date > now) else now
            ext_days = resolve_renewal_days(existing.membership_plan_id, int(existing.amount))
            return {
                'id': existing.id,
                'payment_id': existing.id,
                'provider': existing.provider,
                'transaction_id': existing.transaction_ref,
                'provider_transaction_id': existing.provider_transaction_id or existing.transaction_ref,
                'checkout_url': f'/portal?payment_id={existing.id}',
                'status': existing.status,
                'amount': float(existing.amount),
                'currency': existing.currency,
                'period_code': existing.membership_plan_id,
                'membership_plan_id': existing.membership_plan_id,
                'projected_validity_date': (base_date + timedelta(days=ext_days)).strftime('%Y-%m-%d'),
                'idempotent_replay': True,
            }

    amount = resolve_plan_amount(db, period_code)
    client_amount = payload.get('amount')
    if client_amount is not None and int(client_amount) != int(amount):
        raise HTTPException(
            400,
            f'Client amount (৳{client_amount}) does not match server-calculated renewal fee (৳{amount}) for {period_code}',
        )

    item = PaymentTransaction(
        user_id=user.id,
        member_id=m.id,
        membership_plan_id=period_code,
        idempotency_key=idem_key,
        amount=int(amount),
        currency='BDT',
        provider=provider,
        purpose='RENEWAL',
        status='PENDING',
    )
    db.add(item)
    db.flush()

    try:
        checkout = create_checkout(provider, item.id, float(item.amount), item.currency)
    except (RuntimeError, PermissionError) as exc:
        db.rollback()
        raise HTTPException(503, str(exc)) from exc

    item.transaction_ref = checkout.provider_transaction_id
    log_audit_action(
        db,
        request,
        action='INITIATE_RENEWAL',
        entity='PAYMENT',
        entity_id=str(item.id),
        user=user,
        new_value={'provider': provider, 'trx_id': checkout.provider_transaction_id, 'amount': float(item.amount), 'period': period_code},
    )
    db.commit()
    db.refresh(item)

    now = datetime.utcnow()
    base_date = m.validity_date if (m.validity_date and m.validity_date > now) else now
    ext_days = resolve_renewal_days(period_code, int(item.amount))

    return {
        'id': item.id,
        'payment_id': item.id,
        'provider': provider,
        'transaction_id': checkout.provider_transaction_id,
        'provider_transaction_id': checkout.provider_transaction_id,
        'checkout_url': checkout.checkout_url,
        'status': item.status,
        'amount': float(item.amount),
        'currency': item.currency,
        'period_code': period_code,
        'membership_plan_id': period_code,
        'projected_validity_date': (base_date + timedelta(days=ext_days)).strftime('%Y-%m-%d'),
        'projected_validity_formatted': (base_date + timedelta(days=ext_days)).strftime('%d %b %Y'),
    }


@router.patch('/profile')
def update_profile(payload: MemberProfileUpdate, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = get_member(user, db)
    user.name_bn = payload.name_bn; user.name_en = payload.name_en; user.phone = payload.phone
    for field in ['designation_bn', 'designation_en', 'employee_id', 'diploma_institution', 'graduation_year', 'nid_number', 'date_of_birth', 'current_address', 'permanent_address', 'circle_id']:
        setattr(m, field, getattr(payload, field))
    audit(db, user, 'UPDATE_PROFILE', 'MEMBER', m.id, request.client.host if request.client else None)
    db.commit()
    return {'ok': True, 'id': m.id}


@router.post('/application', response_model=ApplicationResponse)
@router.post('/apply', response_model=ApplicationResponse)
def submit_application(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    from app.models import MembershipApplication
    m = get_member(user, db)
    if m.status == 'ACTIVE':
        raise HTTPException(409, 'Membership is already active')
    m.status = 'SUBMITTED'
    if not m.application_no:
        m.application_no = f'PGCB-APP-{datetime.utcnow().year}-{m.id:04d}'
    m.application_note = 'Application submitted by member.'
    app_row = db.scalar(select(MembershipApplication).where(MembershipApplication.member_id == m.id))
    if not app_row:
        db.add(
            MembershipApplication(
                member_id=m.id,
                application_no=m.application_no,
                membership_type=m.membership_type or 'GENERAL',
                circle_id=m.circle_id,
                status='SUBMITTED',
            )
        )
    else:
        app_row.status = 'SUBMITTED'
        app_row.circle_id = m.circle_id
    audit(db, user, 'SUBMIT_APPLICATION', 'MEMBER', m.id, request.client.host if request.client else None)
    officers = db.scalars(
        select(User).where(
            User.role.in_(['MEMBERSHIP_OFFICER', 'CIRCLE_ADMIN', 'CENTRAL_ADMIN', 'SUPER_ADMIN']),
            User.is_active == True,
        )
    ).all()
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
    clean_name, unique_name, resolved_ct = validate_upload_bytes(
        file.filename,
        file.content_type,
        content,
        max_bytes,
    )
    try:
        stored = save_bytes(content, f'members/{member.id}', unique_name)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    doc = MemberDocument(
        member_id=member.id, document_type=document_type, filename=clean_name,
        storage_path=stored, content_type=resolved_ct, review_status='PENDING'
    )
    db.add(doc)
    if document_type == 'PHOTO':
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
    if not doc or not doc.storage_path:
        raise HTTPException(404, 'Document not available')
    try:
        content = get_file_bytes(doc.storage_path)
        return Response(
            content=content,
            media_type=doc.content_type or 'application/octet-stream',
            headers={'Content-Disposition': f'attachment; filename="{doc.filename}"'},
        )
    except FileNotFoundError:
        raise HTTPException(404, 'Document not found')
    except ValueError:
        raise HTTPException(400, 'Invalid document path')
    except Exception as exc:
        raise HTTPException(502, f'Failed to retrieve document: {exc}')


@router.get('/notifications')
def notifications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    rows = db.scalars(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(30)
    ).all()
    return [
        {
            'id': n.id,
            'title_bn': n.title_bn,
            'body_bn': n.body_bn,
            'type': n.notification_type,
            'read_at': n.read_at,
            'is_read': bool(n.read_at),
            'indicator': '○' if n.read_at else '●',
            'created_at': n.created_at,
            'relative_time': _relative_time(n.created_at, now)[0],
            'relative_time_en': _relative_time(n.created_at, now)[0],
            'relative_time_bn': _relative_time(n.created_at, now)[1],
        }
        for n in rows
    ]


@router.get('/notifications/unread-count')
def notifications_unread_count(user: User = Depends(current_user), db: Session = Depends(get_db)):
    count = db.scalar(select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.read_at.is_(None))) or 0
    return {'unread_count': count}


@router.post('/notifications/{notification_id}/read')
def mark_notification_read(notification_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    n = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    if not n:
        raise HTTPException(404, 'Notification not found')
    n.read_at = datetime.utcnow(); db.commit()
    return {'ok': True}


@router.post('/notifications/read-all')
def mark_all_notifications_read(user: User = Depends(current_user), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    unread = db.scalars(select(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))).all()
    for n in unread:
        n.read_at = now
    db.commit()
    return {'ok': True, 'updated': len(unread)}


@router.get('/notification-preferences')
def get_notification_preferences(user: User = Depends(current_user), db: Session = Depends(get_db)):
    import json
    from app.models import SiteSetting
    defaults = {'email_enabled': True, 'sms_enabled': True, 'in_app_enabled': True}
    row = db.scalar(select(SiteSetting).where(SiteSetting.key == f'notification_prefs_user_{user.id}'))
    if row and row.value:
        try:
            defaults.update(json.loads(row.value))
        except Exception:
            pass
    return defaults


@router.put('/notification-preferences')
def update_notification_preferences(payload: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
    import json
    from app.models import SiteSetting
    prefs = {
        'email_enabled': bool(payload.get('email_enabled', True)),
        'sms_enabled': bool(payload.get('sms_enabled', True)),
        'in_app_enabled': bool(payload.get('in_app_enabled', True)),
    }
    key = f'notification_prefs_user_{user.id}'
    row = db.scalar(select(SiteSetting).where(SiteSetting.key == key))
    if row:
        row.value = json.dumps(prefs)
    else:
        db.add(SiteSetting(key=key, value=json.dumps(prefs), category='NOTIFICATION_PREFS'))
    db.commit()
    return {'ok': True, **prefs}


@router.get('/certificates')
def list_member_certificates(user: User = Depends(current_user), db: Session = Depends(get_db)):
    from app.services.certificate_service import CertificateService
    m = get_member(user, db)
    return CertificateService.ensure_member_wallet_certificates(db, user, m)



