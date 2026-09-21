from __future__ import annotations

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ContentWorkflow, Circular, Journal, Event

MODEL_BY_TYPE = {'CIRCULAR': Circular, 'JOURNAL': Journal, 'EVENT': Event}


def publish_scheduled_content(db: Session) -> int:
    now = datetime.utcnow()
    rows = db.scalars(select(ContentWorkflow).where(ContentWorkflow.status == 'SCHEDULED', ContentWorkflow.scheduled_at.is_not(None), ContentWorkflow.scheduled_at <= now).limit(500)).all()
    count = 0
    for workflow in rows:
        model = MODEL_BY_TYPE.get(workflow.entity_type)
        entity = db.get(model, workflow.entity_id) if model else None
        if not entity:
            workflow.status = 'ARCHIVED'
            continue
        workflow.status = 'PUBLISHED'
        workflow.published_at = now
        if hasattr(entity, 'is_published'):
            entity.is_published = True
        if hasattr(entity, 'published_at') and not entity.published_at:
            entity.published_at = now
        count += 1
    return count
