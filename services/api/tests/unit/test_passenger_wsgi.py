from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

API_DIR = Path(__file__).resolve().parents[2]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

import pytest
from sqlalchemy.exc import OperationalError


@pytest.fixture(autouse=True)
def preserve_app_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    yield


def _invoke_wsgi(app_callable, path: str = "/health", method: str = "GET") -> tuple[str, list[tuple[str, str]], str]:
    """Helper to invoke a WSGI callable and capture status, headers, and body."""
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "SERVER_NAME": "127.0.0.1",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "http",
        "wsgi.input": io.BytesIO(b""),
        "wsgi.errors": sys.stderr,
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
    }

    status_capture: list[str] = []
    headers_capture: list[tuple[str, str]] = []

    def start_response(status, headers, exc_info=None):
        status_capture.append(status)
        headers_capture.extend(headers)

    body_chunks = list(app_callable(environ, start_response))
    body = b"".join(body_chunks).decode("utf-8")
    return status_capture[0] if status_capture else "", headers_capture, body


def test_passenger_wsgi_entrypoint_and_adapter():
    """Verify that passenger_wsgi exposes a valid WSGI callable wrapping FastAPI."""
    import passenger_wsgi
    from a2wsgi import ASGIMiddleware

    assert hasattr(passenger_wsgi, "application")
    assert isinstance(passenger_wsgi.application, ASGIMiddleware)


def test_deployment_startup_passenger_wsgi_delegation():
    """Verify that deployment/hostseba/startup/passenger_wsgi delegates to services/api/passenger_wsgi."""
    import deployment.hostseba.startup.passenger_wsgi as deployment_passenger
    from a2wsgi import ASGIMiddleware

    assert hasattr(deployment_passenger, "application")
    assert isinstance(deployment_passenger.application, ASGIMiddleware)


def test_passenger_wsgi_health_liveness():
    """Verify that /health returns HTTP 200 with service metadata."""
    import passenger_wsgi

    status, headers, body = _invoke_wsgi(passenger_wsgi.application, path="/health")
    assert status.startswith("200")
    data = json.loads(body)
    assert data.get("status") == "ok"
    assert data.get("service") == "pgcb-api"


def test_passenger_wsgi_health_succeeds_even_when_db_down(monkeypatch):
    """Verify that /health is a pure liveness probe that succeeds even if DB is unavailable."""
    import passenger_wsgi

    # Mock SessionLocal to raise an error if invoked
    mock_session = MagicMock()
    mock_session.side_effect = OperationalError("SELECT 1", {}, Exception("Database connection refused"))
    monkeypatch.setattr("app.main.SessionLocal", mock_session)

    status, headers, body = _invoke_wsgi(passenger_wsgi.application, path="/health")
    assert status.startswith("200")
    data = json.loads(body)
    assert data.get("status") == "ok"


def test_passenger_wsgi_ready_failure_on_db_down(monkeypatch):
    """Verify that /ready returns HTTP 503 when the database check fails."""
    import passenger_wsgi

    # Mock SessionLocal to raise OperationalError on execute
    mock_db = MagicMock()
    mock_db.execute.side_effect = OperationalError("SELECT 1", {}, Exception("Database server unreachable"))
    mock_session_factory = MagicMock(return_value=mock_db)
    monkeypatch.setattr("app.main.SessionLocal", mock_session_factory)

    status, headers, body = _invoke_wsgi(passenger_wsgi.application, path="/ready")
    assert status.startswith("503")
    data = json.loads(body)
    assert data.get("status") == "not_ready"
    assert data.get("database") == "error"


def test_mask_sensitive_data():
    """Verify credential masking in error messages and stack traces."""
    from services.api.passenger_wsgi import mask_sensitive_data

    # PostgreSQL / MySQL URL with credentials
    url_text = "Failed connecting to postgresql://powergri_user:SuperSecretP@ss123@127.0.0.1:5432/powergri_portal"
    masked_url = mask_sensitive_data(url_text)
    assert "SuperSecretP@ss123" not in masked_url
    assert "postgresql://powergri_user:***@127.0.0.1:5432/powergri_portal" in masked_url

    # Key=Value and Key: Value secrets
    kv_text = "jwt_secret=myjwtkey123 password='mypassword' smtp_pass: smtppass456 token=abcdef"
    masked_kv = mask_sensitive_data(kv_text)
    assert "myjwtkey123" not in masked_kv
    assert "mypassword" not in masked_kv
    assert "smtppass456" not in masked_kv
    assert "abcdef" not in masked_kv
    assert "jwt_secret=***" in masked_kv
    assert "token=***" in masked_kv


def test_create_fallback_application_diagnostic():
    """Verify that create_fallback_application returns a safe 500 JSON response with masked details."""
    from services.api.passenger_wsgi import create_fallback_application

    simulated_exc = RuntimeError(
        "DB connection failed at postgresql://powergri_user:topsecret999@localhost:5432/db with jwt_secret=shhh"
    )
    fallback_app = create_fallback_application(simulated_exc)

    status, headers, body = _invoke_wsgi(fallback_app, path="/health")
    assert status.startswith("500")

    header_dict = dict(headers)
    assert header_dict.get("Content-Type") == "application/json; charset=utf-8"
    assert header_dict.get("X-Content-Type-Options") == "nosniff"

    data = json.loads(body)
    assert data.get("status") == "error"
    assert data.get("service") == "pgcb-api"
    assert data.get("error") == "FastAPI Application Startup Failure"

    detail = data.get("detail", "")
    assert "topsecret999" not in detail
    assert "shhh" not in detail
    assert "***" in detail


def test_passenger_wsgi_startup_fallback_when_a2wsgi_missing(monkeypatch):
    """Verify that if a2wsgi fails to import, passenger_wsgi sets application to fallback."""
    import builtins

    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "a2wsgi":
            raise ImportError("No module named 'a2wsgi'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    # Unload passenger_wsgi and re-import under mock
    sys.modules.pop("passenger_wsgi", None)
    import passenger_wsgi

    status, headers, body = _invoke_wsgi(passenger_wsgi.application, path="/health")
    assert status.startswith("500")
    data = json.loads(body)
    assert data.get("status") == "error"
    assert "a2wsgi" in data.get("detail", "")

    # Cleanup sys.modules to restore state
    sys.modules.pop("passenger_wsgi", None)
