from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from axiomq_api.db.base import Base, CreatedAt, UUIDPrimaryKey
from axiomq_api.db.types import str_enum


class PlanCode(StrEnum):
    FREE = "FREE"
    PRO = "PRO"
    TEAM = "TEAM"


class SubscriptionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    TRIALING = "TRIALING"
    PAST_DUE = "PAST_DUE"
    CANCELED = "CANCELED"


class Plan(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "plans"

    code: Mapped[PlanCode] = mapped_column(str_enum(PlanCode, "plan_code"), unique=True)
    name: Mapped[str] = mapped_column(String(80))


class PlanEntitlement(Base):
    """Plan limits are data, never hard-coded in code or UI components.

    ``int_value`` is used for quotas (NULL = unlimited); ``bool_value`` for feature flags.
    """

    __tablename__ = "plan_entitlements"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), primary_key=True
    )
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    int_value: Mapped[int | None]
    bool_value: Mapped[bool | None]

    __table_args__ = (
        CheckConstraint("int_value IS NULL OR int_value >= 0", name="int_value_non_negative"),
        CheckConstraint(
            "NOT (int_value IS NOT NULL AND bool_value IS NOT NULL)", name="single_value_kind"
        ),
    )


class Subscription(UUIDPrimaryKey, CreatedAt, Base):
    """One subscription per workspace. Provider fields are ready for Stripe (not integrated)."""

    __tablename__ = "subscriptions"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plans.id", ondelete="RESTRICT"))
    status: Mapped[SubscriptionStatus] = mapped_column(
        str_enum(SubscriptionStatus, "subscription_status")
    )
    provider: Mapped[str] = mapped_column(String(32), default="none")
    provider_customer_id: Mapped[str | None] = mapped_column(String(128))
    provider_subscription_id: Mapped[str | None] = mapped_column(String(128))
    current_period_end: Mapped[datetime | None]
