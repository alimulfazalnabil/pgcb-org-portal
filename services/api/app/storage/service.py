from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings
from app.storage.base import StorageBackend
from app.storage.disk import DiskStorageBackend
from app.storage.memory import MemoryStorageBackend

logger = logging.getLogger(__name__)

_storage_instance: StorageBackend | None = None


def get_storage(backend_override: str | None = None, root_override: Path | str | None = None) -> StorageBackend:
    """
    Get or create the singleton storage backend based on configuration.
    Supports persistent_disk, local, and test backends.
    """
    global _storage_instance

    if _storage_instance is not None and backend_override is None and root_override is None:
        return _storage_instance

    backend_type = (backend_override or settings.storage_backend).lower()
    root_path = root_override or settings.storage_root

    if backend_type == 'test' or backend_type == 'memory':
        backend = MemoryStorageBackend()
    elif backend_type in ('persistent_disk', 'local'):
        backend = DiskStorageBackend(root_dir=root_path)
    else:
        logger.warning("Unrecognized storage backend '%s'; defaulting to local disk.", backend_type)
        backend = DiskStorageBackend(root_dir=root_path)

    if backend_override is None and root_override is None:
        _storage_instance = backend

    return backend


def reset_storage() -> None:
    """Reset the global storage singleton (useful in tests)."""
    global _storage_instance
    _storage_instance = None


class StorageService:
    """High-level storage service facade wrapping the configured backend."""

    def __init__(self, backend: StorageBackend | None = None) -> None:
        self.backend = backend or get_storage()

    def save(self, content: bytes, folder: str, filename: str) -> str:
        return self.backend.save(content, folder, filename)

    def read(self, storage_path: str) -> bytes:
        return self.backend.read(storage_path)

    def delete(self, storage_path: str) -> bool:
        return self.backend.delete(storage_path)

    def exists(self, storage_path: str) -> bool:
        return self.backend.exists(storage_path)

    def is_valid_path(self, storage_path: str) -> bool:
        return self.backend.is_valid_path(storage_path)

    def ensure_root_exists(self) -> None:
        self.backend.ensure_root_exists()
