from __future__ import annotations

from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """Abstract base class for provider-neutral storage backends."""

    @abstractmethod
    def save(self, content: bytes, folder: str, filename: str) -> str:
        """Store bytes under folder/filename and return the storage identifier or path."""
        pass

    @abstractmethod
    def read(self, storage_path: str) -> bytes:
        """Read and return bytes stored at storage_path. Raises FileNotFoundError if missing."""
        pass

    @abstractmethod
    def delete(self, storage_path: str) -> bool:
        """Delete file at storage_path. Returns True if deleted, False otherwise."""
        pass

    @abstractmethod
    def exists(self, storage_path: str) -> bool:
        """Check if file exists at storage_path."""
        pass

    @abstractmethod
    def is_valid_path(self, storage_path: str) -> bool:
        """Validate if storage_path is safe and contained within the backend root."""
        pass

    @abstractmethod
    def ensure_root_exists(self) -> None:
        """Ensure base directory or storage container is initialized and writable."""
        pass
