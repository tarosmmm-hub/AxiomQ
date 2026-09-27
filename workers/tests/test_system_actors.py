from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def stub_worker():  # type: ignore[no-untyped-def]
    os.environ["AXIOMQ_ENV"] = "test"
    os.environ.setdefault(
        "AXIOMQ_DATABASE_URL",
        os.environ.get(
            "AXIOMQ_TEST_DATABASE_URL",
            "postgresql+psycopg://axiomq:axiomq@localhost:5432/axiomq_test",
        ),
    )
    os.environ.setdefault("AXIOMQ_RATE_LIMIT_BACKEND", "memory")
    from axiomq_api.core.config import get_settings

    get_settings.cache_clear()
    from dramatiq import Worker

    from axiomq_workers.actors import system
    from axiomq_workers.broker import broker

    worker = Worker(broker, worker_timeout=100)
    worker.start()
    yield broker, system
    worker.stop()


def test_ping_actor_runs_through_the_broker(stub_worker) -> None:  # type: ignore[no-untyped-def]
    broker, system = stub_worker
    system.ping.send("hello")
    broker.join(system.ping.queue_name, fail_fast=True)


def test_backend_queue_adapter_addresses_worker_actor_by_name(stub_worker) -> None:  # type: ignore[no-untyped-def]
    from axiomq_api.jobs.dramatiq_queue import DramatiqJobQueue
    from axiomq_api.jobs.ports import JobRequest, QueueName

    broker, _ = stub_worker
    queue = DramatiqJobQueue(broker)
    message_id = queue.enqueue(
        JobRequest(actor="ping", queue=QueueName.SYSTEM, kwargs={"echo": "from-api"})
    )
    assert message_id
    broker.join(QueueName.SYSTEM.value, fail_fast=True)


def test_adapter_rejects_non_serialisable_payload(stub_worker) -> None:  # type: ignore[no-untyped-def]
    from axiomq_api.jobs.dramatiq_queue import DramatiqJobQueue
    from axiomq_api.jobs.ports import JobRequest, QueueName

    broker, _ = stub_worker
    with pytest.raises(TypeError):
        DramatiqJobQueue(broker).enqueue(
            JobRequest(actor="ping", queue=QueueName.SYSTEM, kwargs={"x": object()})
        )
