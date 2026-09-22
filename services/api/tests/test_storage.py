from __future__ import annotations

import os
import tempfile
from pathlib import Path
import pytest

from app.storage import (
    DiskStorageBackend,
    MemoryStorageBackend,
    StorageService,
    get_storage,
    reset_storage,
    safe_name,
)
from app.utils.storage import (
    save_bytes,
    get_file_bytes,
    delete_file,
    is_local_path,
)


def test_safe_name():
    assert safe_name("my photo.jpg") == "my_photo.jpg"
    assert safe_name("../../../etc/passwd") == "passwd"
    assert safe_name("..\\..\\secret.png") == "secret.png"
    assert safe_name("test<>:\"|?*.pdf") == "test.pdf"
    assert safe_name("") == "upload.bin"
    assert safe_name("___") == "___"


def test_disk_storage_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DiskStorageBackend(root_dir=tmpdir)
        storage.ensure_root_exists()

        content = b"Hello, Render Persistent Disk!"
        path = storage.save(content, "documents/test", "hello.txt")

        assert os.path.exists(path)
        assert storage.exists(path)
        assert storage.read(path) == content

        # Test relative path read
        rel_path = "documents/test/hello.txt"
        assert storage.read(rel_path) == content

        # Delete
        assert storage.delete(path) is True
        assert not storage.exists(path)
        assert storage.delete(path) is False

        with pytest.raises(FileNotFoundError):
            storage.read(path)


def test_path_traversal_rejection():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = DiskStorageBackend(root_dir=tmpdir)

        # Attempt to save or read outside root_dir
        with pytest.raises(ValueError, match="Path traversal"):
            storage.read("../../etc/passwd")

        with pytest.raises(ValueError, match="Path traversal"):
            storage._resolve_candidate("/etc/shadow")


def test_memory_storage_lifecycle():
    storage = MemoryStorageBackend()
    content = b"In-memory test data"
    path = storage.save(content, "cache", "data.bin")

    assert storage.exists(path)
    assert storage.read(path) == content
    assert storage.delete(path) is True
    assert not storage.exists(path)

    with pytest.raises(FileNotFoundError):
        storage.read(path)


def test_utils_storage_backward_compatibility():
    with tempfile.TemporaryDirectory() as tmpdir:
        reset_storage()
        # Initialize storage with temp root
        storage = get_storage(backend_override="local", root_override=tmpdir)

        content = b"Backward compatibility payload"
        stored_path = save_bytes(content, "public", "asset.txt")

        assert is_local_path(stored_path)
        assert get_file_bytes(stored_path) == content
        assert delete_file(stored_path) is True
        assert not storage.exists(stored_path)

        reset_storage()
