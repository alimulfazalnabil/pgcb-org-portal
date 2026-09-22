from __future__ import annotations

from pathlib import Path
from app.storage.base import StorageBackend
from app.storage.disk import safe_name


class MemoryStorageBackend(StorageBackend):
    """In-memory storage backend for unit testing and ephemeral mocks."""

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}

    def ensure_root_exists(self) -> None:
        pass

    def is_valid_path(self, storage_path: str) -> bool:
        if not storage_path:
            return False
        return '..' not in storage_path

    def save(self, content: bytes, folder: str, filename: str) -> str:
        clean_fn = safe_name(filename)
        folder_clean = '/'.join(p for p in folder.replace('\\', '/').split('/') if p and p != '..')
        key = f'{folder_clean}/{clean_fn}' if folder_clean else clean_fn
        self._files[key] = content
        return f'memory://{key}'

    def read(self, storage_path: str) -> bytes:
        if not storage_path:
            raise FileNotFoundError('Empty storage path provided')
        key = storage_path.removeprefix('memory://').strip('/')
        if key in self._files:
            return self._files[key]
        raise FileNotFoundError(f'File not found: {storage_path}')

    def delete(self, storage_path: str) -> bool:
        if not storage_path:
            return False
        key = storage_path.removeprefix('memory://').strip('/')
        if key in self._files:
            del self._files[key]
            return True
        return False

    def exists(self, storage_path: str) -> bool:
        if not storage_path:
            return False
        key = storage_path.removeprefix('memory://').strip('/')
        return key in self._files
