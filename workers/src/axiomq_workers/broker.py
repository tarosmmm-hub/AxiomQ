"""Dramatiq broker configuration.

Must be imported before any actor module so that actors bind to this broker.
"""

from __future__ import annotations

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker
from dramatiq.middleware import TimeLimit

from axiomq_api.core.config import Environment, get_settings

# Default hard limit per job; long-running actors (backtests) set their own ``time_limit``.
DEFAULT_TIME_LIMIT_MS = 10 * 60 * 1000


def build_broker() -> dramatiq.Broker:
    settings = get_settings()
    broker: dramatiq.Broker
    if settings.env is Environment.TEST:
        broker = StubBroker()
    else:
        broker = RedisBroker(url=settings.redis_url)  # type: ignore[no-untyped-call]
    for middleware in broker.middleware:
        if isinstance(middleware, TimeLimit):
            middleware.time_limit = DEFAULT_TIME_LIMIT_MS
    return broker


broker = build_broker()
dramatiq.set_broker(broker)
