"""
WSGI Entrypoint for LiteSpeed / Phusion Passenger.
Located at: services/api/wsgi.py
Provides explicit 'wsgi.py' discovery for LiteSpeed Web Server,
delegating directly to passenger_wsgi.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

_API_DIR = Path(__file__).resolve().parent
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

import passenger_wsgi  # noqa: E402

application = passenger_wsgi.application
