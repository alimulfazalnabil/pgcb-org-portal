import io
from datetime import datetime
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.rbac import require_permission
from app.models.core import Document, User
from app.schemas.content import DocumentCreate, DocumentResponse, DocumentUpdate
from app.services import audit
from app.utils.storage import delete_file, get_file_bytes, save_bytes

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    category: str | None = None,
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
    return db.scalars(stmt.offset(offset).limit(limit)).all()


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc or not doc.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.get("/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc or not doc.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        content = get_file_bytes(doc.file_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document file not found on storage: {exc}",
        )

    # Increment download count
    doc.download_count += 1
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
    content = await file.read()
    if len(content) > 25 * 1024 * 1024:  # 25 MB limit for docs
        raise HTTPException(status_code=400, detail="File exceeds maximum 25 MB limit")

    ext = (file.filename or "doc.pdf").split(".")[-1].lower()
    allowed_exts = {"pdf", "docx", "doc", "xlsx", "xls", "pptx", "png", "jpg", "jpeg"}
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"File extension .{ext} is not allowed")

    saved_path = save_bytes(content, "documents", file.filename or f"doc_{int(datetime.utcnow().timestamp())}.{ext}")
    return {
        "file_path": saved_path,
        "file_size": len(content),
        "content_type": file.content_type or "application/pdf",
        "original_filename": file.filename,
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
    db.commit()
    db.refresh(item)
    audit(db, user, "CREATE_DOCUMENT", "document", item.id)
    db.commit()
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
