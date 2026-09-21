from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            response = None
            raise
        finally:
            if response is not None:
                status = str(response.status_code)
                elapsed = time.perf_counter() - started
                REQUEST_COUNT.labels(request.method, status).inc()
                REQUEST_LATENCY.labels(request.method, status).observe(elapsed)
                response.headers['X-Request-ID'] = request_id
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'DENY'
                response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
                response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
                response.headers['Content-Security-Policy'] = (
                    "default-src 'self'; img-src 'self' data: https:; "
                    "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                    "connect-src 'self' https:; frame-ancestors 'none'"
                )
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains' if request.url.scheme == 'https' else ''
                response.headers['Server-Timing'] = f"app;dur={elapsed*1000:.1f}"
            
        return response
