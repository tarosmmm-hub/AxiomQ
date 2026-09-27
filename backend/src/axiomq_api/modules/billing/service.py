"""Plans, subscriptions and entitlement checks (no payment integration yet).

Stripe will later be a ``BillingProvider`` that updates ``subscriptions`` from signed webhooks;
everything else keeps reading only ``subscriptions`` through this service.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from axiomq_api.core.errors import FeatureNotAvailable, QuotaExceeded
from axiomq_api.modules.billing.entitlements import ENTITLEMENT_KEYS, EntitlementKind
from axiomq_api.modules.billing.models import (
    Plan,
    PlanCode,
    PlanEntitlement,
    Subscription,
    SubscriptionStatus,
)

# PAST_DUE keeps access during the payment provider's retry window.
ENTITLED_STATUSES = frozenset(
    {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING, SubscriptionStatus.PAST_DUE}
)


@dataclass(frozen=True)
class Entitlements:
    plan: Plan
    quotas: dict[str, int | None] = field(default_factory=dict)
    features: dict[str, bool] = field(default_factory=dict)

    def quota(self, key: str) -> int | None:
        _require_kind(key, EntitlementKind.QUOTA)
        # A quota missing from the plan's data is treated as 0 (fail closed), never unlimited.
        return self.quotas.get(key, 0)

    def has_feature(self, key: str) -> bool:
        _require_kind(key, EntitlementKind.FEATURE)
        return self.features.get(key, False)


def _require_kind(key: str, kind: EntitlementKind) -> None:
    if ENTITLEMENT_KEYS.get(key) is not kind:
        raise KeyError(f"{key!r} is not a known {kind.value.lower()} entitlement")


def get_plan(db: Session, code: PlanCode) -> Plan:
    return db.execute(select(Plan).where(Plan.code == code)).scalar_one()


def create_free_subscription(db: Session, workspace_id: uuid.UUID) -> Subscription:
    subscription = Subscription(
        workspace_id=workspace_id,
        plan_id=get_plan(db, PlanCode.FREE).id,
        status=SubscriptionStatus.ACTIVE,
        provider="none",
    )
    db.add(subscription)
    return subscription


def effective_plan(db: Session, workspace_id: uuid.UUID) -> Plan:
    row = db.execute(
        select(Plan, Subscription.status)
        .join(Subscription, Subscription.plan_id == Plan.id)
        .where(Subscription.workspace_id == workspace_id)
    ).first()
    if row is None or row[1] not in ENTITLED_STATUSES:
        return get_plan(db, PlanCode.FREE)
    plan: Plan = row[0]
    return plan


def get_entitlements(db: Session, workspace_id: uuid.UUID) -> Entitlements:
    plan = effective_plan(db, workspace_id)
    rows = db.execute(select(PlanEntitlement).where(PlanEntitlement.plan_id == plan.id)).scalars()
    quotas: dict[str, int | None] = {}
    features: dict[str, bool] = {}
    for row in rows:
        kind = ENTITLEMENT_KEYS.get(row.key)
        if kind is EntitlementKind.QUOTA:
            quotas[row.key] = row.int_value
        elif kind is EntitlementKind.FEATURE:
            features[row.key] = bool(row.bool_value)
    return Entitlements(plan=plan, quotas=quotas, features=features)


def ensure_feature(entitlements: Entitlements, key: str) -> None:
    if not entitlements.has_feature(key):
        raise FeatureNotAvailable(extra={"entitlement": key, "plan": entitlements.plan.code.value})


def ensure_quota(entitlements: Entitlements, key: str, *, current_usage: int) -> None:
    """Raise if performing one more unit of ``key`` would exceed the plan's quota."""
    limit = entitlements.quota(key)
    if limit is not None and current_usage >= limit:
        raise QuotaExceeded(
            f"Your plan allows {limit} for '{key}'.",
            extra={"entitlement": key, "limit": limit, "plan": entitlements.plan.code.value},
        )
