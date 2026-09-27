"""Workspaces (tenant boundary) and memberships."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from axiomq_api.core.errors import NotFound
from axiomq_api.modules.workspaces.models import (
    Workspace,
    WorkspaceKind,
    WorkspaceMember,
    WorkspaceRole,
)


@dataclass(frozen=True)
class Membership:
    workspace: Workspace
    role: WorkspaceRole


def create_personal_workspace(db: Session, *, owner_id: uuid.UUID, display_name: str) -> Workspace:
    workspace = Workspace(
        name=f"{display_name}'s workspace"[:120], kind=WorkspaceKind.PERSONAL, owner_id=owner_id
    )
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=owner_id, role=WorkspaceRole.OWNER))
    return workspace


def list_memberships(db: Session, user_id: uuid.UUID) -> list[Membership]:
    rows = db.execute(
        select(Workspace, WorkspaceMember.role)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user_id)
        .order_by(Workspace.kind.desc(), Workspace.created_at)  # PERSONAL first
    ).all()
    return [Membership(workspace=ws, role=role) for ws, role in rows]


def require_membership(db: Session, *, workspace_id: uuid.UUID, user_id: uuid.UUID) -> Membership:
    """Return the membership or raise 404 (never 403: do not reveal that a workspace exists)."""
    row = db.execute(
        select(Workspace, WorkspaceMember.role)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(Workspace.id == workspace_id, WorkspaceMember.user_id == user_id)
    ).first()
    if row is None:
        raise NotFound("Workspace not found.")
    return Membership(workspace=row[0], role=row[1])


def personal_workspace(db: Session, user_id: uuid.UUID) -> Workspace:
    workspace = db.execute(
        select(Workspace).where(
            Workspace.owner_id == user_id, Workspace.kind == WorkspaceKind.PERSONAL
        )
    ).scalar_one_or_none()
    if workspace is None:
        raise NotFound("Personal workspace not found.")
    return workspace
