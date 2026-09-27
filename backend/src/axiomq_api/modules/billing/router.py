from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from axiomq_api.core.deps import UowDep
from axiomq_api.modules.billing.service import get_entitlements
from axiomq_api.modules.identity.deps import AuthDep
from axiomq_api.modules.workspaces.service import personal_workspace, require_membership

router = APIRouter(prefix="/me/entitlements", tags=["billing"])


class PlanOut(BaseModel):
    code: str
    name: str


class EntitlementsOut(BaseModel):
    workspace_id: uuid.UUID
    plan: PlanOut
    # null = unlimited
    quotas: dict[str, int | None]
    features: dict[str, bool]


@router.get("", response_model=EntitlementsOut)
def my_entitlements(
    auth: AuthDep, uow: UowDep, workspace_id: uuid.UUID | None = None
) -> EntitlementsOut:
    """Entitlements of a workspace the user belongs to (defaults to the personal workspace).

    The frontend only uses this to adapt the UI; the backend enforces limits on every action.
    """
    if workspace_id is None:
        workspace_id = personal_workspace(uow.session, auth.user.id).id
    else:
        require_membership(uow.session, workspace_id=workspace_id, user_id=auth.user.id)
    ent = get_entitlements(uow.session, workspace_id)
    return EntitlementsOut(
        workspace_id=workspace_id,
        plan=PlanOut(code=ent.plan.code.value, name=ent.plan.name),
        quotas=ent.quotas,
        features=ent.features,
    )
