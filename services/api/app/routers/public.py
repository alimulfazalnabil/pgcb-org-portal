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
    """Public member directory with privacy protection (PII excluded) and consistent filtered pagination."""
    offset = (page - 1) * limit
    filters = [Member.status == 'ACTIVE']
    if circle_id is not None:
        filters.append(Member.circle_id == circle_id)
    if q and q.strip():
        term = f'%{q.strip()}%'
        filters.append(
            or_(
                User.name_bn.like(term),
                User.name_en.like(term),
                Member.membership_id.like(term),
                Member.designation_bn.like(term),
                Member.designation_en.like(term),
                Member.employee_id.like(term),
            )
        )

    count_stmt = (
        select(func.count(Member.id))
        .select_from(Member)
        .join(User, Member.user_id == User.id)
        .where(*filters)
    )
    total = db.scalar(count_stmt) or 0

    data_stmt = (
        select(Member)
        .join(User, Member.user_id == User.id)
        .options(selectinload(Member.user), selectinload(Member.circle))
        .where(*filters)
        .order_by(Member.membership_id.asc())
        .offset(offset)
        .limit(limit)
    )
    members = db.scalars(data_stmt).all()

    return {
        'total': total,
        'page': page,
        'limit': limit,
        'pages': (total + limit - 1) // limit if limit > 0 else 0,
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
    is_expired_by_date = False
    if m.validity_date:
        val_date = m.validity_date.date() if hasattr(m.validity_date, 'date') else m.validity_date
        if hasattr(val_date, 'year') and val_date < datetime.utcnow().date():
            is_expired_by_date = True
    effective_status = 'EXPIRED' if (m.status == 'EXPIRED' or is_expired_by_date) else m.status

    return VerificationResponse(
        verified=(effective_status == 'ACTIVE'),
        name_bn=name_bn,
        name_en=name_en,
        membership_id=m.membership_id or '',
        employee_id=getattr(m, 'employee_id', None),
        designation_bn=m.designation_bn or getattr(m, 'designation_en', None),
        circle_bn=circle_bn,
        status=effective_status,
        validity_date=validity_str,
        verified_at=datetime.utcnow().strftime('%d-%m-%Y %H:%M UTC'),
    )


def _verify_signature(membership_id: str, signature: str) -> bool:
    expected = hmac.new(settings.jwt_secret.encode(), membership_id.encode(), hashlib.sha256).hexdigest()[:32]
    return hmac.compare_digest(expected, signature)


@router.get('/verify/{membership_id}', response_model=VerificationResponse)
@router.get('/verify-member/{membership_id}', response_model=VerificationResponse)
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
    if not filename or '\x00' in filename or '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(400, 'Invalid asset path')
    clean = Path(filename).name
    roots = [BASE_STORAGE / 'public']
    if getattr(settings, 'upload_dir', None):
        roots.insert(0, Path(settings.upload_dir) / 'public')
    for base_dir in roots:
        base = base_dir.resolve()
        candidate = (base / clean).resolve()
        try:
            candidate.relative_to(base)
        except ValueError:
            continue
        if candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
    raise HTTPException(404, 'Asset not found')

@router.get('/circulars/{circular_id}')
def circular_detail(circular_id: int, db: Session = Depends(get_db)):
    import json
    item = db.get(Circular, circular_id)
    if not item or not item.is_published:
        raise HTTPException(404, 'Circular not found')
    meta_row = db.scalar(select(SiteSetting).where(SiteSetting.key == f'circular_meta:{circular_id}'))
    meta = {
        'issuing_authority': 'কেন্দ্রীয় কার্যনির্বাহী পরিষদ, পিজিসিবি',
        'effective_date': item.published_at.strftime('%Y-%m-%d') if item.published_at else None,
        'target_audience': 'ALL_MEMBERS',
        'related_circular_id': None,
        'superseded_circular_id': None,
    }
    if meta_row and meta_row.value:
        try:
            meta.update(json.loads(meta_row.value))
        except Exception:
            pass
    return {
        'id': item.id, 'category': item.category, 'reference_no': item.reference_no,
        'title_bn': item.title_bn, 'title_en': item.title_en, 'summary_bn': item.summary_bn,
        'document_url': item.document_url, 'published_at': item.published_at, 'priority': item.priority,
        **meta,
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
    member_counts = dict(
        db.execute(
            select(Member.circle_id, func.count(Member.id))
            .where(Member.status == 'ACTIVE')
            .group_by(Member.circle_id)
        ).all()
    )
    return [
        {
            'id': x.id,
            'name_bn': x.name_bn,
            'name_en': x.name_en,
            'slug': (x.name_en or f'circle-{x.id}').lower().replace(' ', '-'),
            'description_bn': x.description_bn,
            'active_members': member_counts.get(x.id, 0),
        }
        for x in rows
    ]


@router.get('/circles/{circle_id}')
def circle_detail(circle_id: int, db: Session = Depends(get_db)):
    circle = db.get(Circle, circle_id)
    if not circle or not circle.active:
        raise HTTPException(404, 'Circle not found')

    active_count = db.scalar(select(func.count(Member.id)).where(Member.circle_id == circle.id, Member.status == 'ACTIVE')) or 0
    pending_count = db.scalar(select(func.count(Member.id)).where(Member.circle_id == circle.id, Member.status.in_(['PENDING', 'SUBMITTED', 'UNDER_REVIEW']))) or 0
    committee_rows = db.scalars(select(CommitteeMember).where(CommitteeMember.circle_id == circle.id, CommitteeMember.active == True).order_by(CommitteeMember.display_order)).all()
    circle_admin = db.scalar(
        select(User)
        .join(Member, Member.user_id == User.id)
        .where(Member.circle_id == circle.id, User.role == 'CIRCLE_ADMIN', User.is_active == True)
    )
    recent_notices = db.scalars(select(Notice).where(Notice.is_published == True).order_by(Notice.published_at.desc()).limit(5)).all()
    recent_events = db.scalars(select(Event).where(Event.is_published == True).order_by(Event.event_date.desc()).limit(5)).all()

    return {
        'id': circle.id,
        'name_bn': circle.name_bn,
        'name_en': circle.name_en,
        'description_bn': circle.description_bn,
        'circle_administrator': {
            'name_bn': circle_admin.name_bn,
            'name_en': circle_admin.name_en,
            'email': circle_admin.email,
        } if circle_admin else None,
        'statistics': {
            'active_members': active_count,
            'pending_members': pending_count,
            'committee_size': len(committee_rows),
        },
        'contact': {
            'office_bn': f'পিজিসিবি {circle.name_bn} আঞ্চলিক কার্যালয়',
            'email': f"{(circle.name_en or 'circle').lower().split()[0]}@pgcb.org.bd",
            'phone': '+880-2-9553663',
        },
        'committee': [
            {
                'id': c.id,
                'name_bn': c.name_bn,
                'name_en': c.name_en,
                'designation_bn': c.designation_bn,
                'designation_en': c.designation_en,
                'photo_url': c.photo_url,
            }
            for c in committee_rows
        ],
        'notices': [{'id': n.id, 'title_bn': n.title_bn, 'published_at': n.published_at} for n in recent_notices],
        'events': [{'id': e.id, 'title_bn': e.title_bn, 'event_date': e.event_date, 'location_bn': e.location_bn} for e in recent_events],
    }


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


@router.get('/notices')
def public_notices(category: str | None = None, priority: str | None = None, limit: int = 20, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    stmt = select(Notice).where(Notice.is_published == True).order_by(Notice.is_pinned.desc(), Notice.published_at.desc(), Notice.created_at.desc()).limit(limit)
    if category:
        stmt = stmt.where(Notice.category == category.upper())
    if priority:
        stmt = stmt.where(Notice.priority == priority.upper())
    rows = db.scalars(stmt).all()
    return [
        {
            'id': n.id,
            'title_bn': n.title_bn,
            'title_en': n.title_en,
            'content_bn': n.content_bn,
            'content_en': n.content_en,
            'priority': n.priority,
            'category': n.category,
            'attachment_url': n.attachment_url,
            'is_pinned': n.is_pinned,
            'is_published': n.is_published,
            'published_at': n.published_at,
        }
        for n in rows
    ]


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


def _normalize_bangla(text_val: str | None) -> str:
    import unicodedata
    if not text_val:
        return ''
    s = unicodedata.normalize('NFC', text_val.strip().lower())
    s = s.replace('\u09af\u09bc', '\u09df').replace('\u09a1\u09bc', '\u09dc').replace('\u09a2\u09bc', '\u09dd')
    return s


def _compute_relevance(query_norm: str, tokens: list[str], title: str | None, summary: str | None) -> float:
    from difflib import SequenceMatcher
    t_norm = _normalize_bangla(title)
    s_norm = _normalize_bangla(summary)
    score = 0.0
    if query_norm and query_norm == t_norm:
        score += 100.0
    elif query_norm and t_norm.startswith(query_norm):
        score += 80.0
    elif query_norm and query_norm in t_norm:
        score += 65.0
    elif query_norm and query_norm in s_norm:
        score += 40.0

    for tok in tokens:
        if len(tok) < 2:
            continue
        if tok in t_norm:
            score += 25.0
        elif tok in s_norm:
            score += 12.0
        else:
            # Typo tolerance check against title words
            for word in t_norm.split():
                if len(word) >= 3 and SequenceMatcher(None, tok, word).ratio() >= 0.76:
                    score += 15.0
                    break
    return round(score, 2)


@router.get('/search/suggestions')
def search_suggestions(q: str = Query(..., min_length=1, max_length=100), db: Session = Depends(get_db)):
    from app.models.core import News
    norm = _normalize_bangla(q)
    like = f'%{norm}%'
    suggestions: list[str] = []
    for title in db.scalars(select(Notice.title_bn).where(Notice.is_published == True, Notice.title_bn.like(like)).limit(4)).all():
        if title and title not in suggestions:
            suggestions.append(title)
    for title in db.scalars(select(Circular.title_bn).where(Circular.is_published == True, Circular.title_bn.like(like)).limit(4)).all():
        if title and title not in suggestions:
            suggestions.append(title)
    for title in db.scalars(select(News.title_bn).where(News.is_published == True, News.title_bn.like(like)).limit(3)).all():
        if title and title not in suggestions:
            suggestions.append(title)
    for title in db.scalars(select(Event.title_bn).where(Event.is_published == True, Event.title_bn.like(like)).limit(3)).all():
        if title and title not in suggestions:
            suggestions.append(title)
    for cname in db.scalars(select(Circle.name_bn).where(Circle.active == True, or_(Circle.name_bn.like(like), Circle.name_en.like(like))).limit(3)).all():
        if cname and cname not in suggestions:
            suggestions.append(cname)
    return {'query': q.strip(), 'suggestions': suggestions[:10]}


@router.get('/search')
def site_search(
    q: str = Query(..., min_length=2, max_length=100),
    type: str | None = Query(default=None, description='Filter by entity type: MEMBER, CIRCULAR, NOTICE, NEWS, EVENT, DOCUMENT, JOURNAL, COMMITTEE, CIRCLE, CERTIFICATE'),
    category: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(30, ge=1, le=60),
    db: Session = Depends(get_db),
):
    """Unified search across institutional content domains with Bangla normalization, typo tolerance, filters, and relevance ranking."""
    from app.models import Certificate
    from app.models.core import News

    query_norm = _normalize_bangla(q)
    tokens = [t for t in query_norm.split() if len(t) >= 2] or [query_norm]
    primary_term = f'%{tokens[0]}%'
    type_filter = type.strip().upper() if type else None
    per_type = max(5, min(20, limit // 3 or 6))
    results: list[dict] = []

    def _type_wanted(t: str) -> bool:
        return not type_filter or type_filter == t

    def _token_or(*cols):
        preds = []
        for tok in tokens[:4]:
            like = f'%{tok}%'
            for col in cols:
                preds.append(col.like(like))
        return or_(*preds) if preds else True

    # 1. Notices
    if _type_wanted('NOTICE'):
        stmt = select(Notice).where(Notice.is_published == True, _token_or(Notice.title_bn, Notice.title_en, Notice.content_bn))
        if category:
            stmt = stmt.where(Notice.category == category.upper())
        for x in db.scalars(stmt.order_by(Notice.is_pinned.desc(), Notice.published_at.desc()).limit(per_type)).all():
            results.append({'type': 'NOTICE', 'id': x.id, 'category': x.category, 'title_bn': x.title_bn, 'summary_bn': x.content_bn[:150] if x.content_bn else '', 'date': x.published_at, 'href': f'/notices/{x.id}'})

    # 1b. News
    if _type_wanted('NEWS'):
        stmt = select(News).where(News.is_published == True, _token_or(News.title_bn, News.title_en, News.summary_bn, News.content_bn, News.tags))
        if category:
            stmt = stmt.where(News.category == category.upper())
        for x in db.scalars(stmt.order_by(News.is_featured.desc(), News.published_at.desc()).limit(per_type)).all():
            results.append({'type': 'NEWS', 'id': x.id, 'category': x.category, 'title_bn': x.title_bn, 'summary_bn': x.summary_bn or (x.content_bn[:150] if x.content_bn else ''), 'date': x.published_at, 'href': f'/news/{x.slug}'})

    # 2. Documents
    if _type_wanted('DOCUMENT'):
        stmt = select(Document).where(Document.is_published == True, _token_or(Document.title_bn, Document.title_en, Document.description_bn))
        if category:
            stmt = stmt.where(Document.category == category.upper())
        for x in db.scalars(stmt.order_by(Document.created_at.desc()).limit(per_type)).all():
            results.append({'type': 'DOCUMENT', 'id': x.id, 'category': x.category, 'title_bn': x.title_bn, 'summary_bn': x.description_bn or '', 'date': x.created_at, 'href': '/documents'})

    # 3. Circulars
    if _type_wanted('CIRCULAR'):
        stmt = select(Circular).where(Circular.is_published == True, _token_or(Circular.title_bn, Circular.title_en, Circular.summary_bn, Circular.reference_no))
        if category:
            stmt = stmt.where(Circular.category == category.upper())
        for x in db.scalars(stmt.order_by(Circular.priority.desc(), Circular.published_at.desc()).limit(per_type)).all():
            results.append({'type': 'CIRCULAR', 'id': x.id, 'category': x.category, 'title_bn': x.title_bn, 'summary_bn': x.summary_bn, 'date': x.published_at, 'href': f'/circulars/{x.id}'})

    # 4. Journals
    if _type_wanted('JOURNAL'):
        stmt = select(Journal).where(Journal.is_published == True, _token_or(Journal.title_bn, Journal.title_en, Journal.author, Journal.abstract_bn))
        if category:
            stmt = stmt.where(Journal.category == category.upper())
        for x in db.scalars(stmt.order_by(Journal.publication_date.desc()).limit(per_type)).all():
            results.append({'type': 'JOURNAL', 'id': x.id, 'category': x.category, 'title_bn': x.title_bn, 'summary_bn': x.abstract_bn, 'date': x.publication_date, 'href': f'/journal/{x.id}'})

    # 5. Events
    if _type_wanted('EVENT'):
        stmt = select(Event).where(Event.is_published == True, _token_or(Event.title_bn, Event.title_en, Event.description_bn, Event.location_bn))
        for x in db.scalars(stmt.order_by(Event.event_date.desc()).limit(per_type)).all():
            results.append({'type': 'EVENT', 'id': x.id, 'category': 'EVENT', 'title_bn': x.title_bn, 'summary_bn': x.description_bn, 'date': x.event_date, 'href': f'/events/{x.id}'})

    # 6. Members (Active public directory)
    if _type_wanted('MEMBER'):
        stmt = (
            select(Member)
            .join(User, Member.user_id == User.id)
            .options(selectinload(Member.user), selectinload(Member.circle))
            .where(Member.status == 'ACTIVE', _token_or(User.name_bn, User.name_en, Member.membership_id, Member.designation_bn, Member.designation_en))
            .limit(per_type)
        )
        for m in db.scalars(stmt).all():
            results.append({
                'type': 'MEMBER',
                'id': m.id,
                'category': m.membership_type,
                'title_bn': f"{m.user.name_bn if m.user else '—'} ({m.membership_id or ''})",
                'summary_bn': f"{m.designation_bn or ''} • {m.circle.name_bn if m.circle else ''}".strip(' •'),
                'date': m.issue_date or m.created_at,
                'href': f"/members?q={m.membership_id or ''}",
            })

    # 7. Committee
    if _type_wanted('COMMITTEE'):
        stmt = select(CommitteeMember).where(CommitteeMember.active == True, _token_or(CommitteeMember.name_bn, CommitteeMember.name_en, CommitteeMember.designation_bn, CommitteeMember.designation_en)).limit(per_type)
        for c in db.scalars(stmt).all():
            results.append({'type': 'COMMITTEE', 'id': c.id, 'category': 'COMMITTEE', 'title_bn': c.name_bn, 'summary_bn': c.designation_bn, 'date': c.created_at, 'href': '/committee'})

    # 8. Grid Circles
    if _type_wanted('CIRCLE'):
        stmt = select(Circle).where(Circle.active == True, _token_or(Circle.name_bn, Circle.name_en, Circle.description_bn)).limit(per_type)
        for cir in db.scalars(stmt).all():
            results.append({'type': 'CIRCLE', 'id': cir.id, 'category': 'CIRCLE', 'title_bn': f"{cir.name_bn} ({cir.name_en})", 'summary_bn': cir.description_bn or '', 'date': cir.created_at, 'href': '/circles'})

    # 9. Certificates
    if _type_wanted('CERTIFICATE'):
        stmt = select(Certificate).where(_token_or(Certificate.certificate_no, Certificate.recipient_name, Certificate.title_bn)).limit(per_type)
        for cert in db.scalars(stmt).all():
            results.append({'type': 'CERTIFICATE', 'id': cert.id, 'category': 'CERTIFICATE', 'title_bn': f"{cert.certificate_no} — {cert.recipient_name}", 'summary_bn': cert.title_bn, 'date': cert.issue_date, 'href': '/certificates/verify'})

    # Media fallback
    if _type_wanted('MEDIA'):
        for x in db.scalars(select(MediaAsset).where(MediaAsset.published == True, _token_or(MediaAsset.title_bn, MediaAsset.description_bn)).order_by(MediaAsset.created_at.desc()).limit(per_type)).all():
            results.append({'type': 'MEDIA', 'id': x.id, 'category': x.media_type, 'title_bn': x.title_bn, 'summary_bn': x.description_bn, 'date': x.created_at, 'href': '/media'})

    # Date filtering + Relevance Ranking
    filtered: list[dict] = []
    for item in results:
        dt = item.get('date')
        if date_from and dt and dt < date_from:
            continue
        if date_to and dt and dt > date_to:
            continue
        item['relevance_score'] = _compute_relevance(query_norm, tokens, item.get('title_bn'), item.get('summary_bn'))
        filtered.append(item)

    filtered.sort(key=lambda item: (item.get('relevance_score', 0.0), item.get('date') or datetime.min), reverse=True)
    sliced = filtered[:limit]
    return {
        'query': q.strip(),
        'normalized_query': query_norm,
        'filters': {'type': type_filter, 'category': category},
        'count': len(sliced),
        'total': len(filtered),
        'results': sliced,
        'items': sliced,
    }


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
    from app.models import ContactInquiryMeta
    item = ContactMessage(name=payload.name, email=payload.email.lower(), phone=payload.phone, subject=payload.subject, message=payload.message)
    db.add(item); db.flush()
    year = datetime.utcnow().year
    ticket_no = f'PGCB-REQ-{year}-{item.id:06d}'
    meta = ContactInquiryMeta(message_id=item.id, ticket_no=ticket_no, status='NEW')
    db.add(meta)
    db.commit(); db.refresh(item)
    return {'ok': True, 'message_id': item.id, 'ticket_no': ticket_no, 'status': 'NEW'}


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


