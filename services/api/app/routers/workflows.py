from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rbac import require_permission
from app.db.session import get_db
from app.models import ContentWorkflow, Circular, Journal, Event, User
from app.services import audit

router = APIRouter(prefix='/admin/workflows', tags=['cms-workflows'])

class WorkflowTransition(BaseModel):
    status: str = Field(pattern=r'^(DRAFT|IN_REVIEW|APPROVED|SCHEDULED|PUBLISHED|ARCHIVED)$')
    review_note: str | None = Field(default=None, max_length=4000)
    scheduled_at: datetime | None = None

CONTENT_MAP = {'CIRCULAR': Circular, 'JOURNAL': Journal, 'EVENT': Event}


def _set_published(entity, status: str, now: datetime):
    if hasattr(entity, 'is_published'):
        entity.is_published = status == 'PUBLISHED'
    if status == 'PUBLISHED' and hasattr(entity, 'published_at') and not entity.published_at:
        entity.published_at = now

@router.get('')
def list_workflows(entity_type: str | None = None, status: str | None = None, _: User = Depends(require_permission('content.read')), db: Session = Depends(get_db)):
    stmt = select(ContentWorkflow).order_by(ContentWorkflow.updated_at.desc())
    if entity_type: stmt = stmt.where(ContentWorkflow.entity_type == entity_type.upper())
    if status: stmt = stmt.where(ContentWorkflow.status == status.upper())
    rows = db.scalars(stmt.limit(500)).all()
    return [{'id': w.id, 'entity_type': w.entity_type, 'entity_id': w.entity_id, 'status': w.status, 'review_note': w.review_note, 'scheduled_at': w.scheduled_at, 'reviewed_by': w.reviewed_by, 'published_by': w.published_by, 'reviewed_at': w.reviewed_at, 'published_at': w.published_at} for w in rows]

@router.post('/{entity_type}/{entity_id}/transition')
def transition(entity_type: str, entity_id: int, payload: WorkflowTransition, request: Request, admin: User = Depends(require_permission('content.publish')), db: Session = Depends(get_db)):
    typ = entity_type.upper()
    model = CONTENT_MAP.get(typ)
    if not model:
        raise HTTPException(400, 'Unsupported content type')
    entity = db.get(model, entity_id)
    if not entity:
        raise HTTPException(404, 'Content not found')
    workflow = db.scalar(select(ContentWorkflow).where(ContentWorkflow.entity_type == typ, ContentWorkflow.entity_id == entity_id))
    if not workflow:
        workflow = ContentWorkflow(entity_type=typ, entity_id=entity_id)
        db.add(workflow)
    status = payload.status
    current = (workflow.status if workflow else None) or 'DRAFT'
    allowed = {
        'DRAFT': {'IN_REVIEW', 'PUBLISHED'},
        'IN_REVIEW': {'DRAFT', 'APPROVED'},
        'APPROVED': {'IN_REVIEW', 'SCHEDULED', 'PUBLISHED'},
        'SCHEDULED': {'APPROVED', 'PUBLISHED'},
        'PUBLISHED': {'ARCHIVED'},
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
    if status in {'IN_REVIEW', 'APPROVED'}:
        workflow.reviewed_by = admin.id; workflow.reviewed_at = now
    if status == 'PUBLISHED':
        workflow.published_by = admin.id; workflow.published_at = now
    if status == 'ARCHIVED':
        workflow.published_at = None
    _set_published(entity, status, now)
    audit(db, admin, f'WORKFLOW_{status}', typ, entity_id, request.client.host if request.client else None)
    db.commit(); db.refresh(workflow)
    return {'ok': True, 'entity_type': typ, 'entity_id': entity_id, 'status': workflow.status, 'is_published': getattr(entity, 'is_published', None), 'scheduled_at': workflow.scheduled_at}
