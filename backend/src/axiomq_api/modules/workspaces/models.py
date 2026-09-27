from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import ForeignKey, String, true
from sqlalchemy.orm import Mapped, mapped_column

from axiomq_api.db.base import Base, CreatedAt, UUIDPrimaryKey
from axiomq_api.db.types import str_enum


class WorkspaceKind(StrEnum):
    PERSONAL = "PERSONAL"
    TEAM = "TEAM"


class WorkspaceRole(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


class Workspace(UUIDPrimaryKey, CreatedAt, Base):
    """Tenant boundary (ADR-0008): every business resource belongs to a workspace."""

    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[WorkspaceKind] = mapped_column(str_enum(WorkspaceKind, "workspace_kind"))
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    analytics_enabled: Mapped[bool] = mapped_column(server_default=true(), default=True)


class WorkspaceMember(CreatedAt, Base):
    __tablename__ = "workspace_members"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    role: Mapped[WorkspaceRole] = mapped_column(str_enum(WorkspaceRole, "workspace_role"))
