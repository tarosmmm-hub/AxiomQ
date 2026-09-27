"""FastAPI dependencies shared by all modules."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from axiomq_api.core.container import Container
from axiomq_api.core.errors import RateLimited
from axiomq_api.core.rate_limit import RateLimitRule
from axiomq_api.db.session import UnitOfWork


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_uow(container: ContainerDep) -> Iterator[UnitOfWork]:
    session = container.session_factory()
    uow = UnitOfWork(session)
    try:
        yield uow
    finally:
        # Anything not explicitly committed by the handler is discarded.
        uow.rollback()
        session.close()


UowDep = Annotated[UnitOfWork, Depends(get_uow)]


@dataclass(frozen=True)
class RequestMeta:
    ip: str | None
    user_agent: str | None


def get_request_meta(request: Request, container: ContainerDep) -> RequestMeta:
    ip = request.client.host if request.client else None
    hops = container.settings.trusted_proxy_hops
    if hops:
        forwarded = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",")]
        forwarded = [p for p in forwarded if p]
        if len(forwarded) >= hops:
            ip = forwarded[-hops]
    user_agent = request.headers.get("user-agent")
    return RequestMeta(ip=ip, user_agent=user_agent[:256] if user_agent else None)


RequestMetaDep = Annotated[RequestMeta, Depends(get_request_meta)]


def enforce_rate_limit(container: Container, rule: RateLimitRule, key: str) -> None:
    result = container.rate_limiter.hit(rule, key)
    if not result.allowed:
        raise RateLimited(result.retry_after_seconds)
