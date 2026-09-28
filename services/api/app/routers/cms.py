from __future__ import annotations

from datetime import datetime
import io
import json
import re
from typing import Any
from xml.sax.saxutils import escape as xml_escape

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.rbac import has_permission, require_permission
from app.db.session import get_db
from app.models import (
    Announcement,
    Circle,
    Circular,
    CommitteeMember,
    ContactInquiryMeta,
    ContactMessage,
    ContentRevision,
    ContentWorkflow,
    Document,
    Event,
    EventRegistration,
    Journal,
    MediaAsset,
    Member,
    Notice,
    Notification,
    SEOMetadata,
    SiteSetting,
    User,
)
from app.domain.notifications import queue_delivery
from app.integrations.notifications import DeliveryResult, create_in_app, record_delivery
from app.models.core import News
from app.services import audit
from app.utils.storage import save_bytes

router = APIRouter(tags=['cms'])


def _slugify(text_val: str, fallback_prefix: str = 'news') -> str:
    cleaned = re.sub(r'[^\w\s-]', '', (text_val or '').strip().lower())
    slug = re.sub(r'[-\s]+', '-', cleaned).strip('-')
    if not slug:
        slug = f'{fallback_prefix}-{int(datetime.utcnow().timestamp())}'
    return slug[:180]


def record_content_revision(
    db: Session,
    entity_type: str,
    entity_id: int,
    status: str,
    title_bn: str | None = None,
    title_en: str | None = None,
    content_snapshot: dict[str, Any] | str | None = None,
    changed_by: int | None = None,
    approved_by: int | None = None,
    published_by: int | None = None,
    change_note: str | None = None,
) -> ContentRevision:
    typ = entity_type.upper()
    current_max = db.scalar(
        select(func.max(ContentRevision.version_no)).where(
            ContentRevision.entity_type == typ,
            ContentRevision.entity_id == entity_id,
        )
    ) or 0
    snapshot_str = (
        json.dumps(content_snapshot, ensure_ascii=False, default=str)
        if isinstance(content_snapshot, dict)
        else content_snapshot
    )
    rev = ContentRevision(
        entity_type=typ,
        entity_id=entity_id,
        version_no=int(current_max) + 1,
        status=status,
        title_bn=title_bn,
        title_en=title_en,
        content_snapshot=snapshot_str,
        changed_by=changed_by,
        approved_by=approved_by,
        published_by=published_by,
        change_note=change_note,
    )
    db.add(rev)
    return rev


def _user_prefs(db: Session, user_id: int) -> dict[str, bool]:
    defaults = {'in_app_enabled': True, 'email_enabled': True, 'sms_enabled': False}
    row = db.scalar(select(SiteSetting).where(SiteSetting.key == f'notification_prefs_user_{user_id}'))
    if row and row.value:
        try:
            defaults.update(json.loads(row.value))
        except Exception:
            pass
    return defaults


def notify_members_of_publication(
    db: Session,
    entity_type: str,
    entity_id: int,
    title_bn: str,
    body_bn: str | None = None,
    circle_id: int | None = None,
) -> int:
    stmt = (
        select(User)
        .join(Member, Member.user_id == User.id)
        .where(User.is_active == True, Member.status == 'ACTIVE')
    )
    if circle_id is not None:
        stmt = stmt.where(Member.circle_id == circle_id)
    users = list(db.scalars(stmt.limit(2000)).all())
    if not users:
        users = list(db.scalars(select(User).where(User.is_active == True, User.role == 'MEMBER').limit(500)).all())
    sent = 0
    summary = (body_bn or title_bn)[:300]
    for u in users:
        prefs = _user_prefs(db, u.id)
        if prefs.get('in_app_enabled', True):
            create_in_app(db, u, f'নতুন প্রকাশনা: {title_bn}', summary, entity_type.upper())
            sent += 1
    return sent


# ==============================================================================
# 1. NEWS MANAGEMENT (ADMIN & PUBLIC)
# ==============================================================================

class NewsPayload(BaseModel):
    slug: str | None = Field(default=None, max_length=220)
    title_bn: str = Field(min_length=3, max_length=260)
    title_en: str | None = Field(default=None, max_length=260)
    summary_bn: str | None = Field(default=None, max_length=4000)
    summary_en: str | None = Field(default=None, max_length=4000)
    content_bn: str = Field(min_length=5)
    content_en: str | None = None
    category: str = Field(default='GENERAL', max_length=60)
    tags: list[str] | str | None = None
    cover_image_url: str | None = Field(default=None, max_length=500)
    gallery_urls: list[str] | None = None
    author_name: str | None = Field(default=None, max_length=160)
    is_featured: bool = False
    is_published: bool = False
    scheduled_at: datetime | None = None
    meta_title: str | None = Field(default=None, max_length=260)
    meta_description: str | None = Field(default=None, max_length=500)
    og_image_url: str | None = Field(default=None, max_length=500)


def _serialize_news(n: News) -> dict[str, Any]:
    gallery: list[str] = []
    if n.gallery_urls:
        try:
            parsed = json.loads(n.gallery_urls)
            if isinstance(parsed, list):
                gallery = [str(x) for x in parsed]
        except Exception:
            gallery = [x.strip() for x in n.gallery_urls.split(',') if x.strip()]
    tags_list = [t.strip() for t in (n.tags or '').split(',') if t.strip()]
    canonical = f"{settings.frontend_url.rstrip('/')}/news/{n.slug}"
    return {
        'id': n.id,
        'slug': n.slug,
        'title_bn': n.title_bn,
        'title_en': n.title_en,
        'summary_bn': n.summary_bn,
        'summary_en': n.summary_en,
        'content_bn': n.content_bn,
        'content_en': n.content_en,
        'category': n.category,
        'tags': tags_list,
        'cover_image_url': n.cover_image_url,
        'gallery_urls': gallery,
        'author_id': n.author_id,
        'author_name': n.author_name or 'পিজিসিবি সম্পাদকীয় ডেস্ক',
        'is_featured': bool(n.is_featured),
        'is_published': bool(n.is_published),
        'scheduled_at': n.scheduled_at,
        'published_at': n.published_at,
        'view_count': n.view_count or 0,
        'meta_title': n.meta_title or n.title_bn,
        'meta_description': n.meta_description or (n.summary_bn or n.content_bn[:160]),
        'og_image_url': n.og_image_url or n.cover_image_url,
        'seo': {
            'meta_title': n.meta_title or n.title_bn,
            'meta_description': n.meta_description or (n.summary_bn or n.content_bn[:160]),
            'og_image_url': n.og_image_url or n.cover_image_url,
            'canonical_url': canonical,
            'json_ld': {
                '@context': 'https://schema.org',
                '@type': 'NewsArticle',
                'headline': n.title_bn,
                'datePublished': n.published_at.isoformat() if n.published_at else None,
                'author': {'@type': 'Organization', 'name': n.author_name or 'PGCB'},
            },
        },
        'created_at': n.created_at,
        'updated_at': n.updated_at,
    }


def _auto_publish_scheduled_news(db: Session) -> None:
    now = datetime.utcnow()
    due = list(
        db.scalars(
            select(News).where(
                News.is_published == False,
                News.scheduled_at != None,
                News.scheduled_at <= now,
            )
        ).all()
    )
    if not due:
        return
    for item in due:
        item.is_published = True
        item.published_at = item.published_at or now
        wf = db.scalar(select(ContentWorkflow).where(ContentWorkflow.entity_type == 'NEWS', ContentWorkflow.entity_id == item.id))
        if wf:
            wf.status = 'PUBLISHED'
            wf.published_at = now
    db.commit()


@router.get('/admin/news')
def admin_list_news(
    category: str | None = None,
    q: str | None = None,
    _: User = Depends(require_permission('content.read')),
    db: Session = Depends(get_db),
):
    _auto_publish_scheduled_news(db)
    stmt = select(News).order_by(News.is_featured.desc(), desc(News.published_at), desc(News.created_at))
    if category:
        stmt = stmt.where(News.category == category.upper())
    if q and q.strip():
        like = f'%{q.strip()}%'
        stmt = stmt.where(or_(News.title_bn.like(like), News.title_en.like(like), News.content_bn.like(like)))
    rows = db.scalars(stmt.limit(200)).all()
    return [_serialize_news(n) for n in rows]


@router.post('/admin/news', status_code=201)
def admin_create_news(
    payload: NewsPayload,
    request: Request,
    admin: User = Depends(require_permission('content.write')),
    db: Session = Depends(get_db),
):
    if payload.is_published and not has_permission(admin.role, 'content.publish'):
        raise HTTPException(403, 'Content Editor cannot publish directly without Publisher/Admin approval')
    base_slug = _slugify(payload.slug or payload.title_en or payload.title_bn)
    slug = base_slug
    counter = 2
    while db.scalar(select(News).where(News.slug == slug)):
        slug = f'{base_slug}-{counter}'
        counter += 1

    tags_str = ','.join(payload.tags) if isinstance(payload.tags, list) else (payload.tags or '')
    gallery_str = json.dumps(payload.gallery_urls, ensure_ascii=False) if payload.gallery_urls else None
    now = datetime.utcnow()
    item = News(
        slug=slug,
        title_bn=payload.title_bn,
        title_en=payload.title_en,
        summary_bn=payload.summary_bn,
        summary_en=payload.summary_en,
        content_bn=payload.content_bn,
        content_en=payload.content_en,
        category=payload.category.upper(),
        tags=tags_str,
        cover_image_url=payload.cover_image_url,
        gallery_urls=gallery_str,
        author_id=admin.id,
        author_name=payload.author_name or admin.name_bn,
        is_featured=payload.is_featured,
        is_published=payload.is_published,
        scheduled_at=payload.scheduled_at,
        published_at=now if payload.is_published else None,
        meta_title=payload.meta_title,
        meta_description=payload.meta_description,
        og_image_url=payload.og_image_url,
    )
    db.add(item)
    db.flush()

    wf_status = 'PUBLISHED' if item.is_published else ('SCHEDULED' if item.scheduled_at else 'DRAFT')
    wf = ContentWorkflow(
        entity_type='NEWS',
        entity_id=item.id,
        status=wf_status,
        scheduled_at=item.scheduled_at,
        reviewed_by=admin.id,
        reviewed_at=now,
        published_by=admin.id if item.is_published else None,
        published_at=now if item.is_published else None,
    )
    db.add(wf)
    record_content_revision(
        db,
        entity_type='NEWS',
        entity_id=item.id,
        status=wf_status,
        title_bn=item.title_bn,
        title_en=item.title_en,
        content_snapshot={'summary_bn': item.summary_bn, 'content_bn': item.content_bn, 'category': item.category},
        changed_by=admin.id,
        published_by=admin.id if item.is_published else None,
        change_note='Initial news creation',
    )
    if item.is_published:
        notify_members_of_publication(db, 'NEWS', item.id, item.title_bn, item.summary_bn)
    audit(db, admin, 'CREATE', 'NEWS', item.id, request.client.host if request.client else None)
    db.commit()
    db.refresh(item)
    return _serialize_news(item)


@router.put('/admin/news/{news_id}')
def admin_update_news(
    news_id: int,
    payload: NewsPayload,
    request: Request,
    admin: User = Depends(require_permission('content.write')),
    db: Session = Depends(get_db),
):
    if payload.is_published and not has_permission(admin.role, 'content.publish'):
        raise HTTPException(403, 'Content Editor cannot publish directly without Publisher/Admin approval')
    item = db.get(News, news_id)
    if not item:
        raise HTTPException(404, 'News article not found')

    was_published = bool(item.is_published)
    item.title_bn = payload.title_bn
    item.title_en = payload.title_en
    item.summary_bn = payload.summary_bn
    item.summary_en = payload.summary_en
    item.content_bn = payload.content_bn
    item.content_en = payload.content_en
    item.category = payload.category.upper()
    item.tags = ','.join(payload.tags) if isinstance(payload.tags, list) else (payload.tags or '')
    item.cover_image_url = payload.cover_image_url
    item.gallery_urls = json.dumps(payload.gallery_urls, ensure_ascii=False) if payload.gallery_urls is not None else item.gallery_urls
    if payload.author_name:
        item.author_name = payload.author_name
    item.is_featured = payload.is_featured
    item.is_published = payload.is_published
    item.scheduled_at = payload.scheduled_at
    item.meta_title = payload.meta_title
    item.meta_description = payload.meta_description
    item.og_image_url = payload.og_image_url
    if item.is_published and not item.published_at:
        item.published_at = datetime.utcnow()

    wf_status = 'PUBLISHED' if item.is_published else ('SCHEDULED' if item.scheduled_at else 'DRAFT')
    record_content_revision(
        db,
        entity_type='NEWS',
        entity_id=item.id,
        status=wf_status,
        title_bn=item.title_bn,
        title_en=item.title_en,
        content_snapshot={'summary_bn': item.summary_bn, 'content_bn': item.content_bn, 'category': item.category},
        changed_by=admin.id,
        published_by=admin.id if item.is_published else None,
        change_note='Updated news article',
    )
    if item.is_published and not was_published:
        notify_members_of_publication(db, 'NEWS', item.id, item.title_bn, item.summary_bn)
    audit(db, admin, 'UPDATE', 'NEWS', item.id, request.client.host if request.client else None)
    db.commit()
    db.refresh(item)
    return _serialize_news(item)


@router.delete('/admin/news/{news_id}')
def admin_delete_news(
    news_id: int,
    request: Request,
    admin: User = Depends(require_permission('content.write')),
    db: Session = Depends(get_db),
):
    item = db.get(News, news_id)
    if not item:
        raise HTTPException(404, 'News article not found')
    db.delete(item)
    audit(db, admin, 'DELETE', 'NEWS', news_id, request.client.host if request.client else None)
    db.commit()
    return {'ok': True}


@router.get('/public/news')
def public_list_news(
    q: str | None = Query(default=None, max_length=100),
    category: str | None = None,
    tag: str | None = None,
    featured: bool | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    _auto_publish_scheduled_news(db)
    stmt = (
        select(News)
        .where(News.is_published == True)
        .order_by(News.is_featured.desc(), desc(News.published_at), desc(News.created_at))
    )
    if category:
        stmt = stmt.where(News.category == category.upper())
    if featured is not None:
        stmt = stmt.where(News.is_featured == featured)
    if tag:
        stmt = stmt.where(News.tags.like(f'%{tag.strip()}%'))
    if q and q.strip():
        like = f'%{q.strip()}%'
        stmt = stmt.where(or_(News.title_bn.like(like), News.title_en.like(like), News.summary_bn.like(like), News.content_bn.like(like)))
    rows = db.scalars(stmt.offset(offset).limit(limit)).all()
    return [_serialize_news(n) for n in rows]


@router.get('/public/news/{slug_or_id}')
def public_get_news_detail(slug_or_id: str, db: Session = Depends(get_db)):
    _auto_publish_scheduled_news(db)
    if slug_or_id.isdigit():
        item = db.get(News, int(slug_or_id))
    else:
        item = db.scalar(select(News).where(News.slug == slug_or_id))
    if not item or not item.is_published:
        raise HTTPException(404, 'News article not found')
    item.view_count = (item.view_count or 0) + 1
    db.commit()
    db.refresh(item)
    return _serialize_news(item)


# ==============================================================================
# 2. CONTENT VERSIONING & EXTENDED NOTICE/CIRCULAR METADATA
# ==============================================================================

@router.get('/admin/revisions/{entity_type}/{entity_id}')
def list_content_revisions(
    entity_type: str,
    entity_id: int,
    _: User = Depends(require_permission('content.read')),
    db: Session = Depends(get_db),
):
    typ = entity_type.upper()
    rows = list(
        db.scalars(
            select(ContentRevision)
            .where(ContentRevision.entity_type == typ, ContentRevision.entity_id == entity_id)
            .order_by(ContentRevision.version_no.desc())
        ).all()
    )
    uids = {
        uid
        for r in rows
        for uid in (r.changed_by, r.approved_by, r.published_by)
        if uid is not None
    }
    user_map = (
        {u.id: u for u in db.scalars(select(User).where(User.id.in_(uids))).all()}
        if uids else {}
    )
    result = []
    for r in rows:
        snap = r.content_snapshot
        if snap:
            try:
                snap = json.loads(snap)
            except Exception:
                pass
        result.append({
            'id': r.id,
            'entity_type': r.entity_type,
            'entity_id': r.entity_id,
            'version_no': r.version_no,
            'status': r.status,
            'title_bn': r.title_bn,
            'title_en': r.title_en,
            'content_snapshot': snap,
            'changed_by': r.changed_by,
            'changed_by_name': user_map[r.changed_by].name_bn if r.changed_by in user_map else None,
            'approved_by': r.approved_by,
            'approved_by_name': user_map[r.approved_by].name_bn if r.approved_by in user_map else None,
            'published_by': r.published_by,
            'published_by_name': user_map[r.published_by].name_bn if r.published_by in user_map else None,
            'change_note': r.change_note,
            'created_at': r.created_at,
        })
    return result


class CircularExtendedMeta(BaseModel):
    issuing_authority: str = Field(default='কেন্দ্রীয় কার্যনির্বাহী পরিষদ, পিজিসিবি', max_length=200)
    effective_date: str | None = None
    target_audience: str = Field(default='ALL_MEMBERS', max_length=100)
    related_circular_id: int | None = None
    superseded_circular_id: int | None = None


@router.get('/admin/cms/circular-meta/{circular_id}')
def get_circular_extended_meta(
    circular_id: int,
    _: User = Depends(require_permission('content.read')),
    db: Session = Depends(get_db),
):
    c = db.get(Circular, circular_id)
    if not c:
        raise HTTPException(404, 'Circular not found')
    row = db.scalar(select(SiteSetting).where(SiteSetting.key == f'circular_meta:{circular_id}'))
    defaults = {
        'circular_id': circular_id,
        'reference_no': c.reference_no,
        'issuing_authority': 'কেন্দ্রীয় কার্যনির্বাহী পরিষদ, পিজিসিবি',
        'effective_date': c.published_at.strftime('%Y-%m-%d') if c.published_at else None,
        'target_audience': 'ALL_MEMBERS',
        'related_circular_id': None,
        'superseded_circular_id': None,
    }
    if row and row.value:
        try:
            defaults.update(json.loads(row.value))
        except Exception:
            pass
    return defaults


@router.put('/admin/cms/circular-meta/{circular_id}')
def update_circular_extended_meta(
    circular_id: int,
    payload: CircularExtendedMeta,
    request: Request,
    admin: User = Depends(require_permission('content.write')),
    db: Session = Depends(get_db),
):
    c = db.get(Circular, circular_id)
    if not c:
        raise HTTPException(404, 'Circular not found')
    key = f'circular_meta:{circular_id}'
    data = payload.model_dump()
    row = db.scalar(select(SiteSetting).where(SiteSetting.key == key))
    if not row:
        row = SiteSetting(key=key, value=json.dumps(data, ensure_ascii=False), category='CMS_META')
        db.add(row)
    else:
        row.value = json.dumps(data, ensure_ascii=False)
    record_content_revision(
        db,
        entity_type='CIRCULAR',
        entity_id=c.id,
        status='PUBLISHED' if c.is_published else 'DRAFT',
        title_bn=c.title_bn,
        title_en=c.title_en,
        content_snapshot={'reference_no': c.reference_no, **data},
        changed_by=admin.id,
        change_note='Updated circular institutional metadata',
    )
    audit(db, admin, 'UPDATE_META', 'CIRCULAR', c.id, request.client.host if request.client else None)
    db.commit()
    return {'circular_id': circular_id, 'reference_no': c.reference_no, **data}


class NoticeExtendedMeta(BaseModel):
    notice_no: str | None = Field(default=None, max_length=100)
    published_by: str | None = Field(default='সাধারণ সম্পাদক, পিজিসিবি', max_length=200)
    target_audience: str = Field(default='ALL_MEMBERS', max_length=100)
    circle_id: int | None = None


@router.get('/admin/cms/notice-meta/{notice_id}')
def get_notice_extended_meta(
    notice_id: int,
    _: User = Depends(require_permission('content.read')),
    db: Session = Depends(get_db),
):
    n = db.get(Notice, notice_id)
    if not n:
        raise HTTPException(404, 'Notice not found')
    row = db.scalar(select(SiteSetting).where(SiteSetting.key == f'notice_meta:{notice_id}'))
    year = (n.created_at or datetime.utcnow()).year
    defaults = {
        'notice_id': notice_id,
        'notice_no': f'PGCB-NOT-{year}-{n.id:04d}',
        'published_by': 'সাধারণ সম্পাদক, পিজিসিবি',
        'target_audience': 'ALL_MEMBERS',
        'circle_id': None,
    }
    if row and row.value:
        try:
            defaults.update(json.loads(row.value))
        except Exception:
            pass
    return defaults


@router.put('/admin/cms/notice-meta/{notice_id}')
def update_notice_extended_meta(
    notice_id: int,
    payload: NoticeExtendedMeta,
    request: Request,
    admin: User = Depends(require_permission('content.write')),
    db: Session = Depends(get_db),
):
    n = db.get(Notice, notice_id)
    if not n:
        raise HTTPException(404, 'Notice not found')
    key = f'notice_meta:{notice_id}'
    year = (n.created_at or datetime.utcnow()).year
    data = payload.model_dump()
    if not data.get('notice_no'):
        data['notice_no'] = f'PGCB-NOT-{year}-{n.id:04d}'
    row = db.scalar(select(SiteSetting).where(SiteSetting.key == key))
    if not row:
        row = SiteSetting(key=key, value=json.dumps(data, ensure_ascii=False), category='CMS_META')
        db.add(row)
    else:
        row.value = json.dumps(data, ensure_ascii=False)
    record_content_revision(
        db,
        entity_type='NOTICE',
        entity_id=n.id,
        status='PUBLISHED' if n.is_published else 'DRAFT',
        title_bn=n.title_bn,
        title_en=n.title_en,
        content_snapshot=data,
        changed_by=admin.id,
        change_note='Updated notice institutional metadata',
    )
    audit(db, admin, 'UPDATE_META', 'NOTICE', n.id, request.client.host if request.client else None)
    db.commit()
    return {'notice_id': notice_id, **data}


# ==============================================================================
# 3. MEDIA LIBRARY WITH AUTOMATIC IMAGE COMPRESSION & WEBP CONVERSION
# ==============================================================================

@router.post('/admin/media/upload-optimized')
async def upload_optimized_media(
    request: Request,
    file: UploadFile = File(...),
    title_bn: str = Form(default='মিডিয়া অ্যাসেট'),
    description_bn: str | None = Form(default=None),
    alt_text: str | None = Form(default=None),
    folder: str = Form(default='news'),
    convert_to_webp: bool = Form(default=True),
    event_id: int | None = Form(default=None),
    admin: User = Depends(require_permission('content.write')),
    db: Session = Depends(get_db),
):
    allowed_folders = {'news', 'events', 'committee', 'banners', 'documents'}
    clean_folder = folder.strip().lower() if folder else 'news'
    if clean_folder not in allowed_folders:
        clean_folder = 'news'

    raw_bytes = await file.read()
    max_bytes = 10 * 1024 * 1024
    if len(raw_bytes) > max_bytes:
        raise HTTPException(413, 'Maximum upload size is 10 MB')
    if not raw_bytes:
        raise HTTPException(400, 'Empty file upload')

    content_type = (file.content_type or '').lower()
    original_size = len(raw_bytes)
    width = None
    height = None
    out_bytes = raw_bytes
    out_ext = '.bin'
    media_type = 'PHOTO'

    if content_type in {'image/jpeg', 'image/jpg', 'image/png', 'image/webp'} or (
        file.filename and file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
    ):
        from PIL import Image

        try:
            img = Image.open(io.BytesIO(raw_bytes))
            width, height = img.size
            if max(width, height) > 1920:
                img.thumbnail((1920, 1920))
                width, height = img.size
            buf = io.BytesIO()
            if convert_to_webp:
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                img.save(buf, format='WEBP', quality=82, optimize=True)
                out_bytes = buf.getvalue()
                out_ext = '.webp'
            else:
                fmt = img.format or 'JPEG'
                if fmt.upper() == 'JPEG' and img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(buf, format=fmt, optimize=True)
                out_bytes = buf.getvalue()
                out_ext = f'.{fmt.lower()}'
        except Exception as exc:
            raise HTTPException(400, f'Invalid image file: {exc}') from exc
    elif content_type == 'application/pdf' or (file.filename and file.filename.lower().endswith('.pdf')):
        if not raw_bytes.startswith(b'%PDF-'):
            raise HTTPException(400, 'Invalid PDF signature')
        out_ext = '.pdf'
        media_type = 'DOCUMENT'
    else:
        raise HTTPException(400, 'Unsupported media file type. Allowed: JPG, PNG, WEBP, PDF')

    stem = _slugify((file.filename or 'asset').rsplit('.', 1)[0], fallback_prefix=clean_folder)
    filename = f'{clean_folder}-{stem}-{int(datetime.utcnow().timestamp())}{out_ext}'
    stored = save_bytes(out_bytes, 'public', filename)
    public_url = stored if str(stored).startswith('http') else f'/api/v1/public/assets/{filename}'

    asset = MediaAsset(
        media_type=media_type,
        title_bn=title_bn,
        description_bn=description_bn or alt_text,
        url=public_url,
        thumbnail_url=public_url if media_type == 'PHOTO' else None,
        event_id=event_id,
        published=True,
    )
    db.add(asset)
    db.flush()
    audit(db, admin, 'UPLOAD_OPTIMIZED_MEDIA', 'MEDIA', asset.id, request.client.host if request.client else None)
    db.commit()
    db.refresh(asset)

    return {
        'ok': True,
        'id': asset.id,
        'url': public_url,
        'filename': filename,
        'folder': clean_folder,
        'format': out_ext.lstrip('.').upper(),
        'width': width,
        'height': height,
        'size_bytes': len(out_bytes),
        'original_size_bytes': original_size,
        'title_bn': asset.title_bn,
        'alt_text': alt_text or title_bn,
    }


# ==============================================================================
# 4. HOMEPAGE CMS
# ==============================================================================

DEFAULT_HOMEPAGE_CONFIG: dict[str, Any] = {
    'hero_banner': {
        'enabled': True,
        'badge_bn': 'পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতি (পিজিসিবি)',
        'headline_bn': 'জাতীয় পাওয়ার গ্রিড পরিচালনা ও প্রকৌশলী কল্যাণে ঐক্যবদ্ধ ডিজিটাল প্ল্যাটফর্ম',
        'headline_en': 'Unified Digital Institutional Portal for PGCB Diploma Engineers',
        'subheadline_bn': 'সদস্যপদ নিবন্ধন, ডিজিটাল আইডি ও ভেরিফিকেশন, সার্কুলার, নোটিশ এবং ৯টি গ্রিড সার্কেলের সমন্বিত সেবা।',
        'cta_primary_text': 'সদস্যপদ আবেদন করুন',
        'cta_primary_href': '/apply',
        'cta_secondary_text': 'সদস্য ডিরেক্টরি ও যাচাই',
        'cta_secondary_href': '/members',
    },
    'emergency_alert': {
        'enabled': False,
        'title_bn': '',
        'message_bn': '',
        'priority': 'URGENT',
        'link_href': '/notices',
    },
    'president_message': {
        'enabled': True,
        'name_bn': 'প্রকৌ. মো. রফিকুল ইসলাম',
        'designation_bn': 'সভাপতি, কেন্দ্রীয় কার্যনির্বাহী পরিষদ',
        'message_bn': 'পিজিসিবি ডিপ্লোমা প্রকৌশলীদের পেশাগত উৎকর্ষ, স্বচ্ছতা এবং প্রাতিষ্ঠানিক ডিজিটাল রূপান্তরে আমরা প্রতিশ্রুতিবদ্ধ।',
        'photo_url': None,
    },
    'secretary_message': {
        'enabled': True,
        'name_bn': 'প্রকৌ. সাইফুল আলম',
        'designation_bn': 'সাধারণ সম্পাদক, কেন্দ্রীয় কার্যনির্বাহী পরিষদ',
        'message_bn': 'সকল গ্রিড সার্কেলের সদস্যদের সেবা ও যোগাযোগ আরও দ্রুত ও নিরাপদ করতে আমাদের এই ডিজিটাল পোর্টাল।',
        'photo_url': None,
    },
    'sections': {
        'featured_notices_limit': 5,
        'featured_events_limit': 3,
        'featured_news_limit': 4,
        'statistics_counters_enabled': True,
    },
    'partner_links': [
        {'title_bn': 'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (PGCB)', 'url': 'https://pgcb.gov.bd'},
        {'title_bn': 'বিদ্যুৎ বিভাগ, জ্বালানি ও খনিজ সম্পদ মন্ত্রণালয়', 'url': 'https://powerdivision.gov.bd'},
        {'title_bn': 'ইনস্টিটিউশন অব ডিপ্লোমা ইঞ্জিনিয়ার্স, বাংলাদেশ (IDEB)', 'url': 'https://ideb.org.bd'},
    ],
}


@router.get('/public/homepage-config')
def get_public_homepage_config(db: Session = Depends(get_db)):
    row = db.scalar(select(SiteSetting).where(SiteSetting.key == 'homepage_cms_config'))
    config = json.loads(json.dumps(DEFAULT_HOMEPAGE_CONFIG))
    if row and row.value:
        try:
            saved = json.loads(row.value)
            if isinstance(saved, dict):
                for k, v in saved.items():
                    if isinstance(v, dict) and isinstance(config.get(k), dict):
                        config[k].update(v)
                    else:
                        config[k] = v
        except Exception:
            pass
    urgent_notice = db.scalar(
        select(Notice)
        .where(Notice.is_published == True, or_(Notice.priority == 'URGENT', Notice.is_pinned == True))
        .order_by(Notice.is_pinned.desc(), desc(Notice.published_at))
    )
    if urgent_notice and not config['emergency_alert'].get('enabled'):
        config['live_urgent_notice'] = {
            'id': urgent_notice.id,
            'title_bn': urgent_notice.title_bn,
            'priority': urgent_notice.priority,
            'href': f'/notices/{urgent_notice.id}',
        }
    return config


@router.put('/admin/homepage-config')
def update_admin_homepage_config(
    payload: dict[str, Any],
    request: Request,
    admin: User = Depends(require_permission('content.write')),
    db: Session = Depends(get_db),
):
    config = json.loads(json.dumps(DEFAULT_HOMEPAGE_CONFIG))
    for k, v in payload.items():
        if isinstance(v, dict) and isinstance(config.get(k), dict):
            config[k].update(v)
        else:
            config[k] = v
    row = db.scalar(select(SiteSetting).where(SiteSetting.key == 'homepage_cms_config'))
    if not row:
        row = SiteSetting(
            key='homepage_cms_config',
            value=json.dumps(config, ensure_ascii=False),
            category='HOMEPAGE_CMS',
        )
        db.add(row)
    else:
        row.value = json.dumps(config, ensure_ascii=False)
    record_content_revision(
        db,
        entity_type='HOMEPAGE',
        entity_id=1,
        status='PUBLISHED',
        title_bn=config.get('hero_banner', {}).get('headline_bn', 'Homepage CMS'),
        content_snapshot=config,
        changed_by=admin.id,
        published_by=admin.id,
        change_note='Updated homepage CMS configuration',
    )
    audit(db, admin, 'UPDATE_HOMEPAGE_CMS', 'SITE_SETTING', row.id, request.client.host if request.client else None)
    db.commit()
    return {'ok': True, 'config': config}


# ==============================================================================
# 5. TARGETED ANNOUNCEMENT ENGINE
# ==============================================================================

class AnnouncementCreatePayload(BaseModel):
    title_bn: str = Field(min_length=3, max_length=260)
    title_en: str | None = Field(default=None, max_length=260)
    body_bn: str = Field(min_length=5, max_length=5000)
    body_en: str | None = None
    target_scope: str = Field(default='ALL_MEMBERS', pattern=r'^(ALL_MEMBERS|CIRCLE|STATUS|ADMINS|COMMITTEE)$')
    target_circle_id: int | None = None
    target_status: str | None = None
    target_role: str | None = None
    channels: str = Field(default='IN_APP', max_length=120)
    priority: str = Field(default='NORMAL', pattern=r'^(NORMAL|IMPORTANT|URGENT)$')
    is_banner: bool = False
    is_published: bool = True
    expires_at: datetime | None = None


def _serialize_announcement(a: Announcement) -> dict[str, Any]:
    return {
        'id': a.id,
        'title_bn': a.title_bn,
        'title_en': a.title_en,
        'body_bn': a.body_bn,
        'body_en': a.body_en,
        'target_scope': a.target_scope,
        'target_circle_id': a.target_circle_id,
        'target_status': a.target_status,
        'target_role': a.target_role,
        'channels': [c.strip() for c in (a.channels or 'IN_APP').split(',') if c.strip()],
        'priority': a.priority,
        'is_banner': bool(a.is_banner),
        'is_published': bool(a.is_published),
        'recipients_count': a.recipients_count or 0,
        'deliveries_count': a.deliveries_count or 0,
        'created_by': a.created_by,
        'published_at': a.published_at,
        'expires_at': a.expires_at,
        'created_at': a.created_at,
    }


@router.get('/admin/announcements')
def admin_list_announcements(
    _: User = Depends(require_permission('content.read')),
    db: Session = Depends(get_db),
):
    rows = db.scalars(select(Announcement).order_by(Announcement.created_at.desc()).limit(200)).all()
    return [_serialize_announcement(a) for a in rows]


@router.post('/admin/announcements', status_code=201)
def admin_create_announcement(
    payload: AnnouncementCreatePayload,
    request: Request,
    admin: User = Depends(require_permission('content.write')),
    db: Session = Depends(get_db),
):
    scope = payload.target_scope.upper()
    if scope == 'CIRCLE':
        if not payload.target_circle_id:
            raise HTTPException(400, 'target_circle_id is required when target_scope is CIRCLE')
        users = list(
            db.scalars(
                select(User)
                .join(Member, Member.user_id == User.id)
                .where(User.is_active == True, Member.circle_id == payload.target_circle_id)
            ).all()
        )
    elif scope == 'STATUS':
        st = (payload.target_status or 'ACTIVE').upper()
        users = list(
            db.scalars(
                select(User)
                .join(Member, Member.user_id == User.id)
                .where(User.is_active == True, Member.status == st)
            ).all()
        )
    elif scope == 'ADMINS':
        users = list(
            db.scalars(
                select(User).where(User.is_active == True, User.role != 'MEMBER')
            ).all()
        )
    elif scope == 'COMMITTEE':
        committee_emails = [
            c.name_en.lower()
            for c in db.scalars(select(CommitteeMember).where(CommitteeMember.active == True)).all()
            if c.name_en and '@' in c.name_en
        ]
        stmt = select(User).where(User.is_active == True)
        if committee_emails:
            stmt = stmt.where(or_(User.email.in_(committee_emails), User.role.in_(['SUPER_ADMIN', 'CENTRAL_ADMIN'])))
        else:
            stmt = stmt.where(User.role.in_(['SUPER_ADMIN', 'CENTRAL_ADMIN', 'CIRCLE_ADMIN']))
        users = list(db.scalars(stmt).all())
    else:
        users = list(db.scalars(select(User).where(User.is_active == True)).all())

    channels_set = {c.strip().upper() for c in payload.channels.split(',') if c.strip()}
    if 'ALL' in channels_set:
        channels_set = {'IN_APP', 'EMAIL', 'SMS'}

    deliveries = 0
    if payload.is_published:
        for u in users:
            prefs = _user_prefs(db, u.id)
            notif = None
            if 'IN_APP' in channels_set and prefs.get('in_app_enabled', True):
                notif = create_in_app(db, u, payload.title_bn, payload.body_bn, 'ANNOUNCEMENT')
                deliveries += 1
                record_delivery(db, notif.id, 'IN_APP', u.email, DeliveryResult('SENT', 'IN_APP'))
            if 'EMAIL' in channels_set and prefs.get('email_enabled', True) and u.email:
                queue_delivery(db, notif.id if notif else None, 'EMAIL', u.email)
                deliveries += 1
            if 'SMS' in channels_set and prefs.get('sms_enabled', False) and u.phone:
                queue_delivery(db, notif.id if notif else None, 'SMS', u.phone)
                deliveries += 1

    item = Announcement(
        title_bn=payload.title_bn,
        title_en=payload.title_en,
        body_bn=payload.body_bn,
        body_en=payload.body_en,
        target_scope=scope,
        target_circle_id=payload.target_circle_id,
        target_status=(payload.target_status or '').upper() or None,
        target_role=payload.target_role,
        channels=','.join(sorted(channels_set)),
        priority=payload.priority,
        is_banner=payload.is_banner,
        is_published=payload.is_published,
        recipients_count=len(users),
        deliveries_count=deliveries,
        created_by=admin.id,
        published_at=datetime.utcnow() if payload.is_published else None,
        expires_at=payload.expires_at,
    )
    db.add(item)
    db.flush()
    audit(db, admin, 'CREATE_ANNOUNCEMENT', 'ANNOUNCEMENT', item.id, request.client.host if request.client else None)
    db.commit()
    db.refresh(item)
    return _serialize_announcement(item)


@router.get('/member/announcements')
def member_announcements(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    m = db.scalar(select(Member).where(Member.user_id == user.id))
    rows = list(
        db.scalars(
            select(Announcement)
            .where(
                Announcement.is_published == True,
                or_(Announcement.expires_at == None, Announcement.expires_at >= now),
            )
            .order_by(Announcement.created_at.desc())
            .limit(50)
        ).all()
    )
    matched = []
    for a in rows:
        if a.target_scope == 'ALL_MEMBERS':
            matched.append(_serialize_announcement(a))
        elif a.target_scope == 'CIRCLE' and m and m.circle_id == a.target_circle_id:
            matched.append(_serialize_announcement(a))
        elif a.target_scope == 'STATUS' and m and m.status == a.target_status:
            matched.append(_serialize_announcement(a))
        elif a.target_scope == 'ADMINS' and user.role != 'MEMBER':
            matched.append(_serialize_announcement(a))
    return matched


@router.get('/public/announcements')
def public_banner_announcements(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    rows = db.scalars(
        select(Announcement)
        .where(
            Announcement.is_published == True,
            Announcement.is_banner == True,
            Announcement.target_scope == 'ALL_MEMBERS',
            or_(Announcement.expires_at == None, Announcement.expires_at >= now),
        )
        .order_by(Announcement.created_at.desc())
        .limit(5)
    ).all()
    return [_serialize_announcement(a) for a in rows]


# ==============================================================================
# 6. SEO METADATA, SITEMAP.XML, ROBOTS.TXT, RSS.XML
# ==============================================================================

class SEOMetadataPayload(BaseModel):
    slug: str | None = Field(default=None, max_length=220)
    meta_title: str = Field(min_length=3, max_length=260)
    meta_description: str = Field(min_length=5, max_length=500)
    og_image_url: str | None = Field(default=None, max_length=500)
    canonical_url: str | None = Field(default=None, max_length=500)
    schema_type: str = Field(default='WebPage', max_length=80)


@router.get('/admin/seo/{entity_type}/{entity_id}')
def get_seo_metadata(
    entity_type: str,
    entity_id: int,
    _: User = Depends(require_permission('content.read')),
    db: Session = Depends(get_db),
):
    typ = entity_type.upper()
    row = db.scalar(select(SEOMetadata).where(SEOMetadata.entity_type == typ, SEOMetadata.entity_id == entity_id))
    if not row:
        return {
            'entity_type': typ,
            'entity_id': entity_id,
            'slug': None,
            'meta_title': 'পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতি (পিজিসিবি)',
            'meta_description': 'Official Institutional Portal of Power Grid Diploma Engineers Association (PGCB).',
            'og_image_url': None,
            'canonical_url': None,
            'schema_type': 'WebPage',
        }
    return {
        'id': row.id,
        'entity_type': row.entity_type,
        'entity_id': row.entity_id,
        'slug': row.slug,
        'meta_title': row.meta_title,
        'meta_description': row.meta_description,
        'og_image_url': row.og_image_url,
        'canonical_url': row.canonical_url,
        'schema_type': row.schema_type,
        'updated_at': row.updated_at,
    }


@router.put('/admin/seo/{entity_type}/{entity_id}')
def upsert_seo_metadata(
    entity_type: str,
    entity_id: int,
    payload: SEOMetadataPayload,
    request: Request,
    admin: User = Depends(require_permission('content.write')),
    db: Session = Depends(get_db),
):
    typ = entity_type.upper()
    row = db.scalar(select(SEOMetadata).where(SEOMetadata.entity_type == typ, SEOMetadata.entity_id == entity_id))
    if not row:
        row = SEOMetadata(
            entity_type=typ,
            entity_id=entity_id,
            slug=payload.slug,
            meta_title=payload.meta_title,
            meta_description=payload.meta_description,
            og_image_url=payload.og_image_url,
            canonical_url=payload.canonical_url,
            schema_type=payload.schema_type,
        )
        db.add(row)
    else:
        row.slug = payload.slug
        row.meta_title = payload.meta_title
        row.meta_description = payload.meta_description
        row.og_image_url = payload.og_image_url
        row.canonical_url = payload.canonical_url
        row.schema_type = payload.schema_type
    audit(db, admin, 'UPSERT_SEO', typ, entity_id, request.client.host if request.client else None)
    db.commit()
    db.refresh(row)
    return {
        'ok': True,
        'id': row.id,
        'entity_type': row.entity_type,
        'entity_id': row.entity_id,
        'meta_title': row.meta_title,
        'meta_description': row.meta_description,
        'og_image_url': row.og_image_url,
        'canonical_url': row.canonical_url,
        'schema_type': row.schema_type,
    }


@router.get('/public/sitemap.xml')
def public_sitemap_xml(db: Session = Depends(get_db)):
    base = settings.frontend_url.rstrip('/')
    now_iso = datetime.utcnow().strftime('%Y-%m-%d')
    static_paths = [
        '/', '/about', '/committee', '/circles', '/members', '/notices',
        '/circulars', '/news', '/events', '/journal', '/documents', '/media', '/contact', '/verify',
    ]
    urls: list[tuple[str, str, str]] = [(f'{base}{p}', now_iso, '0.8') for p in static_paths]

    for n in db.scalars(select(Notice).where(Notice.is_published == True).limit(200)).all():
        dt = (n.published_at or n.created_at or datetime.utcnow()).strftime('%Y-%m-%d')
        urls.append((f'{base}/notices/{n.id}', dt, '0.7'))
    for c in db.scalars(select(Circular).where(Circular.is_published == True).limit(200)).all():
        dt = (c.published_at or c.created_at or datetime.utcnow()).strftime('%Y-%m-%d')
        urls.append((f'{base}/circulars/{c.id}', dt, '0.7'))
    for nw in db.scalars(select(News).where(News.is_published == True).limit(200)).all():
        dt = (nw.published_at or nw.created_at or datetime.utcnow()).strftime('%Y-%m-%d')
        urls.append((f'{base}/news/{nw.slug}', dt, '0.7'))
    for ev in db.scalars(select(Event).where(Event.is_published == True).limit(100)).all():
        dt = (ev.event_date or ev.created_at or datetime.utcnow()).strftime('%Y-%m-%d')
        urls.append((f'{base}/events/{ev.id}', dt, '0.6'))

    xml_entries = '\n'.join(
        f'  <url><loc>{xml_escape(loc)}</loc><lastmod>{lastmod}</lastmod><priority>{prio}</priority></url>'
        for loc, lastmod, prio in urls
    )
    xml_body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'{xml_entries}\n'
        '</urlset>'
    )
    return Response(content=xml_body, media_type='application/xml')


@router.get('/public/robots.txt')
def public_robots_txt():
    base = settings.frontend_url.rstrip('/')
    content = (
        'User-agent: *\n'
        'Allow: /\n'
        'Disallow: /admin\n'
        'Disallow: /portal\n'
        'Disallow: /api/v1/admin\n'
        f'Sitemap: {base}/api/v1/public/sitemap.xml\n'
    )
    return Response(content=content, media_type='text/plain; charset=utf-8')


@router.get('/public/rss.xml')
def public_rss_feed(db: Session = Depends(get_db)):
    base = settings.frontend_url.rstrip('/')
    items: list[dict[str, Any]] = []
    for n in db.scalars(select(Notice).where(Notice.is_published == True).order_by(desc(Notice.published_at)).limit(15)).all():
        items.append({
            'title': f'[নোটিশ] {n.title_bn}',
            'link': f'{base}/notices/{n.id}',
            'description': (n.content_bn or '')[:240],
            'pub_date': n.published_at or n.created_at or datetime.utcnow(),
        })
    for c in db.scalars(select(Circular).where(Circular.is_published == True).order_by(desc(Circular.published_at)).limit(15)).all():
        items.append({
            'title': f'[সার্কুলার {c.reference_no}] {c.title_bn}',
            'link': f'{base}/circulars/{c.id}',
            'description': (c.summary_bn or c.title_bn)[:240],
            'pub_date': c.published_at or c.created_at or datetime.utcnow(),
        })
    for nw in db.scalars(select(News).where(News.is_published == True).order_by(desc(News.published_at)).limit(15)).all():
        items.append({
            'title': f'[সংবাদ] {nw.title_bn}',
            'link': f'{base}/news/{nw.slug}',
            'description': (nw.summary_bn or nw.content_bn or '')[:240],
            'pub_date': nw.published_at or nw.created_at or datetime.utcnow(),
        })
    items.sort(key=lambda x: x['pub_date'], reverse=True)

    rss_items = '\n'.join(
        '    <item>\n'
        f'      <title>{xml_escape(it["title"])}</title>\n'
        f'      <link>{xml_escape(it["link"])}</link>\n'
        f'      <description>{xml_escape(it["description"])}</description>\n'
        f'      <pubDate>{it["pub_date"].strftime("%a, %d %b %Y %H:%M:%S GMT")}</pubDate>\n'
        '    </item>'
        for it in items[:25]
    )
    rss_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        '  <channel>\n'
        '    <title>পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতি (পিজিসিবি) — অফিসিয়াল ফিড</title>\n'
        f'    <link>{xml_escape(base)}</link>\n'
        '    <description>সর্বশেষ নোটিশ, সার্কুলার এবং প্রাতিষ্ঠানিক সংবাদ</description>\n'
        f'{rss_items}\n'
        '  </channel>\n'
        '</rss>'
    )
    return Response(content=rss_xml, media_type='application/rss+xml')


# ==============================================================================
# 7. CMS ANALYTICS (PRIVACY-SAFE CONTENT METRICS)
# ==============================================================================

@router.get('/admin/analytics/cms')
def get_cms_analytics(
    _: User = Depends(require_permission('content.read')),
    db: Session = Depends(get_db),
):
    notices = list(db.scalars(select(Notice).order_by(Notice.is_pinned.desc(), desc(Notice.published_at)).limit(10)).all())
    docs = list(db.scalars(select(Document).order_by(desc(Document.download_count)).limit(10)).all())
    news_rows = list(db.scalars(select(News).order_by(desc(News.view_count), desc(News.published_at)).limit(10)).all())
    events = list(db.scalars(select(Event).order_by(desc(Event.event_date)).limit(10)).all())
    regs = list(db.scalars(select(EventRegistration)).all())
    workflows = list(db.scalars(select(ContentWorkflow)).all())
    announcements = list(db.scalars(select(Announcement).order_by(desc(Announcement.created_at)).limit(10)).all())
    inquiries = list(db.scalars(select(ContactInquiryMeta)).all())

    wf_breakdown: dict[str, int] = {}
    for w in workflows:
        wf_breakdown[w.status] = wf_breakdown.get(w.status, 0) + 1

    inquiry_breakdown: dict[str, int] = {}
    for iq in inquiries:
        inquiry_breakdown[iq.status] = inquiry_breakdown.get(iq.status, 0) + 1

    regs_by_event: dict[int, int] = {}
    for r in regs:
        regs_by_event[r.event_id] = regs_by_event.get(r.event_id, 0) + 1

    return {
        'most_viewed_notices': [
            {'id': n.id, 'title_bn': n.title_bn, 'category': n.category, 'priority': n.priority, 'is_published': n.is_published}
            for n in notices
        ],
        'most_downloaded_documents': [
            {'id': d.id, 'title_bn': d.title_bn, 'category': d.category, 'download_count': d.download_count or 0}
            for d in docs
        ],
        'most_viewed_news': [
            {'id': nw.id, 'slug': nw.slug, 'title_bn': nw.title_bn, 'category': nw.category, 'view_count': nw.view_count or 0}
            for nw in news_rows
        ],
        'event_registration_conversions': [
            {
                'event_id': e.id,
                'title_bn': e.title_bn,
                'capacity': e.capacity,
                'registered_count': regs_by_event.get(e.id, 0),
                'conversion_pct': round((regs_by_event.get(e.id, 0) / e.capacity) * 100.0, 1) if e.capacity else 100.0,
            }
            for e in events
        ],
        'announcement_reach': {
            'total_campaigns': len(announcements),
            'total_recipients_reached': sum(a.recipients_count or 0 for a in announcements),
            'total_deliveries_sent': sum(a.deliveries_count or 0 for a in announcements),
        },
        'workflow_status_breakdown': wf_breakdown,
        'inquiry_ticket_summary': inquiry_breakdown,
        'generated_at': datetime.utcnow().isoformat(),
    }
