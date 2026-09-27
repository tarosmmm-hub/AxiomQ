"""System actors (infrastructure checks)."""

from __future__ import annotations

import logging

import dramatiq
from sqlalchemy import text

from axiomq_api.core.config import get_settings
from axiomq_api.db.session import make_engine
from axiomq_api.jobs.ports import QueueName

logger = logging.getLogger(__name__)


@dramatiq.actor(queue_name=QueueName.SYSTEM.value, max_retries=0)
def ping(echo: str = "pong") -> None:
    """Round-trip check: the worker can consume jobs and reach the database."""
    engine = make_engine(get_settings().database_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    finally:
        engine.dispose()
    logger.info("worker_ping", extra={"echo": echo})
