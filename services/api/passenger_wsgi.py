"""
HostSeba / CloudLinux Phusion Passenger Entrypoint for PGCB FastAPI Backend.
Located at: services/api/passenger_wsgi.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parent
if (API_DIR / "app" / "main.py").is_file():
    if str(API_DIR) not in sys.path:
        sys.path.insert(0, str(API_DIR))
else:
    # Fallback lookup if executed or symlinked elsewhere
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

os.environ.setdefault("APP_ENV", "production")

from app.main import app as asgi_app  # noqa: E402

try:
    from a2wsgi import ASGIMiddleware
except ImportError as exc:
    raise RuntimeError(
        "Critical Deployment Error: 'a2wsgi' is required to run the FastAPI ASGI "
        "application under Phusion Passenger WSGI. Ensure 'a2wsgi' is installed "
        "in your Python environment (pip install -r requirements.txt)."
    ) from exc

# Export standard WSGI callable for LiteSpeed / Phusion Passenger
application = ASGIMiddleware(asgi_app)
