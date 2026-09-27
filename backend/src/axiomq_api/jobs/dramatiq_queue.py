"""Dramatiq adapter for :class:`JobQueue`. The only backend module allowed to import Dramatiq.

Messages are addressed by actor *name* and queue, so the API never imports worker code.
"""

from __future__ import annotations

import json

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from axiomq_api.jobs.ports import JobRequest


class DramatiqJobQueue:
    def __init__(self, broker: dramatiq.Broker) -> None:
        self._broker = broker

    @classmethod
    def from_redis_url(cls, url: str) -> DramatiqJobQueue:
        return cls(RedisBroker(url=url))  # type: ignore[no-untyped-call]

    def enqueue(self, job: JobRequest) -> str:
        # Payloads must be JSON-serialisable primitives (ids, not ORM objects).
        json.dumps(job.kwargs)
        self._broker.declare_queue(job.queue.value)
        message: dramatiq.Message[None] = dramatiq.Message(
            queue_name=job.queue.value,
            actor_name=job.actor,
            args=(),
            kwargs=job.kwargs,
            options={},
        )
        return self._broker.enqueue(message).message_id
