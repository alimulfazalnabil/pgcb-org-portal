from __future__ import annotations

import io
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
import uuid
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.domain.documents_id import (
    _get_document_storage_dir,
    create_member_document,
    replace_member_document,
)
from app.main import app
from app.models.core import DocumentVerificationEvent, DocumentVersion, Member, MemberDocument, User

client = TestClient(app)

VALID_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"


def _create_test_member(db, email_prefix: str = "doc_test") -> tuple[User, Member]:
    email = f"{email_prefix}_{uuid.uuid4().hex[:8]}@pgcb.org.bd"
    user = User(
        email=email,
        name_en="Engr. Document Tester",
        name_bn="প্রকৌশলী টেস্ট",
        password_hash=hash_password("Pass123!"),
        role="MEMBER",
        is_active=True,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    member = Member(
        user_id=user.id,
        membership_id=f"PGCB-TEST-{uuid.uuid4().hex[:6].upper()}",
        membership_type="Professional",
        status="ACTIVE",
        issue_date=datetime.utcnow() - timedelta(days=100),
        validity_date=datetime.utcnow() + timedelta(days=265),
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return user, member


def test_successful_creation_preserves_new_file_and_database_record():
    """1. Successful creation preserves both the new file and database record."""
    with SessionLocal() as db:
        user, member = _create_test_member(db, "success_create")
        filename = f"national_id_{uuid.uuid4().hex[:6]}.pdf"

        doc = create_member_document(
            db=db,
            member=member,
            document_type="NATIONAL_ID",
            file_bytes=VALID_PDF_BYTES,
            original_filename=filename,
            title="My NID Card",
            user=user,
        )

        assert doc.id is not None
        storage_path = Path(doc.storage_path)
        assert storage_path.exists(), f"Stored file must exist on disk: {storage_path}"
        assert storage_path.read_bytes() == VALID_PDF_BYTES

        # Verify database record
        persisted = db.get(MemberDocument, doc.id)
        assert persisted is not None
        assert persisted.filename == filename
        assert persisted.review_status == "PENDING"
        assert persisted.version == 1

        # Verify DocumentVersion row
        versions = db.scalars(select(DocumentVersion).where(DocumentVersion.document_id == doc.id)).all()
        assert len(versions) == 1
        assert versions[0].version_number == 1
        assert versions[0].storage_path == doc.storage_path

        # Verify DocumentVerificationEvent row
        events = db.scalars(select(DocumentVerificationEvent).where(DocumentVerificationEvent.document_id == doc.id)).all()
        assert len(events) == 1
        assert events[0].action == "UPLOAD"

        # Cleanup test file after test assertion
        if storage_path.exists():
            storage_path.unlink()


def test_creation_failure_after_writing_removes_new_file_and_leaves_no_record():
    """2. A creation failure after writing the file removes that new file and leaves no committed record."""
    with SessionLocal() as db:
        user, member = _create_test_member(db, "fail_create")
        filename = f"nid_fail_{uuid.uuid4().hex[:6]}.pdf"

        captured_paths = []
        original_open = open

        def tracking_open(file, mode="r", *args, **kwargs):
            if "w" in mode and "member_documents" in str(file):
                captured_paths.append(str(file))
            return original_open(file, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=tracking_open):
            with patch.object(db, "commit", side_effect=SQLAlchemyError("Simulated DB commit crash")):
                with pytest.raises(SQLAlchemyError) as exc_info:
                    create_member_document(
                        db=db,
                        member=member,
                        document_type="NATIONAL_ID",
                        file_bytes=VALID_PDF_BYTES,
                        original_filename=filename,
                        title="Failed NID",
                        user=user,
                    )
                assert "Simulated DB commit crash" in str(exc_info.value)

        # Verify the file was written during the operation
        assert len(captured_paths) == 1, "File must have been created during upload attempt"
        written_path = Path(captured_paths[0])

        # Verify that atomic cleanup removed the orphaned file from disk
        assert not written_path.exists(), f"Orphaned file was not cleaned up: {written_path}"

        # Verify no database record was committed
        record_count = db.scalar(
            select(func.count(MemberDocument.id)).where(
                MemberDocument.member_id == member.id,
                MemberDocument.filename == filename,
            )
        )
        assert record_count == 0


def test_successful_replacement_preserves_new_file_and_database_state():
    """3. Successful replacement preserves the expected new file and database state."""
    with SessionLocal() as db:
        user, member = _create_test_member(db, "success_replace")
        v1_name = f"academic_v1_{uuid.uuid4().hex[:6]}.pdf"

        # 1. Create Version 1
        doc = create_member_document(
            db=db,
            member=member,
            document_type="ACADEMIC_CERTIFICATE",
            file_bytes=VALID_PDF_BYTES,
            original_filename=v1_name,
            title="Degree Certificate",
            user=user,
        )
        v1_path = Path(doc.storage_path)
        assert v1_path.exists()

        # 2. Replace with Version 2 (PNG)
        v2_name = f"academic_v2_{uuid.uuid4().hex[:6]}.png"
        replaced = replace_member_document(
            db=db,
            document=doc,
            file_bytes=VALID_PNG_BYTES,
            original_filename=v2_name,
            user=user,
        )

        assert replaced.version == 2
        assert replaced.review_status == "UNDER_REVIEW"
        v2_path = Path(replaced.storage_path)
        assert v2_path.exists(), "New replacement file must exist on disk"
        assert v2_path.read_bytes() == VALID_PNG_BYTES

        # Verify original v1 file is preserved for historical version tracking
        assert v1_path.exists(), "Original version 1 file must be preserved in version history"
        assert v1_path != v2_path

        # Verify versions in database
        versions = db.scalars(
            select(DocumentVersion).where(DocumentVersion.document_id == doc.id).order_by(DocumentVersion.version_number)
        ).all()
        assert len(versions) == 2
        assert versions[0].version_number == 1 and versions[0].storage_path == str(v1_path)
        assert versions[1].version_number == 2 and versions[1].storage_path == str(v2_path)

        # Cleanup test files
        if v1_path.exists():
            v1_path.unlink()
        if v2_path.exists():
            v2_path.unlink()


def test_replacement_failure_removes_only_new_file_and_preserves_original():
    """4. A replacement failure removes only the new file and preserves the original file and record."""
    with SessionLocal() as db:
        user, member = _create_test_member(db, "fail_replace")
        v1_name = f"v1_keep_{uuid.uuid4().hex[:6]}.pdf"

        # 1. Initial document creation
        doc = create_member_document(
            db=db,
            member=member,
            document_type="EMPLOYMENT_DOCUMENT",
            file_bytes=VALID_PDF_BYTES,
            original_filename=v1_name,
            title="Employment Document",
            user=user,
        )
        v1_path = Path(doc.storage_path)
        assert v1_path.exists()
        doc_id = doc.id

        # 2. Attempt replacement, but simulate a commit failure after the new file is written
        v2_name = f"v2_should_clean_{uuid.uuid4().hex[:6]}.png"
        captured_v2_paths = []
        original_open = open

        def tracking_open(file, mode="r", *args, **kwargs):
            if "w" in mode and "member_documents" in str(file) and v1_name not in str(file):
                captured_v2_paths.append(str(file))
            return original_open(file, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=tracking_open):
            with patch.object(db, "commit", side_effect=SQLAlchemyError("Simulated DB crash during replacement commit")):
                with pytest.raises(SQLAlchemyError) as exc_info:
                    replace_member_document(
                        db=db,
                        document=doc,
                        file_bytes=VALID_PNG_BYTES,
                        original_filename=v2_name,
                        user=user,
                    )
                assert "Simulated DB crash during replacement commit" in str(exc_info.value)

        # Confirm that v2 file was written during replacement
        assert len(captured_v2_paths) == 1
        v2_written_path = Path(captured_v2_paths[0])

        # Confirm that v2 file was unlinked and does NOT exist
        assert not v2_written_path.exists(), f"Orphaned replacement file was not cleaned up: {v2_written_path}"

        # Confirm that original v1 file is completely intact
        assert v1_path.exists(), f"Original file must NEVER be deleted on failed replacement: {v1_path}"
        assert v1_path.read_bytes() == VALID_PDF_BYTES

        # Confirm database state was rolled back to original
        db.expire_all()
        refreshed = db.get(MemberDocument, doc_id)
        assert refreshed.version == 1
        assert refreshed.storage_path == str(v1_path)
        assert refreshed.review_status == "PENDING"

        # Confirm no Version 2 exists in database
        v2_rows = db.scalars(
            select(DocumentVersion).where(
                DocumentVersion.document_id == doc_id,
                DocumentVersion.version_number == 2,
            )
        ).all()
        assert len(v2_rows) == 0

        # Cleanup original test file
        if v1_path.exists():
            v1_path.unlink()


def test_flush_failure_triggers_rollback_and_filesystem_cleanup():
    """5. Flush failure triggers appropriate rollback and filesystem cleanup."""
    with SessionLocal() as db:
        user, member = _create_test_member(db, "flush_fail")
        filename = f"flush_fail_{uuid.uuid4().hex[:6]}.pdf"

        captured_paths = []
        original_open = open

        def tracking_open(file, mode="r", *args, **kwargs):
            if "w" in mode and "member_documents" in str(file):
                captured_paths.append(str(file))
            return original_open(file, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=tracking_open):
            with patch.object(db, "flush", side_effect=SQLAlchemyError("Database constraint flush error")):
                with pytest.raises(SQLAlchemyError) as exc_info:
                    create_member_document(
                        db=db,
                        member=member,
                        document_type="NATIONAL_ID",
                        file_bytes=VALID_PDF_BYTES,
                        original_filename=filename,
                        user=user,
                    )
                assert "Database constraint flush error" in str(exc_info.value)

        assert len(captured_paths) == 1
        written_path = Path(captured_paths[0])
        assert not written_path.exists(), "File created before flush must be unlinked on flush failure"

        # Confirm transaction was rolled back
        count = db.scalar(select(func.count(MemberDocument.id)).where(MemberDocument.filename == filename))
        assert count == 0


def test_early_validation_prevents_file_creation_completely():
    """6. Early category validation rejects invalid categories without writing any file to disk."""
    with SessionLocal() as db:
        user, member = _create_test_member(db, "early_val")
        filename = f"invalid_cat_{uuid.uuid4().hex[:6]}.pdf"

        captured_writes = []
        original_open = open

        def tracking_open(file, mode="r", *args, **kwargs):
            if "w" in mode and "member_documents" in str(file):
                captured_writes.append(str(file))
            return original_open(file, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=tracking_open):
            with pytest.raises(HTTPException) as exc_info:
                create_member_document(
                    db=db,
                    member=member,
                    document_type="INVALID_NON_EXISTENT_CATEGORY",
                    file_bytes=VALID_PDF_BYTES,
                    original_filename=filename,
                    user=user,
                )
            assert exc_info.value.status_code == 400
            assert "Invalid document category" in exc_info.value.detail

        assert len(captured_writes) == 0, "No file should have been written when validation fails early"


def test_http_endpoint_upload_failure_cleans_up_orphaned_file():
    """7. HTTP endpoint failures clean up files and return HTTP 500 error."""
    with SessionLocal() as db:
        user, member = _create_test_member(db, "http_fail")
        token = create_access_token(user.id, roles=[user.role])
        headers = {"Authorization": f"Bearer {token}"}

    captured_paths = []
    original_open = open

    def tracking_open(file, mode="r", *args, **kwargs):
        if "w" in mode and "member_documents" in str(file):
            captured_paths.append(str(file))
        return original_open(file, mode, *args, **kwargs)

    # Use a TestClient that does not re-raise unhandled server exceptions as Python exceptions
    error_client = TestClient(app, raise_server_exceptions=False)

    # Simulate commit failure in FastAPI request cycle
    with patch("builtins.open", side_effect=tracking_open):
        with patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError("DB server disconnected")):
            files = {"file": ("http_test.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
            data = {"document_type": "NATIONAL_ID", "title": "HTTP Upload"}
            res = error_client.post("/api/v1/member/documents", headers=headers, files=files, data=data)

    assert res.status_code >= 500 or res.status_code == 400
    assert len(captured_paths) == 1, "File was initially written by the upload service"
    written_file = Path(captured_paths[0])
    assert not written_file.exists(), f"HTTP upload failure left an orphaned file: {written_file}"

