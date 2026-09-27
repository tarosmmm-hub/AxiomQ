"""Composition root: builds long-lived services from settings. Tests build their own."""

from __future__ import annotations

from dataclasses import dataclass

import redis
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from axiomq_api.core.clock import Clock, SystemClock
from axiomq_api.core.config import EmailBackend, RateLimitBackend, Settings
from axiomq_api.core.email import (
    ConsoleEmailSender,
    EmailSender,
    InMemoryEmailSender,
    SmtpEmailSender,
)
from axiomq_api.core.rate_limit import InMemoryRateLimiter, RateLimiter, RedisRateLimiter
from axiomq_api.core.security import PasswordHashing
from axiomq_api.db.session import make_engine, make_session_factory


@dataclass
class Container:
    settings: Settings
    clock: Clock
    engine: Engine
    session_factory: sessionmaker[Session]
    passwords: PasswordHashing
    rate_limiter: RateLimiter
    email_sender: EmailSender
    redis: redis.Redis | None

    @property
    def secret(self) -> str:
        return self.settings.secret_key.get_secret_value()


def _email_sender(settings: Settings) -> EmailSender:
    if settings.email_backend is EmailBackend.SMTP:
        return SmtpEmailSender(
            host=settings.smtp_host,
            port=settings.smtp_port,
            sender=settings.email_from,
            username=settings.smtp_username,
            password=settings.smtp_password.get_secret_value() if settings.smtp_password else None,
            starttls=settings.smtp_starttls,
        )
    if settings.email_backend is EmailBackend.MEMORY:
        return InMemoryEmailSender()
    return ConsoleEmailSender()


def build_container(
    settings: Settings,
    *,
    clock: Clock | None = None,
    email_sender: EmailSender | None = None,
    rate_limiter: RateLimiter | None = None,
) -> Container:
    clock = clock or SystemClock()
    engine = make_engine(settings.database_url)
    redis_client: redis.Redis | None = None
    if rate_limiter is None:
        if settings.rate_limit_backend is RateLimitBackend.REDIS:
            redis_client = redis.Redis.from_url(settings.redis_url)
            rate_limiter = RedisRateLimiter(redis_client)
        else:
            rate_limiter = InMemoryRateLimiter(clock)
    return Container(
        settings=settings,
        clock=clock,
        engine=engine,
        session_factory=make_session_factory(engine),
        passwords=PasswordHashing(
            time_cost=settings.argon2_time_cost,
            memory_cost_kib=settings.argon2_memory_cost_kib,
            parallelism=settings.argon2_parallelism,
        ),
        rate_limiter=rate_limiter,
        email_sender=email_sender or _email_sender(settings),
        redis=redis_client,
    )
