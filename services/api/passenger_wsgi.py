"""
HostSeba / CloudLinux Phusion Passenger Entrypoint for PGCB FastAPI Backend.
Located at: services/api/passenger_wsgi.py

Exposes the WSGI `application` callable expected by Phusion Passenger / LiteSpeed,
adapting FastAPI's ASGI app via a2wsgi with robust startup error logging and credential masking.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import traceback
from pathlib import Path

# 1. Ensure services/api is on sys.path
API_DIR = Path(__file__).resolve().parent
if (API_DIR / "app" / "main.py").is_file():
    if str(API_DIR) not in sys.path:
        sys.path.insert(0, str(API_DIR))
else:
    for candidate in (
        Path(__file__).resolve().parents[0],
        Path(__file__).resolve().parents[1] / "services" / "api",
        Path(__file__).resolve().parents[2] / "services" / "api",
    ):
        if (candidate / "app" / "main.py").is_file():
            API_DIR = candidate
            if str(API_DIR) not in sys.path:
                sys.path.insert(0, str(API_DIR))
            break

# 2. Auto-detect and activate virtualenv if not already active
_VENV_CANDIDATES = [
    API_DIR / ".venv",
    API_DIR.parent.parent / ".venv",
    Path("/home/powergri/virtualenv/repositories/pgcb-org-portal/services/api/3.11"),
    Path.home() / "virtualenv" / "repositories" / "pgcb-org-portal" / "services" / "api" / "3.11",
    Path.home() / "virtualenv" / "services" / "api" / "3.11",
]
for venv_path in _VENV_CANDIDATES:
    site_packages = list(venv_path.glob("lib/python*/site-packages"))
    if site_packages and str(site_packages[0]) not in sys.path:
        sys.path.insert(0, str(site_packages[0]))
        break

os.environ.setdefault("APP_ENV", "production")


def mask_sensitive_data(text: str) -> str:
    """Mask passwords, tokens, and secret strings from diagnostic messages."""
    if not text:
        return ""

    def _mask_db_url(m: re.Match) -> str:
        user = m.group(1)
        host = m.group(3)
        port = m.group(4) or ""
        path = m.group(5) or ""
        return f"://{user}:***@{host}{port}{path}"

    # Mask database passwords: match ://user:password@host[:port][/path]
    text = re.sub(
        r"://([^\s/:@]+):(\S+)@([a-zA-Z0-9_.-]+|\[[a-fA-F0-9:]+\])(:\d+)?(/?[^\s]*)",
        _mask_db_url,
        text,
    )
    # Also mask any fallback pattern ://user:pass@
    text = re.sub(r"://([^/\s:]+):([^/\s@]+)@", r"://\1:***@", text)

    # Mask key=value and key: value secrets
    text = re.sub(
        r"(jwt_secret|secret_key|password|db_password|smtp_pass|smtp_password|api_key|token|access_token|refresh_token)\s*([=:])\s*([\"']?)([^\"'\s&,]+)\3",
        r"\1\2***",
        text,
        flags=re.IGNORECASE,
    )
    return text


def _log_startup_error(exc: Exception) -> str:
    """Log startup exceptions to stderr and local passenger_startup.log with credentials masked."""
    raw_tb = traceback.format_exc()
    masked_tb = mask_sensitive_data(raw_tb)
    error_msg = f"[PASSENGER STARTUP ERROR] Failed to initialize FastAPI backend:\n{masked_tb}\n"
    sys.stderr.write(error_msg)
    sys.stderr.flush()

    try:
        log_file = API_DIR / "passenger_startup.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"--- Startup Error at {os.environ.get('APP_ENV', 'unknown')} ---\n")
            f.write(error_msg)
            f.write("\n")
    except Exception:
        pass
    return masked_tb


def create_fallback_application(exc: Exception):
    """Create an emergency WSGI callable returning a safe diagnostic 500 response."""
    def _fallback_application(environ, start_response):
        status = "500 Internal Server Error"
        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("X-Content-Type-Options", "nosniff"),
        ]
        start_response(status, headers)
        payload = {
            "status": "error",
            "service": "pgcb-api",
            "error": "FastAPI Application Startup Failure",
            "detail": mask_sensitive_data(str(exc)),
            "hint": "Check passenger_startup.log in services/api for the masked traceback.",
        }
        body = json.dumps(payload, ensure_ascii=False)
        return [body.encode("utf-8")]

    return _fallback_application


# 3. Attempt application initialization with graceful WSGI fallback on error
application = None
_startup_error_detail: str | None = None

try:
    from app.main import app as asgi_app

    try:
        from a2wsgi import ASGIMiddleware
    except ImportError as exc:
        raise RuntimeError(
            "Critical Deployment Error: 'a2wsgi' is required to run FastAPI under "
            "Phusion Passenger WSGI. Ensure 'a2wsgi' is installed in your Python environment "
            "(pip install -r requirements.txt)."
        ) from exc

    application = ASGIMiddleware(asgi_app)

except Exception as startup_exc:
    _startup_error_detail = _log_startup_error(startup_exc)
    application = create_fallback_application(startup_exc)
