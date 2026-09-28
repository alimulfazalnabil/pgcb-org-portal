from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rbac import has_permission, require_permission
from app.db.session import get_db
from app.models import Certificate, Circular, ContentWorkflow, Document, Event, Journal, Notice, User
from app.models.core import News
from app.routers.cms import notify_members_of_publication, record_content_revision
from app.services import audit

router = APIRouter(prefix='/admin/workflows', tags=['cms-workflows'])


class WorkflowTransition(BaseModel):
    status: str = Field(pattern=r'^(DRAFT|SUBMITTED|IN_REVIEW|APPROVED|SCHEDULED|PUBLISHED|ARCHIVED)$')
    review_note: str | None = Field(default=None, max_length=4000)
    scheduled_at: datetime | None = None


CONTENT_MAP = {
    'CIRCULAR': Circular,
    'NOTICE': Notice,
    'NEWS': News,
    'DOCUMENT': Document,
    'CERTIFICATE': Certificate,
    'JOURNAL': Journal,
    'EVENT': Event,
}


def _set_published(entity, status: str, now: datetime):
    if hasattr(entity, 'is_published'):
        entity.is_published = status == 'PUBLISHED'
    if hasattr(entity, 'status') and isinstance(entity, Certificate):
        if status == 'PUBLISHED':
            entity.status = 'ISSUED'
    if status == 'PUBLISHED' and hasattr(entity, 'published_at') and not entity.published_at:
        entity.published_at = now


def _serialize_workflow(w: ContentWorkflow) -> dict:
    return {
        'id': w.id,
        'entity_type': w.entity_type,
        'entity_id': w.entity_id,
        'status': w.status,
        'review_note': w.review_note,
        'scheduled_at': w.scheduled_at,
        'created_by': w.reviewed_by or w.published_by,
        'reviewed_by': w.reviewed_by,
        'approved_by': w.reviewed_by if w.status in ('APPROVED', 'PUBLISHED', 'SCHEDULED') else None,
        'published_by': w.published_by,
        'reviewed_at': w.reviewed_at,
        'published_at': w.published_at,
        'updated_at': w.updated_at,
    }


@router.get('')
def list_workflows(
    entity_type: str | None = None,
    status: str | None = None,
    _: User = Depends(require_permission('content.read')),
    db: Session = Depends(get_db),
):
    stmt = select(ContentWorkflow).order_by(ContentWorkflow.updated_at.desc())
    if entity_type:
        stmt = stmt.where(ContentWorkflow.entity_type == entity_type.upper())
    if status:
        stmt = stmt.where(ContentWorkflow.status == status.upper())
    rows = db.scalars(stmt.limit(500)).all()
    return [_serialize_workflow(w) for w in rows]


@router.post('/{entity_type}/{entity_id}/transition')
def transition(
    entity_type: str,
    entity_id: int,
    payload: WorkflowTransition,
    request: Request,
    admin: User = Depends(require_permission('content.read')),
    db: Session = Depends(get_db),
):
    status = payload.status
    if status in {'SCHEDULED', 'PUBLISHED', 'ARCHIVED'}:
        if not has_permission(admin.role, 'content.publish'):
            raise HTTPException(403, 'Insufficient permissions: Publisher or Super Admin role required to publish or archive content')
    elif status in {'IN_REVIEW', 'APPROVED'}:
        if not (has_permission(admin.role, 'content.review') or has_permission(admin.role, 'content.publish')):
            raise HTTPException(403, 'Insufficient permissions: Reviewer, Publisher, or Super Admin role required to review/approve content')
    else:
        if not (has_permission(admin.role, 'content.write') or has_permission(admin.role, 'content.review') or has_permission(admin.role, 'content.publish')):
            raise HTTPException(403, 'Insufficient permissions to modify content workflow')

    typ = entity_type.upper()
    model = CONTENT_MAP.get(typ)
    if not model:
        raise HTTPException(400, f'Unsupported content type: {typ}')
    entity = db.get(model, entity_id)
    if not entity:
        raise HTTPException(404, 'Content not found')
    workflow = db.scalar(
        select(ContentWorkflow).where(ContentWorkflow.entity_type == typ, ContentWorkflow.entity_id == entity_id)
    )
    if not workflow:
        workflow = ContentWorkflow(entity_type=typ, entity_id=entity_id, status='DRAFT')
        db.add(workflow)
    current = (workflow.status if workflow else None) or 'DRAFT'
    allowed = {
        'DRAFT': {'SUBMITTED', 'IN_REVIEW', 'PUBLISHED'},
        'SUBMITTED': {'DRAFT', 'IN_REVIEW', 'APPROVED'},
        'IN_REVIEW': {'DRAFT', 'SUBMITTED', 'APPROVED'},
        'APPROVED': {'IN_REVIEW', 'SCHEDULED', 'PUBLISHED'},
        'SCHEDULED': {'APPROVED', 'PUBLISHED'},
        'PUBLISHED': {'ARCHIVED', 'DRAFT'},
        'ARCHIVED': {'DRAFT'},
    }
    if status != current and status not in allowed.get(current, set()):
        raise HTTPException(409, f'Invalid workflow transition: {current} -> {status}')
    if status == 'SCHEDULED':
        if not payload.scheduled_at:
            raise HTTPException(400, 'scheduled_at is required for scheduled content')
        if payload.scheduled_at <= datetime.utcnow():
            raise HTTPException(400, 'scheduled_at must be in the future')
    now = datetime.utcnow()
    workflow.status = status
    workflow.review_note = payload.review_note
    workflow.scheduled_at = payload.scheduled_at
    if status in {'SUBMITTED', 'IN_REVIEW', 'APPROVED'}:
        workflow.reviewed_by = admin.id
        workflow.reviewed_at = now
    if status == 'PUBLISHED':
        if not workflow.reviewed_by:
            workflow.reviewed_by = admin.id
            workflow.reviewed_at = now
        workflow.published_by = admin.id
        workflow.published_at = now
    if status == 'ARCHIVED':
        workflow.published_at = None
    _set_published(entity, status, now)

    record_content_revision(
        db,
        entity_type=typ,
        entity_id=entity_id,
        status=status,
        title_bn=getattr(entity, 'title_bn', None),
        title_en=getattr(entity, 'title_en', None),
        content_snapshot={
            'status': status,
            'review_note': payload.review_note,
            'is_published': getattr(entity, 'is_published', None),
        },
        changed_by=admin.id,
        approved_by=workflow.reviewed_by if status in ('APPROVED', 'PUBLISHED', 'SCHEDULED') else None,
        published_by=workflow.published_by if status == 'PUBLISHED' else None,
        change_note=payload.review_note or f'Workflow transition {current} -> {status}',
    )

    if status == 'PUBLISHED' and typ in {'NOTICE', 'CIRCULAR', 'NEWS'}:
        notify_members_of_publication(
            db,
            entity_type=typ,
            entity_id=entity_id,
            title_bn=getattr(entity, 'title_bn', typ),
            body_bn=getattr(entity, 'summary_bn', None) or getattr(entity, 'content_bn', None),
        )

    audit(db, admin, f'WORKFLOW_{status}', typ, entity_id, request.client.host if request.client else None)
    db.commit()
    db.refresh(workflow)
    return {
        'ok': True,
        **_serialize_workflow(workflow),
        'is_published': getattr(entity, 'is_published', None),
    }


