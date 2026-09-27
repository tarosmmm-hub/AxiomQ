from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from axiomq_api.core.deps import UowDep
from axiomq_api.modules.billing.service import effective_plan
from axiomq_api.modules.identity.deps import AuthDep
from axiomq_api.modules.workspaces.models import WorkspaceKind, WorkspaceRole
from axiomq_api.modules.workspaces.service import list_memberships

router = APIRouter(prefix="/me/workspaces", tags=["workspaces"])


class WorkspaceOut(BaseModel):
    id: uuid.UUID
    name: str
    kind: WorkspaceKind
    role: WorkspaceRole
    plan: str


@router.get("", response_model=list[WorkspaceOut])
def my_workspaces(auth: AuthDep, uow: UowDep) -> list[WorkspaceOut]:
    return [
        WorkspaceOut(
            id=m.workspace.id,
            name=m.workspace.name,
            kind=m.workspace.kind,
            role=m.role,
            plan=effective_plan(uow.session, m.workspace.id).code.value,
        )
        for m in list_memberships(uow.session, auth.user.id)
    ]
