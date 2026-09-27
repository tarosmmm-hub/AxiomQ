from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from axiomq_api.db.base import Base, CreatedAt, UUIDPrimaryKey
from axiomq_api.db.types import str_enum


class User(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "users"

    # Stored normalised (trimmed, lower-case); uniqueness is enforced on this column.
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(80))
    email_verified_at: Mapped[datetime | None]
    last_login_at: Mapped[datetime | None]
    disabled_at: Mapped[datetime | None]

    __table_args__ = (CheckConstraint("email = lower(email)", name="email_lowercase"),)


class AuthSession(UUIDPrimaryKey, CreatedAt, Base):
    """Server-side session. Only the SHA-256 of the cookie token is stored."""

    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(256))

    __table_args__ = (Index("ix_sessions_user_id_active", "user_id", "revoked_at"),)


class TokenPurpose(StrEnum):
    PASSWORD_RESET = "PASSWORD_RESET"  # noqa: S105
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"


class UserToken(UUIDPrimaryKey, CreatedAt, Base):
    """Single-use, expiring token sent by email. Only the SHA-256 is stored."""

    __tablename__ = "user_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    purpose: Mapped[TokenPurpose] = mapped_column(str_enum(TokenPurpose, "token_purpose"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None]
    revoked_at: Mapped[datetime | None]

    __table_args__ = (Index("ix_user_tokens_user_purpose", "user_id", "purpose"),)
