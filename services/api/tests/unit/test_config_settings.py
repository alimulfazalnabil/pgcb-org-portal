from __future__ import annotations

import pytest
from pydantic import ValidationError
from app.core.config import Settings


SYNTHETIC_TEST_SECRET = "synthetic-test-secret-at-least-32-chars-long-for-testing"
SYNTHETIC_PG_URL = "postgresql+psycopg://test_user:test_pass@127.0.0.1:5432/test_db"


def test_development_defaults_allow_sqlite_and_dev_secret(monkeypatch):
    """Verify that development environment boots cleanly with defaults."""
    monkeypatch.setenv("APP_ENV", "development")
    s = Settings(app_env="development", database_url="sqlite:///./test.db")
    assert s.app_env == "development"
    assert s.database_url.startswith("sqlite")
    assert not s.is_production_like


def test_production_rejects_missing_or_default_jwt_secret(monkeypatch):
    """Verify that production rejects missing or placeholder JWT_SECRET."""
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            app_env="production",
            database_url=SYNTHETIC_PG_URL,
            jwt_secret="dev-only-secret-change-me-please-use-a-32-byte-random-secret",
        )
    assert "JWT_SECRET is missing or using the development placeholder" in str(exc_info.value)


def test_production_rejects_short_jwt_secret(monkeypatch):
    """Verify that production rejects secrets shorter than 32 characters, indicating length."""
    monkeypatch.setenv("APP_ENV", "production")
    short_secret = "short-secret-only-24-chr"
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            app_env="production",
            database_url=SYNTHETIC_PG_URL,
            jwt_secret=short_secret,
        )
    err = str(exc_info.value)
    assert "JWT_SECRET is too short" in err
    assert "24 characters" in err
    # Confirm the secret itself is not leaked in the error message
    assert short_secret not in err


def test_production_strips_accidental_quotes_and_whitespace(monkeypatch):
    """Verify that accidental quotes or leading/trailing whitespace in cPanel inputs are sanitized."""
    monkeypatch.setenv("APP_ENV", "production")
    quoted_secret = f'  "{SYNTHETIC_TEST_SECRET}"  '
    s = Settings(
        app_env="production",
        database_url=SYNTHETIC_PG_URL,
        jwt_secret=quoted_secret,
    )
    assert s.jwt_secret == SYNTHETIC_TEST_SECRET
    assert len(s.jwt_secret) >= 32


def test_production_allows_secret_key_as_alias(monkeypatch):
    """Verify that SECRET_KEY is accepted as an alias when JWT_SECRET is unset."""
    monkeypatch.setenv("APP_ENV", "production")
    s = Settings(
        app_env="production",
        database_url=SYNTHETIC_PG_URL,
        jwt_secret="dev-only-secret-placeholder",
        secret_key=SYNTHETIC_TEST_SECRET,
    )
    assert s.jwt_secret == SYNTHETIC_TEST_SECRET


def test_production_rejects_sqlite_database_url(monkeypatch):
    """Verify that production rejects SQLite database URLs."""
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            app_env="production",
            database_url="sqlite:///./pgcb_portal.db",
            jwt_secret=SYNTHETIC_TEST_SECRET,
        )
    assert "DATABASE_URL cannot be SQLite" in str(exc_info.value)


def test_production_accepts_valid_postgresql_config(monkeypatch):
    """Verify that production succeeds with valid PostgreSQL and 32+ char secret."""
    monkeypatch.setenv("APP_ENV", "production")
    s = Settings(
        app_env="production",
        database_url=SYNTHETIC_PG_URL,
        jwt_secret=SYNTHETIC_TEST_SECRET,
    )
    assert s.app_env == "production"
    assert s.is_production_like
    assert s.database_url.startswith("postgresql+psycopg://")
