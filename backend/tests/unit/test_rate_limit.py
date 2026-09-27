from __future__ import annotations

from datetime import UTC, datetime, timedelta

from axiomq_api.core.clock import FrozenClock
from axiomq_api.core.rate_limit import InMemoryRateLimiter, RateLimitRule

RULE = RateLimitRule("test", limit=3, window_seconds=60)


def test_allows_up_to_limit_then_blocks_with_retry_after() -> None:
    clock = FrozenClock(datetime(2026, 1, 1, 0, 0, 10, tzinfo=UTC))
    limiter = InMemoryRateLimiter(clock)
    results = [limiter.hit(RULE, "k") for _ in range(4)]
    assert [r.allowed for r in results] == [True, True, True, False]
    assert results[-1].retry_after_seconds == 50


def test_window_resets() -> None:
    clock = FrozenClock(datetime(2026, 1, 1, tzinfo=UTC))
    limiter = InMemoryRateLimiter(clock)
    for _ in range(3):
        limiter.hit(RULE, "k")
    assert not limiter.hit(RULE, "k").allowed
    clock.advance(timedelta(seconds=60))
    assert limiter.hit(RULE, "k").allowed


def test_keys_and_rules_are_independent() -> None:
    clock = FrozenClock(datetime(2026, 1, 1, tzinfo=UTC))
    limiter = InMemoryRateLimiter(clock)
    for _ in range(3):
        limiter.hit(RULE, "a")
    assert limiter.hit(RULE, "b").allowed
    assert limiter.hit(RateLimitRule("other", 3, 60), "a").allowed
