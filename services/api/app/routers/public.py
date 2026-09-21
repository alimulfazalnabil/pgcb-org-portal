from datetime import datetime
import hashlib, hmac

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload
from fastapi.responses import FileResponse
from pathlib import Path

from app.core.config import settings
from app.db.session import get_db
from app.models import Circular, Circle, CommitteeMember, ContactMessage, Event, Journal, MediaAsset, Member
from app.schemas.content import ContactCreate
from app.schemas.member import VerificationResponse
from app.services import BASE_STORAGE
from app.utils.storage import is_local_path

router = APIRouter(prefix='/public', tags=['public'])


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
    """Search only publicly published content; never query members or private documents."""
    term = f'%{q.strip()}%'
    per_type = max(5, min(20, limit // 3 or 5))
    results: list[dict] = []

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
    from sqlalchemy import func
    active_members = db.scalar(select(func.count(Member.id)).where(Member.status == 'ACTIVE')) or 0
    active_circles = db.scalar(select(func.count(Circle.id)).where(Circle.active == True)) or 0
    publications = db.scalar(select(func.count(Journal.id)).where(Journal.is_published == True)) or 0
    upcoming_events = db.scalar(select(func.count(Event.id)).where(Event.is_published == True, Event.event_date >= datetime.utcnow())) or 0
    return {
        'active_members': active_members,
        'active_circles': active_circles,
        'publications': publications,
        'upcoming_events': upcoming_events,
    }

@router.post('/contact')
def contact(payload: ContactCreate, db: Session = Depends(get_db)):
    item = ContactMessage(name=payload.name, email=payload.email.lower(), phone=payload.phone, subject=payload.subject, message=payload.message)
    db.add(item); db.commit(); db.refresh(item)
    return {'ok': True, 'message_id': item.id}
