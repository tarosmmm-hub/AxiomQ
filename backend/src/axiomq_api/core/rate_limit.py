"""Fixed-window rate limiting.

Redis is the production backend (shared across API replicas). The in-memory backend exists for
unit tests and single-process development only; production settings refuse it.
"""

from __future__ import annotations

import math
import threading
from dataclasses import dataclass
from typing import Protocol

import redis

from axiomq_api.core.clock import Clock


@dataclass(frozen=True)
class RateLimitRule:
    name: str
    limit: int
    window_seconds: int


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int


class RateLimiter(Protocol):
    def hit(self, rule: RateLimitRule, key: str) -> RateLimitResult: ...


class InMemoryRateLimiter:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        self._windows: dict[str, tuple[int, int]] = {}

    def hit(self, rule: RateLimitRule, key: str) -> RateLimitResult:
        now = self._clock.now().timestamp()
        window = int(now // rule.window_seconds)
        bucket = f"{rule.name}:{key}"
        with self._lock:
            current_window, count = self._windows.get(bucket, (window, 0))
            if current_window != window:
                count = 0
            count += 1
            self._windows[bucket] = (window, count)
        retry_after = math.ceil((window + 1) * rule.window_seconds - now)
        return RateLimitResult(allowed=count <= rule.limit, retry_after_seconds=max(retry_after, 1))


class RedisRateLimiter:
    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    def hit(self, rule: RateLimitRule, key: str) -> RateLimitResult:
        bucket = f"axiomq:ratelimit:{rule.name}:{key}"
        pipe = self._client.pipeline(transaction=True)
        pipe.incr(bucket)
        pipe.expire(bucket, rule.window_seconds, nx=True)
        pipe.ttl(bucket)
        count, _, ttl = pipe.execute()
        retry_after = int(ttl) if int(ttl) > 0 else rule.window_seconds
        return RateLimitResult(allowed=int(count) <= rule.limit, retry_after_seconds=retry_after)


# Central catalogue of rules so that limits are reviewed in one place.
LOGIN_PER_IP = RateLimitRule("login_ip", limit=30, window_seconds=15 * 60)
LOGIN_PER_EMAIL = RateLimitRule("login_email", limit=10, window_seconds=15 * 60)
REGISTER_PER_IP = RateLimitRule("register_ip", limit=10, window_seconds=60 * 60)
RESET_PER_IP = RateLimitRule("reset_ip", limit=10, window_seconds=60 * 60)
RESET_PER_EMAIL = RateLimitRule("reset_email", limit=3, window_seconds=60 * 60)
VERIFY_RESEND_PER_USER = RateLimitRule("verify_resend_user", limit=3, window_seconds=60 * 60)
