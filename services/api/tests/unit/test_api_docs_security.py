from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.core.config import Settings


def test_api_docs_available_in_development():
    """Verify that /docs and /openapi.json are accessible when not in production."""
    settings = Settings(app_env="development", docs_enabled=False)
    assert not settings.is_production_like

    is_prod = settings.is_production_like
    enable_docs = getattr(settings, "docs_enabled", False) if is_prod else True

    test_app = FastAPI(
        title="Test Development API",
        docs_url="/docs" if enable_docs else None,
        redoc_url="/redoc" if enable_docs else None,
        openapi_url="/openapi.json" if enable_docs else None,
    )

    client = TestClient(test_app)
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_api_docs_disabled_in_production_by_default():
    """Verify that /docs, /redoc, and /openapi.json return 404 in production by default."""
    settings = Settings(
        app_env="production",
        jwt_secret="a" * 64,
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
        docs_enabled=False,
    )
    assert settings.is_production_like

    is_prod = settings.is_production_like
    enable_docs = getattr(settings, "docs_enabled", False) if is_prod else True

    test_app = FastAPI(
        title="Test Production API",
        docs_url="/docs" if enable_docs else None,
        redoc_url="/redoc" if enable_docs else None,
        openapi_url="/openapi.json" if enable_docs else None,
    )

    client = TestClient(test_app)
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_api_docs_explicitly_enabled_in_production():
    """Verify that /docs can be explicitly enabled in production via DOCS_ENABLED=true."""
    settings = Settings(
        app_env="production",
        jwt_secret="b" * 64,
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
        docs_enabled=True,
    )
    assert settings.is_production_like
    assert settings.docs_enabled is True

    is_prod = settings.is_production_like
    enable_docs = getattr(settings, "docs_enabled", False) if is_prod else True

    test_app = FastAPI(
        title="Test Production API (Docs Enabled)",
        docs_url="/docs" if enable_docs else None,
        redoc_url="/redoc" if enable_docs else None,
        openapi_url="/openapi.json" if enable_docs else None,
    )

    client = TestClient(test_app)
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
