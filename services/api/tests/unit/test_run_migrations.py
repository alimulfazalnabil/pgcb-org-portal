from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch
import pytest

from scripts.run_migrations import mask_sensitive, run_migrations


def test_mask_sensitive_database_url_and_secrets():
    """Verify that credentials, passwords, tokens, and query params are thoroughly masked."""
    fake_password_1 = "RECOGNIZABLE_FAKE_PWD_123!"
    fake_password_2 = "P%40ss%3Aw0rd_456"
    fake_token = "RECOGNIZABLE_FAKE_TOKEN_789"
    fake_userless_pwd = "PASSWORD_WITHOUT_USER"

    raw_1 = f"postgresql+psycopg://dummy_user:{fake_password_1}@localhost:5432/mydb"
    masked_1 = mask_sensitive(raw_1)
    assert fake_password_1 not in masked_1
    assert "postgresql+psycopg://dummy_user:***@localhost:5432/mydb" in masked_1

    raw_2 = f"postgresql+psycopg://dummy_user:{fake_password_2}@127.0.0.1:5432/mydb?sslmode=require&token={fake_token}"
    masked_2 = mask_sensitive(raw_2)
    assert fake_password_2 not in masked_2
    assert fake_token not in masked_2
    assert "token=***" in masked_2

    raw_3 = f"postgresql+psycopg://:{fake_userless_pwd}@db.internal:5432/dbname"
    masked_3 = mask_sensitive(raw_3)
    assert fake_userless_pwd not in masked_3
    assert "://:***@db.internal:5432/dbname" in masked_3


def test_fake_password_never_appears_in_migration_failure_logs(caplog):
    """Verify that even when migrations fail and generate tracebacks, secrets are never logged."""
    fake_secret_pwd = "FAKE_CRITICAL_SECRET_PASSWORD_XYZ99"
    fake_url = f"postgresql+psycopg://pg_admin:{fake_secret_pwd}@127.0.0.1:5432/prod_db"

    mock_settings = MagicMock()
    mock_settings.app_env = "production"
    mock_settings.is_production_like = True
    mock_settings.database_url = fake_url

    with patch("app.core.config.settings", mock_settings):
        with patch("alembic.command.upgrade", side_effect=RuntimeError(f"Connection failed: {fake_url}")):
            with caplog.at_level(logging.INFO):
                exit_code = run_migrations()

    assert exit_code == 1
    captured_logs = caplog.text

    # The secret password must NEVER appear in logs or exception tracebacks
    assert fake_secret_pwd not in captured_logs
    assert "pg_admin:***@127.0.0.1:5432/prod_db" in captured_logs


def test_production_unconditionally_rejects_sqlite_in_run_migrations(monkeypatch, caplog):
    """Verify that run_migrations unconditionally rejects SQLite in production even if legacy override is set."""
    monkeypatch.setenv("ALLOW_SQLITE_IN_PRODUCTION", "true")

    mock_settings = MagicMock()
    mock_settings.app_env = "production"
    mock_settings.is_production_like = True
    mock_settings.database_url = "sqlite:///./production_accidental.db"

    with patch("app.core.config.settings", mock_settings):
        with caplog.at_level(logging.ERROR):
            exit_code = run_migrations()

    assert exit_code == 1
    assert "CRITICAL DEPLOYMENT ERROR: Staging and Production environments require a managed PostgreSQL database" in caplog.text


def test_staging_unconditionally_rejects_sqlite_in_run_migrations(monkeypatch, caplog):
    """Verify that run_migrations unconditionally rejects SQLite in staging."""
    mock_settings = MagicMock()
    mock_settings.app_env = "staging"
    mock_settings.is_production_like = True
    mock_settings.database_url = "sqlite:///./staging_accidental.db"

    with patch("app.core.config.settings", mock_settings):
        with caplog.at_level(logging.ERROR):
            exit_code = run_migrations()

    assert exit_code == 1
    assert "CRITICAL DEPLOYMENT ERROR: Staging and Production environments require a managed PostgreSQL database" in caplog.text


def test_run_migrations_uses_configured_database_url():
    """Verify that in development environment, run_migrations invokes Alembic upgrade head."""
    mock_settings = MagicMock()
    mock_settings.app_env = "development"
    mock_settings.is_production_like = False
    mock_settings.database_url = "sqlite:///./dev.db"

    with patch("app.core.config.settings", mock_settings):
        with patch("alembic.command.upgrade") as mock_upgrade:
            exit_code = run_migrations()
            assert exit_code == 0
            mock_upgrade.assert_called_once()
            alembic_cfg = mock_upgrade.call_args[0][0]
            assert alembic_cfg.get_main_option("sqlalchemy.url") is not None
