from __future__ import annotations

from collections import defaultdict
from threading import Lock

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST  # type: ignore

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

except Exception:  # pragma: no cover - lightweight native fallback for HostSeba
    _lock = Lock()
    _counts: dict[tuple[str, str], int] = defaultdict(int)
    _latency_sum: dict[tuple[str, str], float] = defaultdict(float)

    class _LabelProxy:
        def __init__(self, method: str, status: str) -> None:
            self.key = (str(method), str(status))

        def inc(self, amount: int = 1) -> None:
            with _lock:
                _counts[self.key] += amount

        def observe(self, value: float) -> None:
            with _lock:
                _latency_sum[self.key] += float(value)

    class _MetricStub:
        def labels(self, method: str, status: str) -> _LabelProxy:
            return _LabelProxy(method, status)

    REQUEST_COUNT = _MetricStub()
    REQUEST_LATENCY = _MetricStub()

    def render_metrics() -> tuple[bytes, str]:
        lines = [
            '# HELP pgcb_http_requests_total Total HTTP requests handled by the API.',
            '# TYPE pgcb_http_requests_total counter',
        ]
        with _lock:
            for (method, status), count in sorted(_counts.items()):
                lines.append(f'pgcb_http_requests_total{{method="{method}",status="{status}"}} {count}')
            lines.append('# HELP pgcb_http_request_duration_seconds_sum HTTP request duration sum in seconds.')
            lines.append('# TYPE pgcb_http_request_duration_seconds_sum counter')
            for (method, status), total_sec in sorted(_latency_sum.items()):
                lines.append(f'pgcb_http_request_duration_seconds_sum{{method="{method}",status="{status}"}} {total_sec:.6f}')
        body = ('\n'.join(lines) + '\n').encode('utf-8')
        return body, 'text/plain; version=0.0.4; charset=utf-8'

