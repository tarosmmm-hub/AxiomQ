"""Engine/session factories and the request-scoped unit of work.

The API uses synchronous SQLAlchemy (psycopg 3) so that services and repositories are shared
verbatim with the (synchronous, CPU-bound) workers. FastAPI runs sync endpoints in a thread pool.

Handlers commit explicitly (``uow.commit(...)``) *before* returning, so a client never observes a
response for a write that is not yet durable. Side effects that must only happen after a
successful commit (emails) are deferred and scheduled as background tasks, which also keeps
response times independent of e.g. whether an account exists.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import BackgroundTasks
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def make_engine(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


class UnitOfWork:
    def __init__(self, session: Session) -> None:
        self.session = session
        self._deferred: list[Callable[[], None]] = []

    def defer(self, callback: Callable[[], None]) -> None:
        """Run ``callback`` only if (and after) the transaction commits."""
        self._deferred.append(callback)

    def commit(self, background: BackgroundTasks | None = None) -> None:
        self.session.commit()
        deferred, self._deferred = self._deferred, []
        for callback in deferred:
            if background is not None:
                background.add_task(callback)
            else:
                callback()

    def rollback(self) -> None:
        self._deferred.clear()
        self.session.rollback()
