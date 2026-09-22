from __future__ import annotations

import hashlib
from pathlib import Path
import pytest

from app.storage.disk import DiskStorageBackend, safe_name
from app.storage import get_storage

try:
    import fastapi
    from fastapi.testclient import TestClient
    from app.main import app
    HAS_FASTAPI = True
except (ImportError, Exception):
    HAS_FASTAPI = False


def test_member_document_direct_disk_persistence(tmp_path):
    """
    Test direct member document persistent disk write, hierarchy creation,
    byte verification, and SHA-256 integrity.
    """
    storage_root = tmp_path / "var_data_uploads"
    backend = DiskStorageBackend(storage_root)
    backend.ensure_root_exists()

    # 1. Simulate member document write (e.g. member 42 certificate)
    pdf_content = b"%PDF-1.4\n%PGCB Member Certificate Data\n%%EOF"
    pdf_hash = hashlib.sha256(pdf_content).hexdigest()
    filename = "20260923_cert_diploma.pdf"
    folder = "members/42"

    saved_path = backend.save(pdf_content, folder, filename)
    assert Path(saved_path).exists()
    assert Path(saved_path).is_file()

    # 2. Verify physical disk location
    expected_path = (storage_root / "members" / "42" / filename).resolve()
    assert Path(saved_path).resolve() == expected_path

    # 3. Read back and verify byte-for-byte integrity
    read_bytes = backend.read(saved_path)
    assert read_bytes == pdf_content
    assert hashlib.sha256(read_bytes).hexdigest() == pdf_hash


def test_public_asset_direct_disk_persistence(tmp_path):
    """
    Test public asset write to persistent disk, file access, and hash verification.
    """
    storage_root = tmp_path / "var_data_uploads"
    backend = DiskStorageBackend(storage_root)
    backend.ensure_root_exists()

    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    png_hash = hashlib.sha256(png_content).hexdigest()
    filename = "banner_grid_2026.png"

    saved_path = backend.save(png_content, "public", filename)
    assert Path(saved_path).exists()

    expected_path = (storage_root / "public" / filename).resolve()
    assert Path(saved_path).resolve() == expected_path

    read_bytes = backend.read(saved_path)
    assert read_bytes == png_content
    assert hashlib.sha256(read_bytes).hexdigest() == png_hash


def test_persistent_disk_directory_structure(tmp_path):
    """
    Verify ensure_root_exists initializes standard persistent subdirectories.
    """
    storage_root = tmp_path / "uploads"
    backend = DiskStorageBackend(storage_root)
    backend.ensure_root_exists()

    for expected_dir in ("public", "members", "cards", "certificates"):
        dir_path = storage_root / expected_dir
        assert dir_path.exists(), f"Subdirectory {expected_dir} must exist"
        assert dir_path.is_dir()


# ---- FastAPI TestClient HTTP Integration (runs when fastapi is installed) ----

@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi not installed in local environment")
def test_http_member_document_upload_and_download():
    client = TestClient(app)
    r = client.post("/api/v1/auth/login", json={"email": "member@example.org", "password": "ChangeMe123!"})
    assert r.status_code == 200
    cookies = r.cookies

    pdf_content = b"%PDF-1.4\n%test document content for PGCB membership\n%%EOF"
    pdf_sha256 = hashlib.sha256(pdf_content).hexdigest()

    upload_resp = client.post(
        "/api/v1/member/documents?document_type=CERTIFICATE",
        cookies=cookies,
        files={"file": ("diploma_cert.pdf", pdf_content, "application/pdf")},
    )
    assert upload_resp.status_code == 200
    doc_data = upload_resp.json()
    assert doc_data["document_type"] == "CERTIFICATE"
    assert "diploma_cert.pdf" in doc_data["filename"]
    assert doc_data["review_status"] == "PENDING"
    doc_id = doc_data["id"]

    download_resp = client.get(
        f"/api/v1/member/documents/{doc_id}/download",
        cookies=cookies,
    )
    assert download_resp.status_code == 200
    assert download_resp.content == pdf_content
    assert hashlib.sha256(download_resp.content).hexdigest() == pdf_sha256


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi not installed in local environment")
def test_http_public_asset_upload_and_serving():
    client = TestClient(app)
    r = client.post("/api/v1/auth/login", json={"email": "admin@example.org", "password": "ChangeMe123!"})
    assert r.status_code == 200
    admin_cookies = r.cookies

    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"

    upload_resp = client.post(
        "/api/v1/admin/uploads/public",
        cookies=admin_cookies,
        files={"file": ("announcement_logo.png", png_content, "image/png")},
    )
    assert upload_resp.status_code == 200
    data = upload_resp.json()
    assert data["ok"] is True
    assert "announcement_logo.png" in data["filename"]

    get_resp = client.get(data["url"])
    assert get_resp.status_code == 200
    assert get_resp.content == png_content
