from __future__ import annotations

import os
import uuid

import pytest
import redis

from axiomq_api.core.rate_limit import RateLimitRule, RedisRateLimiter

pytestmark = pytest.mark.integration


@pytest.fixture
def redis_client() -> redis.Redis:
    client = redis.Redis.from_url(
        os.environ.get("AXIOMQ_TEST_REDIS_URL", "redis://localhost:6379/15")
    )
    try:
        client.ping()
    except redis.ConnectionError:
        pytest.skip("Redis not available")
    return client


def test_redis_limiter_blocks_after_limit_and_sets_ttl(redis_client: redis.Redis) -> None:
    limiter = RedisRateLimiter(redis_client)
    rule = RateLimitRule(f"test-{uuid.uuid4().hex}", limit=2, window_seconds=30)
    results = [limiter.hit(rule, "ip-1") for _ in range(3)]
    assert [r.allowed for r in results] == [True, True, False]
    assert 0 < results[-1].retry_after_seconds <= 30
    assert limiter.hit(rule, "ip-2").allowed
    ttl = redis_client.ttl(f"axiomq:ratelimit:{rule.name}:ip-1")
    assert 0 < ttl <= 30  # the window is not extended by later hits
