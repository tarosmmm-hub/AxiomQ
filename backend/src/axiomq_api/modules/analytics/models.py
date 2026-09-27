from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from axiomq_api.db.base import Base, UUIDPrimaryKey


class AnalyticsEvent(UUIDPrimaryKey, Base):
    """First-party, non-invasive product event (no PII, allow-listed properties only)."""

    __tablename__ = "analytics_events"

    name: Mapped[str] = mapped_column(String(64))
    occurred_at: Mapped[datetime]
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE")
    )
    user_ref: Mapped[str | None] = mapped_column(String(32))
    properties: Mapped[dict[str, Any]] = mapped_column(default=dict)

    __table_args__ = (Index("ix_analytics_events_name_time", "name", "occurred_at"),)
