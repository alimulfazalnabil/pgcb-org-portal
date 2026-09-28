import hashlib
import hmac
import io
from datetime import datetime
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import current_user, get_db
from app.core.rbac import require_permission
from app.models.core import ContentRevision, Document, SiteSetting, User
from app.schemas.content import DocumentCreate, DocumentResponse, DocumentUpdate
from app.services import audit
from app.utils.storage import delete_file, get_file_bytes, save_bytes, validate_upload_bytes

router = APIRouter(prefix="/documents", tags=["documents"])


def _sign_doc_token(doc_id: int, expires_ts: int) -> str:
    msg = f"doc:{doc_id}:{expires_ts}".encode()
    sig = hmac.new(settings.jwt_secret.encode(), msg, hashlib.sha256).hexdigest()[:32]
    return f"{expires_ts}.{sig}"


def _verify_doc_token(doc_id: int, token: str | None) -> bool:
    if not token or "." not in token:
        return False
    try:
        exp_str, sig = token.split(".", 1)
        exp_ts = int(exp_str)
    except ValueError:
        return False
    if exp_ts < int(datetime.utcnow().timestamp()):
        return False
    expected = _sign_doc_token(doc_id, exp_ts).split(".", 1)[1]
    return hmac.compare_digest(expected, sig)


def _is_private_doc(db: Session, doc: Document) -> bool:
    if (doc.category or "").upper() in ("PRIVATE", "INTERNAL", "CONFIDENTIAL", "MEMBER_ONLY"):
        return True
    flag = db.scalar(select(SiteSetting).where(SiteSetting.key == f"doc_private:{doc.id}"))
    return bool(flag and flag.value == "true")


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    category: str | None = None,
    q: str | None = None,
    year: int | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit
    stmt = (
        select(Document)
        .where(Document.is_published.is_(True))
        .order_by(desc(Document.created_at))
    )
    if category:
        stmt = stmt.where(Document.category == category.upper())
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Document.title_bn.like(like),
                Document.title_en.like(like),
                Document.description_bn.like(like),
            )
        )
    rows = list(db.scalars(stmt.offset(offset).limit(limit)).all())
    if year is not None:
        rows = [d for d in rows if d.created_at and d.created_at.year == year]
    return rows


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc or not doc.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.get("/{document_id}/signed-url")
def create_signed_download_url(
    document_id: int,
    expires_in_seconds: int = Query(default=900, ge=60, le=86400),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    exp_ts = int(datetime.utcnow().timestamp()) + expires_in_seconds
    token = _sign_doc_token(doc.id, exp_ts)
    audit(db, user, "GENERATE_SIGNED_DOC_URL", "DOCUMENT", doc.id)
    db.commit()
    return {
        "document_id": doc.id,
        "token": token,
        "expires_at": exp_ts,
        "download_url": f"/api/v1/documents/{doc.id}/download?token={token}",
    }


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    request: Request,
    token: str | None = None,
    db: Session = Depends(get_db),
):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    is_private = _is_private_doc(db, doc) or not doc.is_published
    actor_user: User | None = None
    try:
        actor_user = current_user(request, db)
    except Exception:
        actor_user = None

    if is_private and not actor_user and not _verify_doc_token(doc.id, token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Controlled document requires authentication or a valid temporary download token",
        )

    try:
        content = get_file_bytes(doc.file_path)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document storage path")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document file not found on storage: {exc}",
        )

    doc.download_count += 1
    if actor_user:
        audit(db, actor_user, "DOWNLOAD_DOCUMENT", "DOCUMENT", doc.id, request.client.host if request.client else None)
    db.commit()

    media_type = doc.content_type or "application/octet-stream"
    filename = doc.file_path.split("/")[-1].split("\\")[-1]
    encoded_filename = filename.encode("ascii", "ignore").decode("ascii") or "document.pdf"

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{encoded_filename}"',
            "Content-Length": str(len(content)),
        },
    )


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document_file(
    file: UploadFile = File(...),
    user: User = Depends(require_permission("document.write")),
):
    """Upload document file to persistent storage, returning file metadata."""
    max_bytes = 25 * 1024 * 1024
    content = await file.read(max_bytes + 1)
    clean_name, unique_name, resolved_ct = validate_upload_bytes(
        file.filename or "doc.pdf",
        file.content_type,
        content,
        max_bytes,
        allow_office=True,
    )

    saved_path = save_bytes(content, "documents", unique_name)
    return {
        "file_path": saved_path,
        "file_size": len(content),
        "content_type": resolved_ct,
        "original_filename": clean_name,
    }


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    data: DocumentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("document.write")),
):
    item = Document(
        title_bn=data.title_bn,
        title_en=data.title_en,
        category=data.category,
        description_bn=data.description_bn,
        file_path=data.file_path,
        file_size=data.file_size,
        content_type=data.content_type,
        version=data.version,
        is_published=data.is_published,
    )
    db.add(item)
    db.flush()
    db.add(
        ContentRevision(
            entity_type="DOCUMENT",
            entity_id=item.id,
            version_number=1,
            workflow_status="PUBLISHED" if item.is_published else "DRAFT",
            snapshot={"title_bn": item.title_bn, "title_en": item.title_en, "category": item.category, "version": item.version, "file_path": item.file_path},
            change_summary="Initial document upload",
            changed_by=user.id,
        )
    )
    audit(db, user, "CREATE_DOCUMENT", "document", item.id)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("document.write")),
):
    item = db.get(Document, document_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(item, field, val)

    item.updated_at = datetime.utcnow()
    audit(db, user, "UPDATE_DOCUMENT", "document", item.id)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("document.write")),
):
    item = db.get(Document, document_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    delete_file(item.file_path)
    audit(db, user, "DELETE_DOCUMENT", "document", item.id)
    db.delete(item)
    db.commit()
    return None

