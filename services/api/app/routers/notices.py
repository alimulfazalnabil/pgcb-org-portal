from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.rbac import require_permission
from app.models.core import Notice, User
from app.schemas.content import NoticeCreate, NoticeResponse, NoticeUpdate
from app.services import audit

router = APIRouter(prefix="/notices", tags=["notices"])


@router.get("", response_model=list[NoticeResponse])
def list_notices(
    category: str | None = None,
    priority: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit
    stmt = (
        select(Notice)
        .where(Notice.is_published.is_(True))
        .order_by(Notice.is_pinned.desc(), desc(Notice.published_at), desc(Notice.created_at))
    )
    if category:
        stmt = stmt.where(Notice.category == category.upper())
    if priority:
        stmt = stmt.where(Notice.priority == priority.upper())
    return db.scalars(stmt.offset(offset).limit(limit)).all()


@router.get("/urgent", response_model=NoticeResponse | None)
def get_urgent_notice(db: Session = Depends(get_db)):
    """Returns the latest active urgent or pinned notice for top-bar broadcast."""
    stmt = (
        select(Notice)
        .where(Notice.is_published.is_(True))
        .where((Notice.priority == "URGENT") | (Notice.is_pinned.is_(True)))
        .order_by(Notice.is_pinned.desc(), desc(Notice.created_at))
    )
    return db.scalars(stmt).first()


@router.get("/{notice_id}", response_model=NoticeResponse)
def get_notice(notice_id: int, db: Session = Depends(get_db)):
    notice = db.get(Notice, notice_id)
    if not notice or not notice.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")
    return notice


@router.post("", response_model=NoticeResponse, status_code=status.HTTP_201_CREATED)
def create_notice(
    data: NoticeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("notice.write")),
):
    item = Notice(
        title_bn=data.title_bn,
        title_en=data.title_en,
        content_bn=data.content_bn,
        content_en=data.content_en,
        priority=data.priority,
        category=data.category,
        attachment_url=data.attachment_url,
        is_pinned=data.is_pinned,
        is_published=data.is_published,
        published_at=data.published_at or datetime.utcnow(),
        expires_at=data.expires_at,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    audit(db, user, "CREATE_NOTICE", "notice", item.id)
    db.commit()
    return item


@router.put("/{notice_id}", response_model=NoticeResponse)
def update_notice(
    notice_id: int,
    data: NoticeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("notice.write")),
):
    item = db.get(Notice, notice_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(item, field, val)

    item.updated_at = datetime.utcnow()
    audit(db, user, "UPDATE_NOTICE", "notice", item.id)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{notice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("notice.write")),
):
    item = db.get(Notice, notice_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")

    audit(db, user, "DELETE_NOTICE", "notice", item.id)
    db.delete(item)
    db.commit()
    return None
