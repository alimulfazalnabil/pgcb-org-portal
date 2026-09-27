"""
HostSeba / CloudLinux Phusion Passenger Entrypoint for PGCB FastAPI Backend.
Located at: deployment/hostseba/startup/passenger_wsgi.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[3] / "services" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

os.environ.setdefault("APP_ENV", "production")

from app.main import app as asgi_app  # noqa: E402

try:
    from a2wsgi import ASGIMiddleware  # type: ignore
    application = ASGIMiddleware(asgi_app)
except ImportError:
    application = asgi_app
