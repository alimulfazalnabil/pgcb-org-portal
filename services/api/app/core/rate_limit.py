from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request

from app.core.config import settings

try:
    from redis import Redis
except Exception:  # pragma: no cover
    Redis = None  # type: ignore


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        now = monotonic()
        with self._lock:
            bucket = self._hits[key]
            cutoff = now - window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                raise HTTPException(429, 'Too many requests. Please try again later.')
            bucket.append(now)


class RateLimiter:
    def __init__(self) -> None:
        self.local = InMemoryRateLimiter()
        self._redis = None
        self._redis_failed = False

    def _client(self):
        if self._redis_failed or not settings.redis_rate_limit_enabled or Redis is None:
            return None
        if self._redis is None:
            try:
                self._redis = Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=0.15, socket_timeout=0.15)
                self._redis.ping()
            except Exception:
                self._redis = None
                self._redis_failed = True
        return self._redis

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        client = self._client()
        if client is None:
            self.local.check(key, limit, window_seconds)
            return
        try:
            count = int(client.incr(key))
            if count == 1:
                client.expire(key, window_seconds)
            if count > limit:
                raise HTTPException(429, 'Too many requests. Please try again later.')
        except HTTPException:
            raise
        except Exception:
            # Keep the API available if Redis is temporarily unavailable.
            self._redis_failed = True
            self.local.check(key, limit, window_seconds)


limiter = RateLimiter()

def client_key(request: Request, scope: str) -> str:
    host = request.client.host if request.client else 'unknown'
    return f'{scope}:{host}'
