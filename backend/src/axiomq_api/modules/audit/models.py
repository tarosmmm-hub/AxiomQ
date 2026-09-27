from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from axiomq_api.db.base import Base, UUIDPrimaryKey


class AuditLog(UUIDPrimaryKey, Base):
    """Append-only security log."""

    __tablename__ = "audit_log"

    occurred_at: Mapped[datetime]
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(64))
    target_type: Mapped[str | None] = mapped_column(String(64))
    target_id: Mapped[str | None] = mapped_column(String(64))
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(256))
    details: Mapped[dict[str, Any]] = mapped_column(default=dict)

    __table_args__ = (
        Index("ix_audit_log_actor_time", "actor_user_id", "occurred_at"),
        Index("ix_audit_log_action_time", "action", "occurred_at"),
    )
