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
from app.db.safety import (
    validate_test_database_url,
    parse_authorized_target,
    assert_destructive_database_permitted,
    is_test_migration_active,
)
from scripts.backup_pgcb import run_disaster_recovery_drill


def test_safety_guard_rejects_primary_database_file():
    """Verify that validate_test_database_url raises RuntimeError if targeting pgcb_portal.db in any form."""
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*pgcb_portal.db"):
        validate_test_database_url("sqlite:///./pgcb_portal.db")

    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*pgcb_portal.db"):
        validate_test_database_url("sqlite:////var/data/pgcb_portal.db")

    # URL-encoded filename
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*pgcb_portal.db"):
        validate_test_database_url("sqlite:///./pgcb%5Fportal.db")

    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*pgcb_portal.db"):
        validate_test_database_url("sqlite:///./pgcb.db")

    # Absolute path to repository primary database
    primary_portal = (Path(__file__).resolve().parents[1] / "pgcb_portal.db").resolve()
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*primary database"):
        validate_test_database_url(f"sqlite:///{primary_portal.as_posix()}")


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


def test_safety_guard_allows_safe_ci_and_local_targets():
    """Verify that validate_test_database_url accepts valid default CI and local targets without flags."""
    # SQLite local test fallback
    validate_test_database_url("sqlite:///./test_isolated.db")
    # Standard CI service container database names and hosts
    validate_test_database_url("postgresql+psycopg://pgcb_test:pgcb_test_pass@postgres:5432/pgcb_test_db")
    validate_test_database_url("postgresql+psycopg://runner:pass@ci:5432/pgcb_test_db")
    validate_test_database_url("postgresql+psycopg://runner:pass@127.0.0.1:5432/pgcb_test_db")
    validate_test_database_url("postgresql+psycopg://runner:pass@localhost:5432/pgcb_test")
    validate_test_database_url("postgresql+psycopg://runner:pass@test-db:5432/pgcb_portal_test")
    # IPv6 localhost
    validate_test_database_url("postgresql+psycopg://runner:pass@[::1]:5432/pgcb_test_db")
    # Approved test suffixes on approved hosts
    validate_test_database_url("postgresql+psycopg://runner:pass@localhost:5432/custom_service_test")
    validate_test_database_url("postgresql+psycopg://runner:pass@localhost:5432/analytics_test_db")


def test_parse_authorized_target_formats():
    """Verify that parse_authorized_target handles host, port, IPv6, full URLs, and rejects malformed targets."""
    # host/db
    assert parse_authorized_target("192.168.1.50/ephemeral_test") == ("192.168.1.50", None, "ephemeral_test")
    # host:port/db
    assert parse_authorized_target("192.168.1.50:5433/ephemeral_test") == ("192.168.1.50", 5433, "ephemeral_test")
    # IPv6 [::1]:5432/db
    assert parse_authorized_target("[::1]:5432/pgcb_test_db") == ("::1", 5432, "pgcb_test_db")
    # Full postgresql URL
    assert parse_authorized_target("postgresql://user:pass@ci-host:5432/ci_db") == ("ci-host", 5432, "ci_db")

    # Malformed / empty targets
    with pytest.raises(ValueError, match="Empty authorization target"):
        parse_authorized_target("")
    with pytest.raises(ValueError, match="Empty authorization target"):
        parse_authorized_target("   ")
    with pytest.raises(ValueError, match="Malformed AUTHORIZED_TEST_DB_TARGET"):
        parse_authorized_target("no_slash_target")


def test_safety_guard_rejects_conflicting_broad_authorization_flags(monkeypatch):
    """
    Verify that combining broad boolean flags ALLOW_EXTERNAL_TEST_DB and ALLOW_DISPOSABLE_TEST_DB
    raises a conflicting authorization error to prevent accidental arbitrary target execution.
    """
    monkeypatch.setenv("ALLOW_EXTERNAL_TEST_DB", "1")
    monkeypatch.setenv("ALLOW_DISPOSABLE_TEST_DB", "1")
    url = "postgresql+psycopg://user:pass@192.168.1.100:5432/arbitrary_scratch_db"
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION: Conflicting authorization flags"):
        validate_test_database_url(url)


def test_safety_guard_parsed_target_matching_and_mismatches(monkeypatch):
    """
    Verify that AUTHORIZED_TEST_DB_TARGET parses and enforces host, port, and database matching.
    """
    # 1. Exact host, port, database match succeeds
    monkeypatch.setenv("AUTHORIZED_TEST_DB_TARGET", "192.168.1.50:5433/ephemeral_scratch_42")
    validate_test_database_url("postgresql+psycopg://user:pass@192.168.1.50:5433/ephemeral_scratch_42")

    # 2. Host mismatch
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION: Target host mismatch"):
        validate_test_database_url("postgresql+psycopg://user:pass@192.168.1.99:5433/ephemeral_scratch_42")

    # 3. Port mismatch
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION: Target port mismatch"):
        validate_test_database_url("postgresql+psycopg://user:pass@192.168.1.50:5432/ephemeral_scratch_42")

    # 4. Database mismatch
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION: Target database mismatch"):
        validate_test_database_url("postgresql+psycopg://user:pass@192.168.1.50:5433/wrong_db")

    # 5. Malformed target in environment
    monkeypatch.setenv("AUTHORIZED_TEST_DB_TARGET", "malformed_without_slash")
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION: Malformed AUTHORIZED_TEST_DB_TARGET"):
        validate_test_database_url("postgresql+psycopg://user:pass@192.168.1.50:5433/ephemeral_scratch_42")


def test_safety_guard_url_encoded_credentials_and_database(monkeypatch):
    """
    Verify that URL-encoded credentials (e.g. user%40domain, pass%23123) and URL-encoded
    database names (e.g. my%2Dtest%5Fdb) are decoded and validated correctly.
    """
    # Encoded database name my%2Dtest%5Fdb decodes to my-test_db
    monkeypatch.setenv("AUTHORIZED_TEST_DB_TARGET", "127.0.0.1:5432/my-test_db")
    url = "postgresql+psycopg://user%40corp:pass%23123@127.0.0.1:5432/my%2Dtest%5Fdb"
    validate_test_database_url(url)

    # URL-encoded target string matching URL-encoded DB name
    monkeypatch.setenv("AUTHORIZED_TEST_DB_TARGET", "127.0.0.1:5432/my%2Dtest%5Fdb")
    validate_test_database_url(url)


def test_safety_guard_rejects_forbidden_targets_even_with_explicit_opt_in(monkeypatch):
    """Verify that forbidden production targets remain blocked regardless of authorization flags or targets."""
    # Attempting to authorize production with AUTHORIZED_TEST_DB_TARGET
    monkeypatch.setenv("AUTHORIZED_TEST_DB_TARGET", "127.0.0.1/production_backup")
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*forbidden keyword"):
        validate_test_database_url("postgresql+psycopg://user:pass@127.0.0.1:5432/production_backup")

    # Attempting to authorize primary pgcb_portal
    monkeypatch.setenv("AUTHORIZED_TEST_DB_TARGET", "127.0.0.1/pgcb_portal")
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*primary application database"):
        validate_test_database_url("postgresql+psycopg://user:pass@127.0.0.1:5432/pgcb_portal")

    # Attempting to authorize production host
    monkeypatch.setenv("AUTHORIZED_TEST_DB_TARGET", "db.pgcb.org.bd/pgcb_test_db")
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*production infrastructure"):
        validate_test_database_url("postgresql+psycopg://user:pass@db.pgcb.org.bd:5432/pgcb_test_db")


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


def test_connection_failure_remains_failure_without_sqlite_fallback():
    """
    Verify that when an explicit PostgreSQL target is specified and connection fails,
    it raises a FATAL error and does NOT silently fall back to SQLite.
    """
    api_dir = Path(__file__).resolve().parents[1]
    # Unreachable port on localhost with fast timeout
    unreachable_pg_url = "postgresql+psycopg://test_user:test_pass@127.0.0.1:59999/pgcb_test_db?connect_timeout=2"

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_db_selection.py",
        "-k",
        "test_safety_guard_rejects_primary_database_file"
    ]

    env = os.environ.copy()
    env["DATABASE_URL"] = unreachable_pg_url
    env["APP_ENV"] = "test"

    proc = subprocess.run(
        cmd,
        cwd=str(api_dir),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    # Must fail, NOT fall back to SQLite and succeed
    assert proc.returncode != 0
    combined_output = proc.stdout + proc.stderr
    assert ("FATAL: Explicit PostgreSQL test database connection failed" in combined_output
            or "Connection refused" in combined_output
            or "OperationalError" in combined_output)


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


def test_destructive_operations_guarded_before_execution():
    """
    Verify that alembic/env.py and app/db/seed.py have immediate guards calling
    validate_test_database_url before destructive operations.
    """
    # 1. seed_main with unapproved database in test environment must raise before seeding
    orig_url = str(engine.url)
    try:
        # Intentionally point engine at dangerous URL
        from app.db.seed import main as seed_main
        import app.db.session
        dangerous_eng = set_engine("sqlite:///./pgcb_portal.db")
        with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*pgcb_portal.db"):
            seed_main()
    finally:
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


def test_safety_module_backwards_compatibility_reexport():
    """Verify that tests.conftest re-exports safety module symbols for legacy test compatibility."""
    import tests.conftest as tc
    assert hasattr(tc, "validate_test_database_url")
    assert hasattr(tc, "parse_authorized_target")
    assert hasattr(tc, "assert_destructive_database_permitted")
    assert hasattr(tc, "is_test_migration_active")
    assert tc.validate_test_database_url is validate_test_database_url
    assert tc.parse_authorized_target is parse_authorized_target


def test_assert_destructive_database_permitted_fails_closed_on_invalid_app_env(monkeypatch):
    """
    Verify that assert_destructive_database_permitted fails closed when APP_ENV is:
    1. Unset or empty
    2. Misspelled (e.g. 'prodution', 'tst', 'staging_live')
    3. Production or staging
    4. Unrecognized custom values
    """
    safe_test_url = "sqlite:///./temp_safe_test.db"

    # 1. Unset or empty
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*APP_ENV is unset or empty"):
        assert_destructive_database_permitted(safe_test_url, action_name="test_wipe", app_env="")

    monkeypatch.delenv("APP_ENV", raising=False)
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*APP_ENV is unset or empty"):
        assert_destructive_database_permitted(safe_test_url, action_name="test_wipe")

    # 2. Misspelled environments
    misspelled_envs = ["prodution", "prodd", "stagingg", "tst", "developmnt", "local_prod"]
    for bad_env in misspelled_envs:
        with pytest.raises(RuntimeError, match=f"SAFETY VIOLATION.*denied in APP_ENV='{bad_env}'"):
            assert_destructive_database_permitted(safe_test_url, action_name="test_wipe", app_env=bad_env)

    # 3. Production and staging
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*denied in APP_ENV='production'"):
        assert_destructive_database_permitted(safe_test_url, action_name="test_wipe", app_env="production")

    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*denied in APP_ENV='staging'"):
        assert_destructive_database_permitted(safe_test_url, action_name="test_wipe", app_env="staging")


def test_assert_destructive_database_permitted_fails_closed_against_primary_and_production_targets():
    """
    Verify that destructive actions fail closed against primary and production targets:
    1. SQLite primary database file in test context
    2. Primary postgresql database name in test context
    3. Production host in development context
    4. Forbidden database keyword in development context
    """
    # 1. Test context targeting pgcb_portal.db
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*cannot target primary database file"):
        assert_destructive_database_permitted(
            "sqlite:///./pgcb_portal.db",
            action_name="test_schema_create",
            app_env="test",
        )

    # 2. Test context targeting primary postgres database
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*primary application database"):
        assert_destructive_database_permitted(
            "postgresql+psycopg://user:pass@127.0.0.1:5432/pgcb_portal",
            action_name="test_schema_create",
            app_env="test",
        )

    # 3. Development context targeting production host
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*forbidden production infrastructure host"):
        assert_destructive_database_permitted(
            "postgresql+psycopg://user:pass@db.pgcb.org.bd:5432/pgcb_dev_db",
            action_name="dev_reset",
            app_env="development",
        )

    # 4. Development context targeting database with production keyword
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*forbidden database.*containing production keywords"):
        assert_destructive_database_permitted(
            "postgresql+psycopg://user:pass@127.0.0.1:5432/my_production_db",
            action_name="dev_reset",
            app_env="development",
        )


def test_seed_synthetic_members_fails_closed_on_invalid_or_production_env(monkeypatch):
    """Verify that seed_synthetic_members fails closed when APP_ENV is invalid or production."""
    from app.db.seed import seed_synthetic_members
    from unittest.mock import MagicMock

    mock_db = MagicMock()

    # 1. Misspelled APP_ENV
    monkeypatch.setattr(settings, "app_env", "prodution")
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*denied in APP_ENV='prodution'"):
        seed_synthetic_members(mock_db, count=5)

    # 2. Production APP_ENV
    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*denied in APP_ENV='production'"):
        seed_synthetic_members(mock_db, count=5)


def test_is_test_migration_active_distinguishes_production_from_test(monkeypatch):
    """
    Verify that is_test_migration_active:
    - Returns False for legitimate deployment environments (production, staging) when not under test
    - Returns True when APP_ENV is 'test', PYTEST_CURRENT_TEST is set, or ALEMBIC_TEST_MODE is enabled
    """
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("ALEMBIC_TEST_MODE", raising=False)

    # Legitimate production migrations
    assert is_test_migration_active("production") is False
    assert is_test_migration_active("staging") is False
    assert is_test_migration_active("development") is False

    # Test migration scenarios
    assert is_test_migration_active("test") is True

    # Under pytest
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_migration_check")
    assert is_test_migration_active("production") is True

    # Explicit ALEMBIC_TEST_MODE flag does not override production deployment outside pytest
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("ALEMBIC_TEST_MODE", "1")
    assert is_test_migration_active("production") is False
    assert is_test_migration_active("staging") is False
    assert is_test_migration_active("development") is True
    assert is_test_migration_active("test") is True


def test_alembic_and_safety_module_run_independent_of_pytest():
    """
    Verify that app.db.safety and alembic migration configuration can run in a standalone
    Python process without pytest installed or test fixtures loaded.
    """
    api_dir = Path(__file__).resolve().parents[1]

    # Script imports safety and runs without pytest or tests directory in sys.path
    standalone_code = (
        "import sys; "
        "assert 'pytest' not in sys.modules; "
        "from app.db.safety import is_test_migration_active, validate_test_database_url, assert_destructive_database_permitted; "
        "assert is_test_migration_active('production') is False; "
        "assert is_test_migration_active('test') is True; "
        "print('STANDALONE_SAFETY_SUCCESS')"
    )

    cmd = [sys.executable, "-c", standalone_code]

    env = os.environ.copy()
    env.pop("PYTEST_CURRENT_TEST", None)
    env.pop("ALEMBIC_TEST_MODE", None)
    env["APP_ENV"] = "production"

    proc = subprocess.run(
        cmd,
        cwd=str(api_dir),
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"Standalone execution failed:\n{proc.stderr}\n{proc.stdout}"
    assert "STANDALONE_SAFETY_SUCCESS" in proc.stdout


def test_validate_test_database_url_rejects_empty_or_whitespace_urls():
    """Verify that validate_test_database_url and assert_destructive_database_permitted fail closed on empty URLs."""
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION: Empty database URL"):
        validate_test_database_url("")

    with pytest.raises(RuntimeError, match="SAFETY VIOLATION: Empty database URL"):
        validate_test_database_url("   ")

    with pytest.raises(RuntimeError, match="SAFETY VIOLATION: Destructive operation.*Empty database URL"):
        assert_destructive_database_permitted("", action_name="test_wipe", app_env="test")

    with pytest.raises(RuntimeError, match="SAFETY VIOLATION: Destructive operation.*Empty database URL"):
        assert_destructive_database_permitted("   ", action_name="test_wipe", app_env="test")


def test_safety_guard_rejects_sqlite_alias_and_samefile(tmp_path):
    """
    Verify that validate_test_database_url detects and rejects SQLite paths resolving or
    linking to the real primary repository database file via aliases or samefile identity.
    """
    primary_portal = (Path(__file__).resolve().parents[1] / "pgcb_portal.db").resolve()
    assert primary_portal.exists(), "Primary database file must exist for verification"

    # 1. Alias filename with same primary name in different directory
    fake_alias = tmp_path / "pgcb_portal.db"
    fake_alias.write_text("dummy")
    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*primary database"):
        validate_test_database_url(f"sqlite:///{fake_alias.as_posix()}")

    # 2. Hardlink or alias pointing to real primary database
    link_path = tmp_path / "custom_alias_link.db"
    try:
        os.link(primary_portal, link_path)
        with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*alias/link to primary database"):
            validate_test_database_url(f"sqlite:///{link_path.as_posix()}")
    except (OSError, NotImplementedError):
        # In environments where hard links are restricted, test relative path resolution
        rel_path = f"sqlite:///./{primary_portal.name}"
        with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*primary database"):
            validate_test_database_url(rel_path)


def test_seeding_helpers_validate_exact_bound_engine_before_writing(monkeypatch):
    """
    Verify that seeding helpers inspect the exact database engine bound to the active session
    immediately before attempting any write operations.
    """
    from app.db.seed import seed_synthetic_members
    from unittest.mock import MagicMock
    from sqlalchemy.engine import make_url

    monkeypatch.setattr(settings, "app_env", "test")

    # Mock session bound to primary production database
    mock_db = MagicMock()
    mock_engine = MagicMock()
    mock_engine.url = make_url("postgresql+psycopg://user:pass@127.0.0.1:5432/pgcb_portal")
    mock_db.get_bind.return_value = mock_engine

    with pytest.raises(RuntimeError, match="SAFETY VIOLATION.*primary application database"):
        seed_synthetic_members(mock_db, count=5)

    # Verify no database statements were executed
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


def test_safety_guard_never_leaks_database_credentials_in_error_messages():
    """
    Verify that validate_test_database_url, assert_destructive_database_permitted,
    and parse_authorized_target strictly mask database credentials in all exception messages.
    """
    secret = "SUPER_SECRET_PRODUCTION_PASS_98765"
    url_with_secret = f"postgresql+psycopg://db_admin:{secret}@db.pgcb.org.bd:5432/pgcb_test_db"

    # 1. validate_test_database_url forbidden host check
    with pytest.raises(RuntimeError) as exc_info:
        validate_test_database_url(url_with_secret)
    err_msg = str(exc_info.value)
    assert secret not in err_msg, "Credential secret leaked in validate_test_database_url error!"
    assert "***" in err_msg, "Expected masked credential indicator '***' in error message"

    # 2. assert_destructive_database_permitted forbidden host check
    with pytest.raises(RuntimeError) as exc_info:
        assert_destructive_database_permitted(url_with_secret, action_name="test_wipe", app_env="test")
    err_msg = str(exc_info.value)
    assert secret not in err_msg, "Credential secret leaked in assert_destructive_database_permitted error!"
    assert "***" in err_msg, "Expected masked credential indicator '***' in error message"

    # 3. parse_authorized_target malformed URL with secret
    malformed_url = f"postgresql://db_admin:{secret}@db.pgcb.org.bd:invalid_port/pgcb_test_db"
    with pytest.raises(ValueError) as exc_info:
        parse_authorized_target(malformed_url)
    err_msg = str(exc_info.value)
    assert secret not in err_msg, "Credential secret leaked in parse_authorized_target error!"


def test_parse_authorized_target_rejects_forbidden_hosts_and_keywords_at_parse_time():
    """
    Verify that parse_authorized_target fails fast if the target contains forbidden
    infrastructure hostnames, production keywords, or primary database names.
    """
    # Forbidden host
    with pytest.raises(ValueError, match="Forbidden production infrastructure host"):
        parse_authorized_target("pgcb.org.bd/my_test_db")

    with pytest.raises(ValueError, match="Forbidden production infrastructure host"):
        parse_authorized_target("postgresql://user:pass@hostseba.com:5432/my_test_db")

    # Forbidden keyword in database name
    with pytest.raises(ValueError, match="contains forbidden keyword"):
        parse_authorized_target("127.0.0.1/production_db")

    with pytest.raises(ValueError, match="contains forbidden keyword"):
        parse_authorized_target("postgresql://user:pass@127.0.0.1:5432/live_db")

    # Primary database name
    with pytest.raises(ValueError, match="primary database name"):
        parse_authorized_target("127.0.0.1/pgcb_portal")
