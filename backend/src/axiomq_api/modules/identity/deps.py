from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from axiomq_api.core.deps import ContainerDep, RequestMetaDep, UowDep
from axiomq_api.core.errors import NotAuthenticated
from axiomq_api.modules.identity.cookies import SESSION_COOKIE
from axiomq_api.modules.identity.models import AuthSession, User
from axiomq_api.modules.identity.service import IdentityService


def get_identity_service(
    container: ContainerDep, uow: UowDep, meta: RequestMetaDep
) -> IdentityService:
    return IdentityService(container, uow, meta)


IdentityDep = Annotated[IdentityService, Depends(get_identity_service)]


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: AuthSession


def get_auth_context(request: Request, identity: IdentityDep) -> AuthContext:
    result = identity.authenticate(request.cookies.get(SESSION_COOKIE))
    if result is None:
        raise NotAuthenticated()
    return AuthContext(user=result[0], session=result[1])


AuthDep = Annotated[AuthContext, Depends(get_auth_context)]
