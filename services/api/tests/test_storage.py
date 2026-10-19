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
        reset_storage()


REPO_ROOT = Path(__file__).resolve().parents[3]
REPO_STORAGE = (REPO_ROOT / "storage").resolve()
API_STORAGE = (REPO_ROOT / "services" / "api" / "storage").resolve()


def test_storage_isolation_and_no_repo_pollution():
    """Verify that test storage uses an isolated directory and never writes to repo root storage."""
    from app.core.config import settings
    import app.services
    from app.utils.storage import save_bytes, delete_file

    # Active settings and BASE_STORAGE must point to an isolated location
    active_storage = Path(settings.storage_root).resolve()
    assert active_storage != REPO_STORAGE, f"Test storage root must not be repo storage: {active_storage}"
    assert active_storage != API_STORAGE, f"Test storage root must not be api storage: {active_storage}"
    assert app.services.BASE_STORAGE == active_storage

    # Save a canary file through application storage
    canary_content = b"isolation-canary-payload"
    canary_name = "test_isolation_canary.bin"
    saved = save_bytes(canary_content, "public", canary_name)

    saved_p = Path(saved).resolve()
    assert saved_p.exists()
    assert active_storage in saved_p.parents or saved_p.is_relative_to(active_storage)
    assert not (REPO_STORAGE / "public" / canary_name).exists()
    assert not (API_STORAGE / "public" / canary_name).exists()

    # Clean up canary
    delete_file(saved)
    assert not saved_p.exists()


def test_card_generation_writes_only_to_isolated_storage():
    """1. Verify that institutional card generation writes only to isolated storage, not repo storage."""
    from app.core.config import settings
    from app.models import Member, User
    from app.routers.card import build_card, build_card_back

    active_storage = Path(settings.storage_root).resolve()

    test_id = "PGD-TEST-ISOLATION-01"
    member = Member(
        id=9991,
        membership_id=test_id,
        status="ACTIVE",
        designation_bn="সহকারী প্রকৌশলী",
        designation_en="Assistant Engineer",
    )
    user = User(
        id=9991,
        name_bn="সাজিদ হাসান",
        name_en="Sajid Hasan",
        email="sajid.test@example.org",
    )

    card_path = build_card(member, user)
    back_path = build_card_back(member)

    try:
        assert card_path.exists()
        assert back_path.exists()
        assert active_storage in card_path.resolve().parents or card_path.resolve().is_relative_to(active_storage)
        assert active_storage in back_path.resolve().parents or back_path.resolve().is_relative_to(active_storage)

        # Must never exist in repo storage
        assert not (REPO_STORAGE / "cards" / f"{test_id}.png").exists()
        assert not (REPO_STORAGE / "cards" / f"{test_id}_back.png").exists()
    finally:
        if card_path.exists():
            card_path.unlink()
        if back_path.exists():
            back_path.unlink()


def test_certificate_generation_writes_only_to_isolated_storage():
    """2. Verify that certificate rendering writes only to isolated storage, not repo storage."""
    from datetime import datetime
    from app.core.config import settings
    from app.models import Certificate
    from app.services.certificate_service import CertificateService

    active_storage = Path(settings.storage_root).resolve()

    test_cert_no = "PGCB-CERT-ISOLATION-99"
    cert = Certificate(
        id=9992,
        certificate_no=test_cert_no,
        recipient_name="মাহমুদ আলম",
        title_bn="বার্ষিক সাধারণ সম্মেলন ২০২৬",
        issue_date=datetime.utcnow(),
    )

    png_path, pdf_path = CertificateService.render_certificate_files(cert)

    try:
        assert png_path.exists()
        assert pdf_path.exists()
        assert active_storage in png_path.resolve().parents or png_path.resolve().is_relative_to(active_storage)
        assert active_storage in pdf_path.resolve().parents or pdf_path.resolve().is_relative_to(active_storage)

        # Must never exist in repo storage
        assert not (REPO_STORAGE / "certificates" / f"{test_cert_no}.png").exists()
        assert not (REPO_STORAGE / "certificates" / f"{test_cert_no}.pdf").exists()
    finally:
        if png_path.exists():
            png_path.unlink()
        if pdf_path.exists():
            pdf_path.unlink()


def test_upload_path_using_get_storage_writes_only_to_isolated_storage():
    """3. Verify that document/asset uploads through get_storage write only to isolated storage."""
    from app.core.config import settings
    from app.utils.storage import save_bytes, delete_file

    active_storage = Path(settings.storage_root).resolve()

    filename = "isolation_test_upload.pdf"
    content = b"%PDF-1.4\n%Test isolated upload bytes\n%%EOF"

    stored_path_str = save_bytes(content, "member_documents", filename)
    stored_path = Path(stored_path_str).resolve()

    try:
        assert stored_path.exists()
        assert active_storage in stored_path.parents or stored_path.is_relative_to(active_storage)
        assert not (REPO_STORAGE / "member_documents" / filename).exists()
    finally:
        delete_file(stored_path_str)
        assert not stored_path.exists()


def test_cleanup_teardown_preserves_preexisting_repo_storage_files():
    """4. Verify that creating, using, and cleaning up a temporary storage instance never alters repo files."""
    # Find sample pre-existing files in repo storage
    cards_dir = REPO_STORAGE / "cards"
    assert cards_dir.exists(), f"Repository cards directory must exist at {cards_dir}"

    sample_files = list(cards_dir.glob("*.png"))[:3]
    assert len(sample_files) > 0, "Expected pre-existing test cards in repository"

    # Snapshot modification times and sizes
    snapshots = {f: (f.stat().st_size, f.stat().st_mtime_ns) for f in sample_files}

    # Simulate ephemeral test storage cycle
    with tempfile.TemporaryDirectory(prefix="pgcb_teardown_test_") as temp_dir:
        temp_path = Path(temp_dir)
        temp_backend = DiskStorageBackend(root_dir=temp_path)
        temp_backend.ensure_root_exists()

        # Write arbitrary files into temp storage
        temp_file = temp_backend.save(b"ephemeral data", "cards", "ADM-TEST-001.png")
        assert Path(temp_file).exists()

    # After temp directory is deleted/cleaned up:
    for f, (orig_size, orig_mtime) in snapshots.items():
        assert f.exists(), f"Pre-existing repo file {f.name} must still exist after temp cleanup"
        current_stat = f.stat()
        assert current_stat.st_size == orig_size, f"File {f.name} size changed from {orig_size} to {current_stat.st_size}"
        assert current_stat.st_mtime_ns == orig_mtime, f"File {f.name} mtime was modified"


def test_isolation_guard_fails_when_storage_writer_pointed_at_repo_root():
    """5. Verify that our isolation assertion correctly detects and fails if storage points at repo storage."""
    def check_storage_isolated(candidate_path: Path | str) -> None:
        cand = Path(candidate_path).resolve()
        if cand == REPO_STORAGE or REPO_STORAGE in cand.parents:
            raise AssertionError(f"Isolation violation: target storage path points to repository storage: {cand}")

    # Deliberately pointing to REPO_STORAGE MUST raise an AssertionError
    with pytest.raises(AssertionError, match="Isolation violation"):
        check_storage_isolated(REPO_STORAGE)

    with pytest.raises(AssertionError, match="Isolation violation"):
        check_storage_isolated(REPO_STORAGE / "cards")

    # Pointing to isolated test directory MUST NOT raise
    from app.core.config import settings
    active_storage = Path(settings.storage_root).resolve()
    check_storage_isolated(active_storage)
