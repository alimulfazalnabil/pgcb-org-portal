from __future__ import annotations

import gzip
import os
import subprocess
import sys
import types
from pathlib import Path
import pytest
from sqlalchemy import Engine

from app.core.config import settings
from app.db.session import engine, set_engine, SessionLocal
from tests.conftest import validate_test_database_url
from scripts.backup_pgcb import run_disaster_recovery_drill


def test_safety_guard_rejects_primary_database_file():
    """Verify that validate_test_database_url raises RuntimeError if targeting pgcb_portal.db."""
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*pgcb_portal.db"):
        validate_test_database_url("sqlite:///./pgcb_portal.db")

    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*pgcb_portal.db"):
        validate_test_database_url("sqlite:////var/data/pgcb_portal.db")


def test_safety_guard_rejects_production_hostnames():
    """Verify that validate_test_database_url raises RuntimeError if targeting production hosts."""
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*production infrastructure"):
        validate_test_database_url("postgresql+psycopg://user:pass@db.pgcb.org.bd:5432/pgcb_test_db")

    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*production infrastructure"):
        validate_test_database_url("postgresql+psycopg://user:pass@hostseba.com:5432/pgcb_test_db")


def test_safety_guard_rejects_production_app_env(monkeypatch):
    """Verify that validate_test_database_url raises RuntimeError if APP_ENV=production or staging."""
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*APP_ENV=production"):
        validate_test_database_url("sqlite:///./some_test.db")

    monkeypatch.setenv("APP_ENV", "staging")
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*APP_ENV=staging"):
        validate_test_database_url("sqlite:///./some_test.db")


def test_safety_guard_rejects_forbidden_keywords_in_db_name():
    """Verify that database names containing prod/production/staging/live are strictly rejected."""
    forbidden_urls = [
        "postgresql+psycopg://user:pass@127.0.0.1:5432/latest_production",
        "postgresql+psycopg://user:pass@127.0.0.1:5432/my_staging_db",
        "postgresql+psycopg://user:pass@127.0.0.1:5432/prod_app",
        "postgresql+psycopg://user:pass@127.0.0.1:5432/live_database",
    ]
    for url in forbidden_urls:
        with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*forbidden keyword"):
            validate_test_database_url(url)


def test_safety_guard_rejects_primary_db_names():
    """Verify that primary database names (pgcb_portal, pgcb, portal) are rejected."""
    for db_name in ("pgcb_portal", "pgcb", "portal"):
        url = f"postgresql+psycopg://user:pass@127.0.0.1:5432/{db_name}"
        with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*primary application database"):
            validate_test_database_url(url)


def test_safety_guard_rejects_loose_substring_matches():
    """
    Verify that database names containing 'test' only as an accidental substring
    (and not matching approved allowlist or _test/_test_db suffix) are rejected.
    """
    loose_urls = [
        "postgresql+psycopg://user:pass@127.0.0.1:5432/protest_registry",
        "postgresql+psycopg://user:pass@127.0.0.1:5432/contest_entries",
        "postgresql+psycopg://user:pass@127.0.0.1:5432/testament",
    ]
    for url in loose_urls:
        with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*not an authorized test database"):
            validate_test_database_url(url)


def test_safety_guard_rejects_unapproved_hosts_without_explicit_flag():
    """Verify that non-allowlisted external network hosts are rejected without explicit authorization."""
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*not in approved test host list"):
        validate_test_database_url("postgresql+psycopg://user:pass@192.168.1.100:5432/pgcb_test_db")


def test_safety_guard_allows_safe_test_urls():
    """Verify that validate_test_database_url accepts valid test URLs without raising."""
    validate_test_database_url("sqlite:///./test_isolated.db")
    validate_test_database_url("postgresql+psycopg://pgcb_test:pgcb_test_pass@127.0.0.1:5432/pgcb_test_db")
    validate_test_database_url("postgresql+psycopg://runner:pass@postgres:5432/pgcb_test")
    validate_test_database_url("postgresql+psycopg://runner:pass@ci:5432/pgcb_portal_test")
    validate_test_database_url("postgresql+psycopg://runner:pass@localhost:5432/custom_service_test")
    validate_test_database_url("postgresql+psycopg://runner:pass@localhost:5432/analytics_test_db")


def test_safety_guard_allows_disposable_env_opt_in(monkeypatch):
    """Verify that ALLOW_DISPOSABLE_TEST_DB=1 permits non-standard test DB names, but still blocks production keywords."""
    monkeypatch.setenv("ALLOW_DISPOSABLE_TEST_DB", "1")
    # Custom disposable name allowed
    validate_test_database_url("postgresql+psycopg://user:pass@127.0.0.1:5432/ephemeral_ci_runner_42")

    # Forbidden production keywords still blocked even with escape hatch
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*forbidden keyword"):
        validate_test_database_url("postgresql+psycopg://user:pass@127.0.0.1:5432/production_snapshot")


def test_active_test_session_uses_isolated_database():
    """Verify that current test runner is connected to test database and NOT pgcb_portal.db."""
    current_url = str(engine.url)
    assert "pgcb_portal.db" not in current_url
    assert current_url == str(settings.database_url)


def test_explicit_postgresql_database_url_is_respected_in_subprocess():
    """
    Spawn a pytest subprocess with an explicit DATABASE_URL pointing to a custom mock postgresql URL.
    Verify that conftest.py does not silently overwrite it with SQLite.
    """
    api_dir = Path(__file__).resolve().parents[1]
    test_pg_url = "postgresql+psycopg://test_user:test_pass@127.0.0.1:5432/pgcb_test_db"

    check_code = (
        "import os; "
        "from app.core.config import settings; "
        "import app.db.session; "
        "assert os.environ.get('DATABASE_URL') == '" + test_pg_url + "'; "
        "assert settings.database_url == '" + test_pg_url + "'; "
        "assert app.db.session.engine.url.render_as_string(hide_password=False) == '" + test_pg_url + "'; "
        "print('POSTGRES_PRESERVED_SUCCESS')"
    )

    cmd = [
        sys.executable,
        "-c",
        f"import tests.conftest; {check_code}"
    ]

    env = os.environ.copy()
    env["DATABASE_URL"] = test_pg_url
    env["APP_ENV"] = "test"

    proc = subprocess.run(
        cmd,
        cwd=str(api_dir),
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"Subprocess failed with stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    assert "POSTGRES_PRESERVED_SUCCESS" in proc.stdout


def test_unapproved_database_rejected_before_destructive_action_in_subprocess():
    """
    Verify that an unapproved target URL (e.g. localhost/pgcb_portal) fails in subprocess
    at conftest initialization BEFORE any table creation or database interaction.
    """
    api_dir = Path(__file__).resolve().parents[1]
    dangerous_url = "postgresql+psycopg://test_user:test_pass@127.0.0.1:5432/pgcb_portal"

    cmd = [
        sys.executable,
        "-c",
        "import tests.conftest"
    ]

    env = os.environ.copy()
    env["DATABASE_URL"] = dangerous_url
    env["APP_ENV"] = "test"

    proc = subprocess.run(
        cmd,
        cwd=str(api_dir),
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "SAFETY VIOLATION" in proc.stderr
    assert "primary application database" in proc.stderr


def test_set_engine_synchronization():
    """Verify that set_engine updates app.db.session globals, rebinds SessionLocal, and synchronizes settings."""
    orig_url = str(engine.url)
    try:
        new_test_sqlite = "sqlite:///./temp_sync_test.db"
        new_eng = set_engine(new_test_sqlite)
        assert str(new_eng.url) == new_test_sqlite
        assert settings.database_url == new_test_sqlite

        # Verify SessionLocal is bound to the new engine
        session = SessionLocal()
        try:
            assert session.get_bind() == new_eng
        finally:
            session.close()
    finally:
        set_engine(orig_url)


def test_set_engine_does_not_overwrite_unrelated_module_attributes():
    """Verify that set_engine does NOT overwrite attributes named 'engine' that are not SQLAlchemy Engine instances."""
    dummy_mod = types.ModuleType("app._test_dummy_module")
    dummy_mod.engine = "unrelated_string_engine"
    sys.modules["app._test_dummy_module"] = dummy_mod

    orig_url = str(engine.url)
    try:
        new_test_sqlite = "sqlite:///./temp_dummy_test.db"
        set_engine(new_test_sqlite)
        assert dummy_mod.engine == "unrelated_string_engine"
    finally:
        sys.modules.pop("app._test_dummy_module", None)
        set_engine(orig_url)


def test_disaster_recovery_drill_postgresql_metadata(monkeypatch, tmp_path):
    """Verify that disaster recovery drill truthfully reports PostgreSQL dump verification without live restore."""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    (storage_dir / "sample.txt").write_text("institutional record")

    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    # Mock backup_database to return a simulated PostgreSQL dump archive
    pg_dump_path = backup_dir / "db_pgcb_postgresql_daily_test.sql.gz"
    with gzip.open(pg_dump_path, "wt", encoding="utf-8") as f:
        f.write("-- PostgreSQL database dump\nCREATE TABLE test_tab (id serial);\n")

    from scripts.backup_pgcb import _sha256_file
    fake_manifest = {
        "status": "SUCCESS",
        "tier": "daily",
        "type": "database",
        "path": str(pg_dump_path),
        "sha256": _sha256_file(pg_dump_path),
        "size_bytes": pg_dump_path.stat().st_size,
    }

    import scripts.backup_pgcb as bk
    monkeypatch.setattr(bk, "backup_database", lambda url, bdir, tier="daily": fake_manifest)

    res = run_disaster_recovery_drill(
        database_url="postgresql+psycopg://user:pass@127.0.0.1:5432/pgcb_test_db",
        storage_root=storage_dir,
        backup_dir=backup_dir,
    )

    assert res["drill_status"] == "PASSED"
    restore_info = res["restore_verification"]
    assert restore_info["verified"] is True
    assert restore_info["live_restore_performed"] is False
    assert "Live table restore requires a dedicated disposable database cluster" in restore_info["notes"]

    step_names = [s["step"] for s in res["steps"]]
    assert any("PostgreSQL Dump Archive & Format Verification" in s for s in step_names)
