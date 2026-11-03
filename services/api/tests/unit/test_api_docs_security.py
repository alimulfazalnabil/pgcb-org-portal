from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.core.config import Settings


def create_test_app(settings: Settings) -> FastAPI:
    """Helper mirroring the exact documentation initialization logic in app/main.py."""
    _is_prod_like = settings.is_production_like
    _docs_enabled = False if _is_prod_like else getattr(settings, "docs_enabled", True)

    return FastAPI(
        title="PGCB Organization Portal API (Test)",
        docs_url="/docs" if _docs_enabled else None,
        redoc_url="/redoc" if _docs_enabled else None,
        openapi_url="/openapi.json" if _docs_enabled else None,
    )


def test_api_docs_available_in_development():
    """Verify that /docs, /redoc, and /openapi.json are accessible in development."""
    settings = Settings(app_env="development")
    assert not settings.is_production_like
    assert settings.docs_enabled is True

    app = create_test_app(settings)
    client = TestClient(app)

    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_api_docs_available_in_testing():
    """Verify that /docs, /redoc, and /openapi.json are accessible in testing."""
    settings = Settings(app_env="testing")
    assert not settings.is_production_like
    assert settings.docs_enabled is True

    app = create_test_app(settings)
    client = TestClient(app)

    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_api_docs_disabled_in_production_by_default():
    """Verify that production unconditionally disables docs by default (404)."""
    settings = Settings(
        app_env="production",
        jwt_secret="c" * 64,
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
    )
    assert settings.is_production_like
    assert settings.docs_enabled is False

    app = create_test_app(settings)
    client = TestClient(app)

    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_api_docs_disabled_in_production_even_when_docs_enabled_is_true():
    """Verify that DOCS_ENABLED=true CANNOT override the production lockout."""
    settings = Settings(
        app_env="production",
        jwt_secret="d" * 64,
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
        docs_enabled=True,
    )
    assert settings.is_production_like
    # settings.docs_enabled must be forced to False by validate_production
    assert settings.docs_enabled is False

    app = create_test_app(settings)
    client = TestClient(app)

    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_api_docs_disabled_in_staging_by_default():
    """Verify that staging unconditionally disables docs by default (404)."""
    settings = Settings(
        app_env="staging",
        jwt_secret="e" * 64,
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
    )
    assert settings.is_production_like
    assert settings.docs_enabled is False

    app = create_test_app(settings)
    client = TestClient(app)

    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_api_docs_disabled_in_staging_even_when_docs_enabled_is_true():
    """Verify that DOCS_ENABLED=true CANNOT override the staging lockout."""
    settings = Settings(
        app_env="staging",
        jwt_secret="f" * 64,
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
        docs_enabled=True,
    )
    assert settings.is_production_like
    assert settings.docs_enabled is False

    app = create_test_app(settings)
    client = TestClient(app)

    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404
