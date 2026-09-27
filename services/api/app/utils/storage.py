from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException

from app.core.config import settings
from app.services import BASE_STORAGE
from app.storage import get_storage, safe_name

# Backward-compatibility alias
_safe_name = safe_name

FORBIDDEN_EXT_SEGMENTS = {
    'exe', 'dll', 'bat', 'cmd', 'sh', 'bash', 'ps1', 'vbs', 'js', 'mjs', 'cjs',
    'php', 'phtml', 'py', 'rb', 'pl', 'cgi', 'jar', 'war', 'html', 'htm', 'svg', 'xml',
}

BASE_EXT_TO_MIMES: dict[str, set[str]] = {
    'pdf': {'application/pdf'},
    'jpg': {'image/jpeg', 'image/jpg'},
    'jpeg': {'image/jpeg', 'image/jpg'},
    'png': {'image/png'},
    'webp': {'image/webp'},
}

VIDEO_EXT_TO_MIMES: dict[str, set[str]] = {
    'mp4': {'video/mp4'},
}

OFFICE_EXT_TO_MIMES: dict[str, set[str]] = {
    'docx': {'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/octet-stream'},
    'xlsx': {'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/octet-stream'},
    'pptx': {'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'application/octet-stream'},
    'doc': {'application/msword', 'application/octet-stream'},
    'xls': {'application/vnd.ms-excel', 'application/octet-stream'},
}


def _matches_magic_bytes(ext: str, content: bytes) -> bool:
    if ext == 'pdf':
        return content.startswith(b'%PDF-')
    if ext == 'png':
        return content.startswith(b'\x89PNG\r\n\x1a\n')
    if ext in ('jpg', 'jpeg'):
        return content.startswith(b'\xff\xd8\xff')
    if ext == 'webp':
        return len(content) >= 12 and content[:4] == b'RIFF' and content[8:12] == b'WEBP'
    if ext == 'mp4':
        return len(content) >= 12 and (content[4:8] == b'ftyp' or content.startswith(b'\x00\x00\x00'))
    if ext in ('docx', 'xlsx', 'pptx'):
        return content.startswith(b'PK\x03\x04') or content.startswith(b'%PDF-')
    if ext in ('doc', 'xls'):
        return content.startswith(b'\xd0\xcf\x11\xe0') or content.startswith(b'PK\x03\x04')
    return False


def validate_upload_bytes(
    filename: str | None,
    content_type: str | None,
    content: bytes,
    max_bytes: int,
    *,
    allow_video: bool = False,
    allow_office: bool = False,
) -> tuple[str, str, str]:
    """
    Validate file extension, MIME type, magic bytes, file size, and filename safety.
    Returns (clean_display_filename, uuid_storage_filename, normalized_content_type).
    """
    raw_name = filename or ''
    if '\x00' in raw_name:
        raise HTTPException(400, 'Invalid filename')
    if not content:
        raise HTTPException(400, 'Uploaded file cannot be empty')
    if len(content) > max_bytes:
        max_mb = max(1, round(max_bytes / (1024 * 1024)))
        raise HTTPException(413, f'Maximum file size is {max_mb} MB')

    clean_name = safe_name(raw_name or 'upload.bin')
    parts = [p.lower() for p in clean_name.split('.') if p]
    if len(parts) < 2:
        raise HTTPException(400, 'File extension is required')

    ext = parts[-1]
    # Reject double-extension executable disguises (e.g. shell.php.pdf)
    if any(seg in FORBIDDEN_EXT_SEGMENTS for seg in parts[:-1]) or ext in FORBIDDEN_EXT_SEGMENTS:
        raise HTTPException(400, 'Executable or script file extensions are not allowed')

    allowed_map = dict(BASE_EXT_TO_MIMES)
    if allow_video:
        allowed_map.update(VIDEO_EXT_TO_MIMES)
    if allow_office:
        allowed_map.update(OFFICE_EXT_TO_MIMES)

    if ext not in allowed_map:
        raise HTTPException(400, f'Unsupported file extension .{ext}')

    normalized_ct = (content_type or '').split(';')[0].strip().lower()
    if normalized_ct and normalized_ct not in allowed_map[ext]:
        # Allow generic application/pdf fallback in upload_document_file if content_type omitted
        raise HTTPException(400, f'Unsupported or mismatched MIME type: {normalized_ct}')

    if not _matches_magic_bytes(ext, content):
        raise HTTPException(400, 'File header magic bytes do not match the declared file type')

    resolved_ct = normalized_ct or next(iter(allowed_map[ext]))
    uuid_storage_name = f'{uuid.uuid4().hex}_{clean_name}'
    return clean_name, uuid_storage_name, resolved_ct


def local_upload(content: bytes, folder: str, filename: str) -> str:
    """Store bytes locally or to persistent disk storage."""
    storage = get_storage()
    return storage.save(content, folder, filename)


def save_bytes(content: bytes, folder: str, filename: str) -> str:
    """Save content bytes to the configured storage backend (Render persistent disk or local)."""
    storage = get_storage()
    return storage.save(content, folder, filename)


def _resolve_within_base_storage(storage_path: str) -> Path:
    if not storage_path or '\x00' in storage_path or '..' in Path(storage_path.replace('\\', '/')).parts:
        raise ValueError(f'Security: Path traversal attempt detected: {storage_path}')
    base = BASE_STORAGE.resolve()
    p = Path(storage_path)
    candidate = p.resolve() if p.is_absolute() else (base / p).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ValueError(f'Security: Path traversal attempt detected: {storage_path}') from exc
    return candidate


def is_local_path(value: str) -> bool:
    """Check if value is a valid file path on the configured storage backend or BASE_STORAGE."""
    if not value:
        return False
    storage = get_storage()
    if storage.is_valid_path(value):
        return True
    try:
        _resolve_within_base_storage(value)
        return True
    except Exception:
        return False


def get_file_bytes(storage_path: str) -> bytes:
    """Retrieve file bytes from the configured storage backend or BASE_STORAGE."""
    if not storage_path:
        raise FileNotFoundError('Empty storage path provided')
    if '\x00' in storage_path or '..' in Path(storage_path.replace('\\', '/')).parts:
        raise ValueError(f'Security: Path traversal attempt detected: {storage_path}')

    storage = get_storage()
    try:
        return storage.read(storage_path)
    except FileNotFoundError:
        candidate = _resolve_within_base_storage(storage_path)
        if candidate.exists() and candidate.is_file():
            return candidate.read_bytes()
        raise FileNotFoundError(f'File not found: {storage_path}')


def delete_file(storage_path: str) -> bool:
    """Safely delete a stored file from storage."""
    if not storage_path:
        return False
    storage = get_storage()
    deleted = storage.delete(storage_path)
    if deleted:
        return True
    try:
        candidate = _resolve_within_base_storage(storage_path)
        if candidate.exists() and candidate.is_file():
            candidate.unlink()
            return True
    except Exception:
        pass
    return False
