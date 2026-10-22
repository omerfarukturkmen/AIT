"""In-memory sliding-window rate limiting.

State lives in this process only. Behind a reverse proxy, run uvicorn with
`--proxy-headers --forwarded-allow-ips=<proxy ip>` so `request.client.host`
is the real client address; with several worker processes, move the counters
to a shared store such as Redis.
"""

import threading
import time
from collections import deque

from fastapi import HTTPException, Request

TOO_MANY_REQUESTS = "Çok fazla istek gönderildi. Lütfen biraz sonra tekrar dene."


class RateLimitExceeded(HTTPException):
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=429,
            detail=TOO_MANY_REQUESTS,
            headers={"Retry-After": str(retry_after)},
        )


class RateLimiter:
    _registry: list["RateLimiter"] = []

    def __init__(self, name: str, max_requests: int, window_seconds: int):
        self.name = name
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()
        RateLimiter._registry.append(self)

    def check(self, key: str) -> None:
        """Records one request for `key`; raises RateLimitExceeded if over."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= now - self.window_seconds:
                hits.popleft()
            if len(hits) >= self.max_requests:
                retry_after = int(hits[0] + self.window_seconds - now) + 1
                raise RateLimitExceeded(retry_after)
            hits.append(now)

            if len(self._hits) > 10_000:
                for stale in [k for k, v in self._hits.items() if not v]:
                    del self._hits[stale]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    @classmethod
    def reset_all(cls) -> None:
        for limiter in cls._registry:
            limiter.reset()


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"
