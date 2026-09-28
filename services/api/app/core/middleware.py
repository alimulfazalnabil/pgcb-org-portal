from __future__ import annotations

from collections import deque
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.cache import is_never_cached_path, is_selectively_cached_path, portal_cache
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY


class ObservabilityTracker:
    def __init__(self) -> None:
        self.total_requests: int = 0
        self.http_errors_4xx: int = 0
        self.http_errors_5xx: int = 0
        self.slow_requests_count: int = 0
        self.latencies_ms: deque[float] = deque(maxlen=1000)
        self.recent_errors: deque[dict] = deque(maxlen=100)

    def record(self, method: str, path: str, status_code: int, elapsed_ms: float) -> None:
        self.total_requests += 1
        self.latencies_ms.append(elapsed_ms)
        if 400 <= status_code < 500:
            self.http_errors_4xx += 1
        elif status_code >= 500:
            self.http_errors_5xx += 1
        if elapsed_ms > 500.0:
            self.slow_requests_count += 1

    def record_error_id(self, error_id: str, method: str, path: str, exc_type: str) -> None:
        self.recent_errors.appendleft(
            {
                'error_id': error_id,
                'method': method,
                'path': path,
                'type': exc_type,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            }
        )

    def summary(self) -> dict:
        samples = list(self.latencies_ms)
        avg_ms = round(sum(samples) / len(samples), 2) if samples else 0.0
        sorted_samples = sorted(samples)
        p95_idx = min(len(sorted_samples) - 1, int(len(sorted_samples) * 0.95)) if sorted_samples else 0
        p95_ms = round(sorted_samples[p95_idx], 2) if sorted_samples else 0.0
        return {
            'total_requests': self.total_requests,
            'http_errors_4xx': self.http_errors_4xx,
            'http_errors_5xx': self.http_errors_5xx,
            'slow_requests_count': self.slow_requests_count,
            'avg_latency_ms': avg_ms,
            'p95_latency_ms': p95_ms,
            'recent_errors': list(self.recent_errors)[:20],
        }


observability_tracker = ObservabilityTracker()


def _apply_security_headers(response: Response, request: Request, request_id: str, elapsed: float) -> None:
    response.headers['X-Request-ID'] = request_id
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "connect-src 'self' https:; frame-ancestors 'none'"
    )
    response.headers['Strict-Transport-Security'] = (
        'max-age=31536000; includeSubDomains' if request.url.scheme == 'https' else ''
    )
    response.headers['Server-Timing'] = f'app;dur={elapsed * 1000:.1f}'


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        path = request.url.path
        method = request.method.upper()

        # Selective Cache lookup for public GET routes
        cache_key = None
        if method == 'GET' and is_selectively_cached_path(path):
            query_str = request.url.query
            cache_key = f'{path}?{query_str}' if query_str else path
            hit, cached_payload = portal_cache.get(cache_key)
            if hit and cached_payload is not None:
                body_bytes, status_code, media_type = cached_payload
                elapsed = time.perf_counter() - started
                cached_resp = Response(content=body_bytes, status_code=status_code, media_type=media_type)
                cached_resp.headers['X-Cache'] = 'HIT'
                cached_resp.headers['Cache-Control'] = 'public, max-age=120, stale-while-revalidate=60'
                _apply_security_headers(cached_resp, request, request_id, elapsed)
                REQUEST_COUNT.labels(method, str(status_code)).inc()
                REQUEST_LATENCY.labels(method, str(status_code)).observe(elapsed)
                observability_tracker.record(method, path, status_code, elapsed * 1000.0)
                return cached_resp

        try:
            response = await call_next(request)
        except Exception:
            response = None
            raise

        elapsed = time.perf_counter() - started
        elapsed_ms = elapsed * 1000.0
        status_code = response.status_code
        status_str = str(status_code)

        REQUEST_COUNT.labels(method, status_str).inc()
        REQUEST_LATENCY.labels(method, status_str).observe(elapsed)
        observability_tracker.record(method, path, status_code, elapsed_ms)

        if is_never_cached_path(path):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
            response.headers['X-Cache'] = 'BYPASS'
        elif cache_key and status_code == 200:
            body_chunks = [chunk async for chunk in response.body_iterator]
            full_body = b''.join(body_chunks)
            media_type = response.media_type or response.headers.get('content-type', 'application/json')
            portal_cache.set(cache_key, (full_body, status_code, media_type))
            new_resp = Response(
                content=full_body,
                status_code=status_code,
                headers=dict(response.headers),
                media_type=media_type,
            )
            new_resp.headers['X-Cache'] = 'MISS'
            new_resp.headers['Cache-Control'] = 'public, max-age=120, stale-while-revalidate=60'
            _apply_security_headers(new_resp, request, request_id, elapsed)
            return new_resp

        # Invalidate public cache on successful admin/CMS state mutations
        if method in ('POST', 'PUT', 'PATCH', 'DELETE') and 200 <= status_code < 300:
            if any(
                seg in path
                for seg in (
                    '/notices',
                    '/news',
                    '/events',
                    '/circles',
                    '/committee',
                    '/settings',
                    '/homepage-config',
                    '/workflows',
                    '/faqs',
                )
            ):
                portal_cache.invalidate_prefix('')

        _apply_security_headers(response, request, request_id, elapsed)
        return response
