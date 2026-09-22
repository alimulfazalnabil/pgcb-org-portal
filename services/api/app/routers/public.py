from datetime import datetime
import hashlib, hmac

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload
from fastapi.responses import FileResponse
from pathlib import Path

import uuid
from pydantic import BaseModel, EmailStr, Field
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import get_db
from app.models import Circular, Circle, CommitteeMember, ContactMessage, Document, Event, Journal, MediaAsset, Member, Notice, SiteSetting, User
from app.schemas.content import ContactCreate
from app.schemas.member import VerificationResponse
from app.services import BASE_STORAGE, EmailService
from app.utils.storage import is_local_path

router = APIRouter(prefix='/public', tags=['public'])



@router.get('/settings')
def public_settings(db: Session = Depends(get_db)):
    """Retrieve public institutional site settings."""
    rows = db.scalars(select(SiteSetting)).all()
    # Provide baseline defaults merged with database values
    settings_dict = {
        'org_name_bn': 'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)',
        'org_name_en': 'Power Grid Company of Bangladesh (PGCB)',
        'contact_email': 'info@pgcb.gov.bd',
        'contact_phone': '+880-2-9553663',
        'address_bn': 'পিজিসিবি ভবন, আফতাবনগর, ঢাকা-১২১২',
        'address_en': 'PGCB Bhaban, Aftabnagar, Dhaka-1212',
    }
    for row in rows:
        if row.value is not None:
            settings_dict[row.key] = row.value
    return settings_dict


@router.get('/members')
def public_members(
    q: str | None = Query(default=None, max_length=100),
    circle_id: int | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Public member directory with privacy protection (PII excluded)."""
    offset = (page - 1) * limit
    stmt = (
        select(Member)
        .options(selectinload(Member.user), selectinload(Member.circle))
        .where(Member.status == 'ACTIVE')
        .order_by(Member.membership_id.asc())
    )
    if circle_id:
        stmt = stmt.where(Member.circle_id == circle_id)
    if q:
        term = f'%{q.strip()}%'
        stmt = stmt.where(
            or_(
                Member.membership_id.like(term),
                Member.designation_bn.like(term),
                Member.designation_en.like(term),
                Member.employee_id.like(term),
            )
        )
    
    total = db.scalar(select(func.count(Member.id)).where(Member.status == 'ACTIVE')) or 0
    members = db.scalars(stmt.offset(offset).limit(limit)).all()
    
    return {
        'total': total,
        'page': page,
        'limit': limit,
        'items': [
            {
                'membership_id': m.membership_id,
                'name_bn': (m.user.name_bn if m.user else None) or getattr(m, 'full_name_bn', None) or '—',
                'name_en': (m.user.name_en if m.user else None) or getattr(m, 'full_name_en', None),
                'designation_bn': m.designation_bn,
                'designation_en': m.designation_en,
                'circle_name_bn': m.circle.name_bn if m.circle else None,
                'circle_name_en': m.circle.name_en if m.circle else None,
                'status': m.status,
            }
            for m in members
        ],
    }


def _verification_response(m: Member) -> VerificationResponse:
    name_bn = (m.user.name_bn if m.user else None) or getattr(m, 'full_name_bn', None) or getattr(m, 'name_bn', None) or '—'
    name_en = (m.user.name_en if m.user else None) or getattr(m, 'full_name_en', None) or getattr(m, 'name_en', None)
    circle_bn = m.circle.name_bn if m.circle else None
    validity_str = m.validity_date.strftime('%d-%m-%Y') if (m.validity_date and hasattr(m.validity_date, 'strftime')) else (str(m.validity_date)[:10] if m.validity_date else None)
    
    return VerificationResponse(
        verified=m.status == 'ACTIVE',
        name_bn=name_bn,
        name_en=name_en,
        membership_id=m.membership_id or '',
        employee_id=getattr(m, 'employee_id', None),
        designation_bn=m.designation_bn or getattr(m, 'designation_en', None),
        circle_bn=circle_bn,
        status=m.status,
        validity_date=validity_str,
        verified_at=datetime.utcnow().strftime('%d-%m-%Y %H:%M UTC'),
    )


def _verify_signature(membership_id: str, signature: str) -> bool:
    expected = hmac.new(settings.jwt_secret.encode(), membership_id.encode(), hashlib.sha256).hexdigest()[:32]
    return hmac.compare_digest(expected, signature)


@router.get('/verify/{membership_id}', response_model=VerificationResponse)
def verify(membership_id: str, db: Session = Depends(get_db)):
    stmt = select(Member).options(selectinload(Member.user), selectinload(Member.circle)).where(Member.membership_id == membership_id)
    m = db.scalar(stmt)
    if not m:
        raise HTTPException(404, 'Membership record not found')
    return _verification_response(m)


@router.get('/verify-token/{token}', response_model=VerificationResponse)
def verify_token(token: str, db: Session = Depends(get_db)):
    try:
        membership_id, signature = token.rsplit('.', 1)
    except ValueError:
        raise HTTPException(400, 'Invalid verification token')
    if not _verify_signature(membership_id, signature):
        raise HTTPException(400, 'Invalid verification token')
    stmt = select(Member).options(selectinload(Member.user), selectinload(Member.circle)).where(Member.membership_id == membership_id)
    m = db.scalar(stmt)
    if not m:
        raise HTTPException(404, 'Membership record not found')
    return _verification_response(m)



@router.get('/assets/{filename:path}')
def public_asset(filename: str):
    candidate = (BASE_STORAGE / 'public' / Path(filename).name).resolve()
    base = (BASE_STORAGE / 'public').resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        raise HTTPException(404, 'Asset not found')
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(404, 'Asset not found')
    return FileResponse(candidate)

@router.get('/circulars/{circular_id}')
def circular_detail(circular_id: int, db: Session = Depends(get_db)):
    item = db.get(Circular, circular_id)
    if not item or not item.is_published:
        raise HTTPException(404, 'Circular not found')
    return {
        'id': item.id, 'category': item.category, 'reference_no': item.reference_no,
        'title_bn': item.title_bn, 'title_en': item.title_en, 'summary_bn': item.summary_bn,
        'document_url': item.document_url, 'published_at': item.published_at, 'priority': item.priority,
    }

@router.get('/journals/{journal_id}')
def journal_detail(journal_id: int, db: Session = Depends(get_db)):
    item = db.get(Journal, journal_id)
    if not item or not item.is_published:
        raise HTTPException(404, 'Journal not found')
    return {
        'id': item.id, 'category': item.category, 'title_bn': item.title_bn, 'title_en': item.title_en,
        'author': item.author, 'edition': item.edition, 'publication_date': item.publication_date,
        'abstract_bn': item.abstract_bn, 'cover_image_url': item.cover_image_url, 'document_url': item.document_url,
    }

@router.get('/circles')
def circles(db: Session = Depends(get_db)):
    rows = db.scalars(select(Circle).where(Circle.active == True).order_by(Circle.name_bn)).all()
    return [{'id': x.id, 'name_bn': x.name_bn, 'name_en': x.name_en, 'description_bn': x.description_bn} for x in rows]


@router.get('/circles/{circle_id}/committee')
def circle_committee(circle_id: int, db: Session = Depends(get_db)):
    if not db.get(Circle, circle_id):
        raise HTTPException(404, 'Circle not found')
    rows = db.scalars(select(CommitteeMember).where(CommitteeMember.circle_id == circle_id, CommitteeMember.active == True).order_by(CommitteeMember.display_order)).all()
    return [{'id': x.id, 'name_bn': x.name_bn, 'name_en': x.name_en, 'designation_bn': x.designation_bn, 'designation_en': x.designation_en, 'photo_url': x.photo_url, 'term_start': x.term_start, 'term_end': x.term_end} for x in rows]


@router.get('/committee')
def committee(db: Session = Depends(get_db)):
    rows = db.scalars(select(CommitteeMember).where(CommitteeMember.circle_id == None, CommitteeMember.active == True).order_by(CommitteeMember.display_order)).all()
    return [{'id': x.id, 'name_bn': x.name_bn, 'name_en': x.name_en, 'designation_bn': x.designation_bn, 'designation_en': x.designation_en, 'message_bn': x.message_bn, 'photo_url': x.photo_url, 'term_start': x.term_start, 'term_end': x.term_end} for x in rows]


@router.get('/circulars')
def circulars(q: str | None = Query(default=None, max_length=100), category: str | None = None, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100)); offset = max(offset, 0)
    stmt = select(Circular).where(Circular.is_published == True).order_by(Circular.priority.desc(), Circular.published_at.desc()).limit(limit).offset(offset)
    if category: stmt = stmt.where(Circular.category == category)
    if q:
        like = f'%{q}%'; stmt = stmt.where(or_(Circular.title_bn.like(like), Circular.title_en.like(like), Circular.summary_bn.like(like), Circular.reference_no.like(like)))
    rows = db.scalars(stmt).all()
    return [{'id': x.id, 'category': x.category, 'reference_no': x.reference_no, 'title_bn': x.title_bn, 'title_en': x.title_en, 'summary_bn': x.summary_bn, 'document_url': x.document_url, 'published_at': x.published_at, 'priority': x.priority} for x in rows]


@router.get('/journals')
def journals(q: str | None = Query(default=None, max_length=100), limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100)); offset = max(offset, 0)
    stmt = select(Journal).where(Journal.is_published == True).order_by(Journal.publication_date.desc()).limit(limit).offset(offset)
    if q:
        like = f'%{q}%'; stmt = stmt.where(or_(Journal.title_bn.like(like), Journal.title_en.like(like), Journal.author.like(like), Journal.abstract_bn.like(like)))
    rows = db.scalars(stmt).all()
    return [{'id': x.id, 'category': x.category, 'title_bn': x.title_bn, 'title_en': x.title_en, 'author': x.author, 'edition': x.edition, 'publication_date': x.publication_date, 'abstract_bn': x.abstract_bn, 'cover_image_url': x.cover_image_url, 'document_url': x.document_url} for x in rows]


@router.get('/events')
def events(upcoming: bool = False, limit: int = 50, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    stmt = select(Event).where(Event.is_published == True).order_by(Event.event_date.asc() if upcoming else Event.event_date.desc()).limit(limit)
    if upcoming: stmt = stmt.where(Event.event_date >= datetime.utcnow())
    rows = db.scalars(stmt).all()
    return [{'id': x.id, 'title_bn': x.title_bn, 'title_en': x.title_en, 'description_bn': x.description_bn, 'event_date': x.event_date, 'location_bn': x.location_bn, 'cover_image_url': x.cover_image_url, 'registration_enabled': x.registration_enabled, 'capacity': x.capacity, 'registration_deadline': x.registration_deadline, 'fee_amount': x.fee_amount, 'fee_currency': x.fee_currency} for x in rows]


@router.get('/media')
def media(media_type: str | None = None, limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 200)); offset = max(0, offset)
    stmt = select(MediaAsset).where(MediaAsset.published == True).order_by(MediaAsset.created_at.desc()).limit(limit).offset(offset)
    if media_type: stmt = stmt.where(MediaAsset.media_type == media_type)
    rows = db.scalars(stmt).all()
    return [{'id': x.id, 'media_type': x.media_type, 'title_bn': x.title_bn, 'description_bn': x.description_bn, 'url': x.url, 'thumbnail_url': x.thumbnail_url, 'event_id': x.event_id} for x in rows]




@router.get('/search')
def site_search(q: str = Query(..., min_length=2, max_length=100), limit: int = Query(30, ge=1, le=60), db: Session = Depends(get_db)):
    """Search publicly published content: notices, circulars, journals, documents, events, media."""
    term = f'%{q.strip()}%'
    per_type = max(4, min(15, limit // 5 or 4))
    results: list[dict] = []

    # Notices
    notice_rows = db.scalars(
        select(Notice)
        .where(
            Notice.is_published == True,
            or_(Notice.title_bn.like(term), Notice.title_en.like(term), Notice.content_bn.like(term)),
        )
        .order_by(Notice.is_pinned.desc(), Notice.published_at.desc())
        .limit(per_type)
    ).all()
    for x in notice_rows:
        results.append({'type': 'NOTICE', 'id': x.id, 'title_bn': x.title_bn, 'summary_bn': x.content_bn[:150] if x.content_bn else '', 'date': x.published_at, 'href': f'/notices/{x.id}'})

    # Documents
    doc_rows = db.scalars(
        select(Document)
        .where(
            Document.is_published == True,
            or_(Document.title_bn.like(term), Document.title_en.like(term), Document.description_bn.like(term)),
        )
        .order_by(Document.created_at.desc())
        .limit(per_type)
    ).all()
    for x in doc_rows:
        results.append({'type': 'DOCUMENT', 'id': x.id, 'title_bn': x.title_bn, 'summary_bn': x.description_bn or '', 'date': x.created_at, 'href': f'/documents'})

    circular_rows = db.scalars(
        select(Circular)
        .where(
            Circular.is_published == True,
            or_(Circular.title_bn.like(term), Circular.title_en.like(term), Circular.summary_bn.like(term), Circular.reference_no.like(term)),
        )
        .order_by(Circular.priority.desc(), Circular.published_at.desc())
        .limit(per_type)
    ).all()
    for x in circular_rows:
        results.append({'type': 'CIRCULAR', 'id': x.id, 'title_bn': x.title_bn, 'summary_bn': x.summary_bn, 'date': x.published_at, 'href': f'/circulars/{x.id}'})

    journal_rows = db.scalars(
        select(Journal)
        .where(
            Journal.is_published == True,
            or_(Journal.title_bn.like(term), Journal.title_en.like(term), Journal.author.like(term), Journal.abstract_bn.like(term)),
        )
        .order_by(Journal.publication_date.desc())
        .limit(per_type)
    ).all()
    for x in journal_rows:
        results.append({'type': 'JOURNAL', 'id': x.id, 'title_bn': x.title_bn, 'summary_bn': x.abstract_bn, 'date': x.publication_date, 'href': f'/journal/{x.id}'})

    event_rows = db.scalars(
        select(Event)
        .where(
            Event.is_published == True,
            or_(Event.title_bn.like(term), Event.title_en.like(term), Event.description_bn.like(term), Event.location_bn.like(term)),
        )
        .order_by(Event.event_date.desc())
        .limit(per_type)
    ).all()
    for x in event_rows:
        results.append({'type': 'EVENT', 'id': x.id, 'title_bn': x.title_bn, 'summary_bn': x.description_bn, 'date': x.event_date, 'href': f'/events/{x.id}'})

    media_rows = db.scalars(
        select(MediaAsset)
        .where(
            MediaAsset.published == True,
            or_(MediaAsset.title_bn.like(term), MediaAsset.description_bn.like(term)),
        )
        .order_by(MediaAsset.created_at.desc())
        .limit(per_type)
    ).all()
    for x in media_rows:
        results.append({'type': 'MEDIA', 'id': x.id, 'title_bn': x.title_bn, 'summary_bn': x.description_bn, 'date': x.created_at, 'href': '/media'})

    results.sort(key=lambda item: item.get('date') or datetime.min, reverse=True)
    return {'query': q.strip(), 'count': min(len(results), limit), 'results': results[:limit]}


@router.get('/stats')
def public_stats(db: Session = Depends(get_db)):
    active_members = db.scalar(select(func.count(Member.id)).where(Member.status == 'ACTIVE')) or 0
    active_circles = db.scalar(select(func.count(Circle.id)).where(Circle.active == True)) or 0
    publications = db.scalar(select(func.count(Journal.id)).where(Journal.is_published == True)) or 0
    upcoming_events = db.scalar(select(func.count(Event.id)).where(Event.is_published == True, Event.event_date >= datetime.utcnow())) or 0
    notices_count = db.scalar(select(func.count(Notice.id)).where(Notice.is_published == True)) or 0
    documents_count = db.scalar(select(func.count(Document.id)).where(Document.is_published == True)) or 0
    return {
        'active_members': active_members,
        'active_circles': active_circles,
        'publications': publications,
        'upcoming_events': upcoming_events,
        'notices_count': notices_count,
        'documents_count': documents_count,
    }

@router.post('/contact')
def contact(payload: ContactCreate, db: Session = Depends(get_db)):
    item = ContactMessage(name=payload.name, email=payload.email.lower(), phone=payload.phone, subject=payload.subject, message=payload.message)
    db.add(item); db.commit(); db.refresh(item)
    return {'ok': True, 'message_id': item.id}


class PublicMembershipApplyRequest(BaseModel):
    name_bn: str = Field(min_length=2, max_length=200)
    name_en: str | None = None
    email: EmailStr
    phone: str = Field(min_length=11, max_length=20)
    employee_id: str | None = None
    designation_bn: str = Field(min_length=2, max_length=200)
    circle_id: int | None = None
    diploma_institution: str | None = None
    graduation_year: int | None = None
    nid_number: str | None = None
    date_of_birth: datetime | None = None
    current_address: str | None = None
    permanent_address: str | None = None
    membership_type: str = "GENERAL"
    password: str = Field(min_length=8, max_length=128)


@router.post('/membership/apply')
def public_membership_apply(payload: PublicMembershipApplyRequest, db: Session = Depends(get_db)):
    """Public multi-step membership application submission."""
    email = payload.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(
            status_code=409,
            detail='এই ইমেইল ঠিকানাটি দিয়ে ইতোমধ্যে একটি একাউন্ট খোলা আছে। অনুগ্রহ করে লগইন করুন।'
        )

    # Generate sequential or unique application tracking number
    year = datetime.utcnow().year
    app_no = f"APP-{year}-{uuid.uuid4().hex[:6].upper()}"

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        name_bn=payload.name_bn,
        name_en=payload.name_en,
        phone=payload.phone,
        role='MEMBER',
        is_active=True,
        email_verified=False,
    )
    db.add(user)
    db.flush()

    member = Member(
        user_id=user.id,
        application_no=app_no,
        employee_id=payload.employee_id,
        designation_bn=payload.designation_bn,
        designation_en=payload.name_en,
        circle_id=payload.circle_id,
        diploma_institution=payload.diploma_institution,
        graduation_year=payload.graduation_year,
        nid_number=payload.nid_number,
        date_of_birth=payload.date_of_birth,
        current_address=payload.current_address,
        permanent_address=payload.permanent_address,
        membership_type=payload.membership_type,
        status='SUBMITTED',
        application_note='আবেদনটি সফলভাবে জমা হয়েছে এবং প্রাথমিক পর্যালোচনার অপেক্ষায় রয়েছে।',
    )
    db.add(member)
    db.commit()

    # Send confirmation email
    try:
        EmailService.send_application_submitted(
            to_email=user.email,
            name=user.name_bn,
            application_no=app_no,
        )
    except Exception:
        pass

    return {
        'ok': True,
        'application_no': app_no,
        'message': 'আপনার আবেদনটি সফলভাবে জমা হয়েছে। ট্র্যাকিং নম্বরটি সংরক্ষণ করুন।',
    }


@router.get('/membership/track/{application_no}')
def track_membership_application(application_no: str, db: Session = Depends(get_db)):
    """Track the verification and review progress of a membership application."""
    normalized_app_no = application_no.strip().upper()
    member = db.scalar(
        select(Member)
        .options(selectinload(Member.circle), selectinload(Member.user))
        .where(Member.application_no == normalized_app_no)
    )
    if not member:
        raise HTTPException(
            status_code=404,
            detail=f"আবেদন নম্বর '{application_no}' সঠিক নয় বা ডাটাবেজে পাওয়া যায়নি।"
        )

    user_name = member.user.name_bn if member.user else ''
    masked_name = user_name[0] + '***' if len(user_name) > 1 else '—'

    # Build clear chronological steps
    is_active = member.status == 'ACTIVE'
    is_rejected = member.status == 'REJECTED'
    is_under_review = member.status in ('UNDER_REVIEW', 'ACTION_REQUIRED')

    timeline = [
        {
            'step': 1,
            'title': 'আবেদন দাখিল সম্পন্ন (Application Submitted)',
            'status': 'COMPLETED',
            'date': member.created_at.strftime('%d-%m-%Y %H:%M') if member.created_at else None,
            'description': 'আবেদনপত্র সিস্টেমে সফলভাবে গৃহীত হয়েছে।'
        },
        {
            'step': 2,
            'title': 'নথি ও তথ্যাদি যাচাইকরণ (Document Verification)',
            'status': 'COMPLETED' if is_active else ('IN_PROGRESS' if is_under_review or member.status == 'SUBMITTED' else 'PENDING'),
            'date': member.updated_at.strftime('%d-%m-%Y %H:%M') if member.updated_at and member.status != 'SUBMITTED' else None,
            'description': 'সার্কেল ও কেন্দ্রীয় কর্মকর্তা কর্তৃক এনআইডি ও শিক্ষাগত যোগ্যতা পর্যালোচনা।'
        },
        {
            'step': 3,
            'title': 'কার্যনির্বাহী পরিষদ অনুমোদন (Final Approval)',
            'status': 'COMPLETED' if is_active else ('REJECTED' if is_rejected else 'PENDING'),
            'date': member.issue_date.strftime('%d-%m-%Y') if member.issue_date and is_active else None,
            'description': 'সদস্যপদ সক্রিয়করণ ও ডিজিটাল সদস্য আইডি প্রদান।'
        }
    ]

    return {
        'application_no': member.application_no,
        'status': member.status,
        'applicant_name_masked': masked_name,
        'circle_bn': member.circle.name_bn if member.circle else 'অনির্ধারিত',
        'submission_date': member.created_at.strftime('%d-%m-%Y') if member.created_at else None,
        'application_note': member.application_note,
        'timeline': timeline,
        'membership_id': member.membership_id if is_active else None,
    }


