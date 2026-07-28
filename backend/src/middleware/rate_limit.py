from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, max_requests: int = 30, window_seconds: float = 60.0) -> None:
        self._max_requests = max_requests
        self._window = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def _clean_bucket(self, key: str, now: float) -> None:
        cutoff = now - self._window
        self._buckets[key] = [ts for ts in self._buckets[key] if ts > cutoff]

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        self._clean_bucket(key, now)
        if len(self._buckets[key]) >= self._max_requests:
            return False
        self._buckets[key].append(now)
        return True


_webhook_limiter = RateLimiter(max_requests=60, window_seconds=60.0)
_auth_limiter = RateLimiter(max_requests=10, window_seconds=60.0)


def webhook_rate_limit(override_limiter: RateLimiter | None = None) -> Callable:
    limiter = override_limiter or _webhook_limiter

    async def dependency(request: Request) -> None:
        client_ip = _client_ip(request)
        if not limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please wait and try again.",
            )

    return dependency


def auth_rate_limit() -> Callable:
    """Rate limit for auth + dashboard endpoints."""

    async def dependency(request: Request) -> None:
        client_ip = _client_ip(request)
        if not _auth_limiter.is_allowed(client_ip):
            raise HTTPException(429, detail="Too many attempts. Wait and try again.")

    return dependency


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    client = request.client
    return client.host if client else "unknown"
