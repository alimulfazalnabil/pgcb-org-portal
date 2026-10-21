"""
HostSeba / CloudLinux Phusion Passenger Entrypoint for PGCB FastAPI Backend.
Located at: deployment/hostseba/startup/passenger_wsgi.py
Delegates to services/api/passenger_wsgi.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_API_DIR = Path(__file__).resolve().parents[3] / "services" / "api"
if not (_API_DIR / "passenger_wsgi.py").is_file():
    for candidate in (
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parents[1] / "services" / "api",
        Path(__file__).resolve().parents[2] / "services" / "api",
    ):
        if (candidate / "passenger_wsgi.py").is_file():
            _API_DIR = candidate
            break

if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

import passenger_wsgi  # noqa: E402

application = passenger_wsgi.application
