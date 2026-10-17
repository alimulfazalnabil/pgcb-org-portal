from __future__ import annotations

import io
import sys
from pathlib import Path
import pytest


def test_passenger_wsgi_entrypoint_and_adapter():
    """Verify that passenger_wsgi exposes a valid WSGI callable wrapping FastAPI."""
    import deployment.hostseba.startup.passenger_wsgi as passenger_module
    from a2wsgi import ASGIMiddleware

    # 1. Entrypoint must export 'application'
    assert hasattr(passenger_module, "application")
    assert isinstance(passenger_module.application, ASGIMiddleware)

    # 2. Invoke WSGI application with mock environ
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/health",
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

    body_chunks = list(passenger_module.application(environ, start_response))
    body = b"".join(body_chunks).decode("utf-8")

    assert len(status_capture) == 1
    assert status_capture[0].startswith("200")
    assert "pgcb-api" in body or "ok" in body


def test_passenger_wsgi_fails_clearly_without_a2wsgi(monkeypatch):
    """Verify that importing without a2wsgi raises a clear RuntimeError rather than silent fallback."""
    import importlib
    import builtins

    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "a2wsgi":
            raise ImportError("No module named 'a2wsgi'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    # Unload module if previously loaded
    sys.modules.pop("deployment.hostseba.startup.passenger_wsgi", None)

    with pytest.raises(RuntimeError) as exc_info:
        import deployment.hostseba.startup.passenger_wsgi  # noqa: F401

    assert "Critical Deployment Error" in str(exc_info.value)
    assert "a2wsgi" in str(exc_info.value)
