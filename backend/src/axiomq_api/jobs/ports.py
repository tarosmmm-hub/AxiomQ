"""Job queue port (ADR-0006).

Services enqueue work through this interface; only ``dramatiq_queue`` knows about Dramatiq.
Job *state* (queued/running/succeeded/failed) is persisted in PostgreSQL by the owning module
(e.g. ``backtests.status``); the queue is transport, not the source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol


class QueueName(StrEnum):
    """Separate queues so a burst of backtests cannot delay paper-trading ticks."""

    SYSTEM = "system"
    BACKTESTS = "backtests"
    PAPER_TICKS = "paper_ticks"
    DATA_IMPORTS = "data_imports"


@dataclass(frozen=True)
class JobRequest:
    actor: str
    queue: QueueName
    kwargs: dict[str, Any] = field(default_factory=dict)


class JobQueue(Protocol):
    def enqueue(self, job: JobRequest) -> str:
        """Enqueue and return the transport message id."""
        ...


class InMemoryJobQueue:
    """Test double: records jobs instead of sending them."""

    def __init__(self) -> None:
        self.jobs: list[JobRequest] = []

    def enqueue(self, job: JobRequest) -> str:
        self.jobs.append(job)
        return f"mem-{len(self.jobs)}"
