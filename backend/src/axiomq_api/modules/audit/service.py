"""Security audit log.

``record`` writes inside the caller's transaction (the entry exists iff the action committed).
``record_independent`` uses its own transaction; it is used for events that must be persisted
even though the request fails (e.g. failed logins).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from axiomq_api.core.clock import Clock
from axiomq_api.core.deps import RequestMeta
from axiomq_api.modules.audit.models import AuditLog


class AuditAction:
    USER_REGISTERED = "user.registered"
    REGISTER_EXISTING_EMAIL = "user.register_existing_email"
    LOGIN_SUCCEEDED = "auth.login_succeeded"
    LOGIN_FAILED = "auth.login_failed"
    LOGOUT = "auth.logout"
    PASSWORD_RESET_REQUESTED = "auth.password_reset_requested"
    PASSWORD_RESET_COMPLETED = "auth.password_reset_completed"
    PASSWORD_CHANGED = "auth.password_changed"
    EMAIL_VERIFIED = "auth.email_verified"
    PROFILE_UPDATED = "user.profile_updated"


class AuditService:
    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def _entry(
        self,
        action: str,
        *,
        actor_user_id: uuid.UUID | None,
        target_type: str | None,
        target_id: str | None,
        meta: RequestMeta | None,
        details: dict[str, Any] | None,
    ) -> AuditLog:
        return AuditLog(
            occurred_at=self._clock.now(),
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            ip=meta.ip if meta else None,
            user_agent=meta.user_agent if meta else None,
            details=details or {},
        )

    def record(
        self,
        db: Session,
        action: str,
        *,
        actor_user_id: uuid.UUID | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        meta: RequestMeta | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        db.add(
            self._entry(
                action,
                actor_user_id=actor_user_id,
                target_type=target_type,
                target_id=target_id,
                meta=meta,
                details=details,
            )
        )

    def record_independent(
        self,
        session_factory: sessionmaker[Session],
        action: str,
        *,
        actor_user_id: uuid.UUID | None = None,
        meta: RequestMeta | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        with session_factory() as db:
            db.add(
                self._entry(
                    action,
                    actor_user_id=actor_user_id,
                    target_type=None,
                    target_id=None,
                    meta=meta,
                    details=details,
                )
            )
            db.commit()
