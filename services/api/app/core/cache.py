from __future__ import annotations

import time
from threading import Lock
from typing import Any


NEVER_CACHE_PREFIXES = (
    '/api/v1/payments',
    '/api/v1/payment-webhooks',
    '/api/v1/member',
    '/api/v1/membership',
    '/api/v1/admin',
    '/api/v1/auth',
    '/api/v1/card',
    '/api/v1/workflows',
)

SELECTIVE_CACHE_PREFIXES = (
    '/api/v1/public/notices',
    '/api/v1/notices',
    '/api/v1/public/news',
    '/api/v1/public/events',
    '/api/v1/events',
    '/api/v1/public/settings',
    '/api/v1/public/circles',
    '/api/v1/public/organization-hierarchy',
    '/api/v1/public/homepage-config',
    '/api/v1/public/committee',
    '/api/v1/public/faqs',
)


def is_never_cached_path(path: str) -> bool:
    clean = (path or '').rstrip('/') or '/'
    return any(clean.startswith(prefix) for prefix in NEVER_CACHE_PREFIXES)


def is_selectively_cached_path(path: str) -> bool:
    clean = (path or '').rstrip('/') or '/'
    if is_never_cached_path(clean):
        return False
    return any(clean.startswith(prefix) for prefix in SELECTIVE_CACHE_PREFIXES)


class SelectiveTTLCache:
    """Thread-safe in-memory TTL cache for public read-heavy institutional endpoints."""

    def __init__(self, default_ttl_seconds: int = 120, max_entries: int = 512) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl_seconds
        self.max_entries = max_entries
        self.hits = 0
        self.misses = 0
        self.invalidations = 0

    def get(self, key: str) -> tuple[bool, Any]:
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self.misses += 1
                return False, None
            expires_at, value = entry
            if now >= expires_at:
                del self._store[key]
                self.misses += 1
                return False, None
            self.hits += 1
            return True, value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expires_at = time.monotonic() + max(1, ttl)
        with self._lock:
            if len(self._store) >= self.max_entries and key not in self._store:
                oldest_key = min(self._store.items(), key=lambda item: item[1][0])[0]
                del self._store[oldest_key]
            self._store[key] = (expires_at, value)

    def invalidate_prefix(self, prefix: str = '') -> int:
        removed = 0
        with self._lock:
            if not prefix:
                removed = len(self._store)
                self._store.clear()
            else:
                keys = [k for k in self._store if k.startswith(prefix)]
                for k in keys:
                    del self._store[k]
                    removed += 1
            self.invalidations += removed
        return removed

    def stats(self) -> dict[str, Any]:
        with self._lock:
            total = self.hits + self.misses
            hit_rate = round(self.hits / total, 4) if total > 0 else 0.0
            return {
                'entries': len(self._store),
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'invalidations': self.invalidations,
                'default_ttl_seconds': self.default_ttl,
                'cached_scopes': [
                    'public_notices',
                    'published_news',
                    'events',
                    'organization_info',
                    'public_committee',
                ],
                'never_cached_scopes': [
                    'payment_status',
                    'membership_status',
                    'admin_actions',
                    'personal_information',
                ],
            }


portal_cache = SelectiveTTLCache(default_ttl_seconds=120, max_entries=512)
