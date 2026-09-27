from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text

from axiomq_api.core.clock import FrozenClock
from axiomq_api.core.config import EmailBackend, Environment, RateLimitBackend, Settings
from axiomq_api.core.container import Container, build_container
from axiomq_api.core.email import InMemoryEmailSender
from axiomq_api.core.middleware import CSRF_COOKIE, CSRF_HEADER
from axiomq_api.core.rate_limit import InMemoryRateLimiter
from axiomq_api.main import create_app

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DATABASE_URL = os.environ.get(
    "AXIOMQ_TEST_DATABASE_URL", "postgresql+psycopg://axiomq:axiomq@localhost:5432/axiomq_test"
)
# Reference data seeded by migrations; never truncated between tests.
REFERENCE_TABLES = {"alembic_version", "plans", "plan_entitlements"}


def run_alembic(url: str, *args: str) -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.attributes["configure_logger"] = False
    getattr(command, args[0])(cfg, *args[1:])


@pytest.fixture(scope="session")
def db_engine() -> Iterator[Engine]:
    engine = create_engine(TEST_DATABASE_URL)
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    except Exception as exc:  # pragma: no cover - environment guard
        pytest.skip(f"PostgreSQL not available for integration tests: {exc}")
    run_alembic(TEST_DATABASE_URL, "upgrade", "head")
    yield engine
    engine.dispose()


@pytest.fixture
def clean_db(db_engine: Engine) -> Iterator[Engine]:
    yield db_engine
    with db_engine.begin() as conn:
        tables = [
            row[0]
            for row in conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            if row[0] not in REFERENCE_TABLES
        ]
        if tables:
            conn.execute(text(f"TRUNCATE {', '.join(tables)} CASCADE"))


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "env": Environment.TEST,
        "database_url": TEST_DATABASE_URL,
        "secret_key": "test-secret-key-0123456789-abcdefghijklmnop",
        "cookie_secure": False,
        "argon2_time_cost": 1,
        "argon2_memory_cost_kib": 8,
        "argon2_parallelism": 1,
        "email_backend": EmailBackend.MEMORY,
        "rate_limit_backend": RateLimitBackend.MEMORY,
        "frontend_url": "http://app.test",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock(datetime(2026, 1, 5, 12, 0, tzinfo=UTC))


@pytest.fixture
def outbox() -> InMemoryEmailSender:
    return InMemoryEmailSender()


@pytest.fixture
def container(clean_db: Engine, clock: FrozenClock, outbox: InMemoryEmailSender) -> Container:
    return build_container(
        make_settings(), clock=clock, email_sender=outbox, rate_limiter=InMemoryRateLimiter(clock)
    )


class ApiClient(TestClient):
    """TestClient that performs the CSRF double-submit like the frontend does."""

    def csrf(self) -> str:
        token = self.cookies.get(CSRF_COOKIE)
        if token is None:
            token = self.get("/api/v1/auth/csrf").json()["csrf_token"]
        return token

    def request(self, method: str, url: str, **kwargs):  # type: ignore[no-untyped-def,override]
        if method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
            headers = dict(kwargs.pop("headers", None) or {})
            headers.setdefault(CSRF_HEADER, self.csrf())
            kwargs["headers"] = headers
        return super().request(method, url, **kwargs)


@pytest.fixture
def client(container: Container) -> Iterator[ApiClient]:
    with ApiClient(create_app(container=container)) as c:
        yield c


@pytest.fixture
def make_client(container: Container) -> Iterator[object]:
    """Factory for extra, independent browser-like clients (separate cookie jars)."""
    clients: list[ApiClient] = []

    def factory() -> ApiClient:
        c = ApiClient(create_app(container=container))
        c.__enter__()
        clients.append(c)
        return c

    yield factory
    for c in clients:
        c.__exit__(None, None, None)
