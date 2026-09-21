from __future__ import annotations

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter(
    'pgcb_http_requests_total',
    'Total HTTP requests handled by the API.',
    ['method', 'status'],
)
REQUEST_LATENCY = Histogram(
    'pgcb_http_request_duration_seconds',
    'HTTP request duration in seconds.',
    ['method', 'status'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
