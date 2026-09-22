from __future__ import annotations

import logging
import os
from pathlib import Path

from app.storage.base import StorageBackend

logger = logging.getLogger(__name__)


def safe_name(filename: str) -> str:
    """Sanitize filename to prevent path injection and unwanted characters."""
    raw = (filename or 'upload.bin').replace('\\', '/').split('/')[-1].replace(' ', '_')
    cleaned = ''.join(ch for ch in raw if ch.isalnum() or ch in '._-')
    return cleaned or 'upload.bin'


class DiskStorageBackend(StorageBackend):
    """
    Provider-neutral storage backend storing files on a local filesystem or
    Render Persistent Disk mounted at /var/data (e.g. /var/data/uploads).
    Enforces strict path-traversal prevention.
    """

    def __init__(self, root_dir: Path | str) -> None:
        self.root_dir = Path(root_dir).resolve()

    def _resolve_candidate(self, storage_path: Path | str) -> Path:
        """Resolve a candidate path and verify it is strictly within root_dir."""
        p = Path(storage_path)
        if p.is_absolute():
            candidate = p.resolve()
        else:
            candidate = (self.root_dir / p).resolve()

        # Strict path-traversal check
        try:
            candidate.relative_to(self.root_dir)
        except ValueError as exc:
            raise ValueError(f'Security: Path traversal attempt detected: {storage_path}') from exc

        return candidate

    def is_valid_path(self, storage_path: str) -> bool:
        """Return True if storage_path resolves safely inside root_dir."""
        if not storage_path:
            return False
        try:
            self._resolve_candidate(storage_path)
            return True
        except (ValueError, Exception):
            return False

    def ensure_root_exists(self) -> None:
        """
        Create root_dir and standard subdirectories.
        Called on application startup lifespan.
        """
        try:
            self.root_dir.mkdir(parents=True, exist_ok=True)
            for sub in ('public', 'members', 'cards', 'certificates'):
                (self.root_dir / sub).mkdir(parents=True, exist_ok=True)

            # Test write access with a canary file
            canary = self.root_dir / '.write_test'
            canary.write_text('ok')
            canary.unlink(missing_ok=True)
            logger.info('Persistent disk storage root initialized successfully at: %s', self.root_dir)
        except OSError as exc:
            logger.warning(
                'Could not fully initialize storage root directory (%s): %s. '
                'This is expected in ephemeral pre-deploy or build environments without mounted disks.',
                self.root_dir,
                exc,
            )

    def save(self, content: bytes, folder: str, filename: str) -> str:
        """Store bytes under folder/filename and return absolute path string."""
        clean_filename = safe_name(filename)
        # Clean folder parts to eliminate empty, slash or dot-dot entries
        folder_parts = [p for p in Path(folder).parts if p not in ('.', '..', '/', '\\')]
        target_dir = self.root_dir.joinpath(*folder_parts)
        candidate = self._resolve_candidate(target_dir / clean_filename)

        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes(content)
        return str(candidate)

    def read(self, storage_path: str) -> bytes:
        """Read and return bytes stored at storage_path. Raises FileNotFoundError if missing."""
        if not storage_path:
            raise FileNotFoundError('Empty storage path provided')

        candidate = self._resolve_candidate(storage_path)
        if not candidate.exists() or not candidate.is_file():
            raise FileNotFoundError(f'File not found: {storage_path}')

        return candidate.read_bytes()

    def delete(self, storage_path: str) -> bool:
        """Safely delete file at storage_path. Returns True if deleted, False otherwise."""
        if not storage_path:
            return False
        try:
            candidate = self._resolve_candidate(storage_path)
            if candidate.exists() and candidate.is_file():
                candidate.unlink()
                return True
        except Exception:
            return False
        return False

    def exists(self, storage_path: str) -> bool:
        """Return True if the file exists at storage_path."""
        if not storage_path:
            return False
        try:
            candidate = self._resolve_candidate(storage_path)
            return candidate.exists() and candidate.is_file()
        except Exception:
            return False
