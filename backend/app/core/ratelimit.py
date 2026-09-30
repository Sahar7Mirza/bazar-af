"""Tiny in-memory sliding-window limiter (single process). Use Redis or a gateway limit when scaling out."""

import time
from collections import defaultdict, deque
from threading import Lock

from app.core.errors import TooManyRequests


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit, self.window = limit, window_seconds
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.limit:
                raise TooManyRequests("Too many submissions. Please try again later.", code="rate_limited")
            q.append(now)

    def reset(self) -> None:
        with self.lock:
            self.hits.clear()


survey_limiter = RateLimiter(limit=10, window_seconds=3600)
