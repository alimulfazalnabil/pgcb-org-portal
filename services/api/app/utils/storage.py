from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.services import BASE_STORAGE
from app.storage import get_storage, safe_name

# Backward-compatibility alias
_safe_name = safe_name


def local_upload(content: bytes, folder: str, filename: str) -> str:
    """Store bytes locally or to persistent disk storage."""
    storage = get_storage()
    return storage.save(content, folder, filename)


def save_bytes(content: bytes, folder: str, filename: str) -> str:
    """Save content bytes to the configured storage backend (Render persistent disk or local)."""
    storage = get_storage()
    return storage.save(content, folder, filename)


def is_local_path(value: str) -> bool:
    """Check if value is a valid file path on the configured storage backend or BASE_STORAGE."""
    if not value:
        return False
    storage = get_storage()
    if storage.is_valid_path(value):
        return True
    try:
        path = Path(value).resolve()
        base = BASE_STORAGE.resolve()
        path.relative_to(base)
        return True
    except Exception:
        return False


def get_file_bytes(storage_path: str) -> bytes:
    """Retrieve file bytes from the configured storage backend or BASE_STORAGE."""
    if not storage_path:
        raise FileNotFoundError('Empty storage path provided')

    storage = get_storage()
    try:
        return storage.read(storage_path)
    except (FileNotFoundError, ValueError):
        # Fallback check against BASE_STORAGE
        p = Path(storage_path).resolve()
        if p.exists() and p.is_file():
            return p.read_bytes()
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
        p = Path(storage_path).resolve()
        if p.exists() and p.is_file():
            p.unlink()
            return True
    except Exception:
        pass
    return False
