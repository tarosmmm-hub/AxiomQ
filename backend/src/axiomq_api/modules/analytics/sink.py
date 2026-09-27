"""Analytics sinks. Events are written in the caller's transaction, so an event exists only if
the action it describes was committed."""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy.orm import Session

from axiomq_api.core.clock import Clock
from axiomq_api.core.security import pseudonymize
from axiomq_api.modules.analytics.events import Scalar, validate_event
from axiomq_api.modules.analytics.models import AnalyticsEvent
from axiomq_api.modules.workspaces.models import Workspace


class AnalyticsSink(Protocol):
    def track(
        self,
        db: Session,
        name: str,
        *,
        workspace_id: uuid.UUID | None,
        user_id: uuid.UUID | None,
        properties: dict[str, Scalar] | None = None,
    ) -> None: ...


class DatabaseAnalyticsSink:
    def __init__(self, *, secret: str, clock: Clock) -> None:
        self._secret = secret
        self._clock = clock

    def track(
        self,
        db: Session,
        name: str,
        *,
        workspace_id: uuid.UUID | None,
        user_id: uuid.UUID | None,
        properties: dict[str, Scalar] | None = None,
    ) -> None:
        props = validate_event(name, properties or {})
        if workspace_id is not None:
            workspace = db.get(Workspace, workspace_id)
            if workspace is not None and not workspace.analytics_enabled:
                return
        db.add(
            AnalyticsEvent(
                name=name,
                occurred_at=self._clock.now(),
                workspace_id=workspace_id,
                user_ref=pseudonymize(self._secret, str(user_id), purpose="analytics")
                if user_id
                else None,
                properties=props,
            )
        )
