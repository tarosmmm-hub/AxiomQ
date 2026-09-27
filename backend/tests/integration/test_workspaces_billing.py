from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from axiomq_api.core.errors import FeatureNotAvailable, QuotaExceeded
from axiomq_api.modules.analytics.models import AnalyticsEvent
from axiomq_api.modules.analytics.sink import DatabaseAnalyticsSink
from axiomq_api.modules.billing.models import PlanCode, Subscription, SubscriptionStatus
from axiomq_api.modules.billing.service import (
    ensure_feature,
    ensure_quota,
    get_entitlements,
    get_plan,
)
from axiomq_api.modules.workspaces.models import Workspace
from tests.integration.helpers import register_and_login

pytestmark = pytest.mark.integration


def workspace_id(client) -> uuid.UUID:  # type: ignore[no-untyped-def]
    return uuid.UUID(client.get("/api/v1/me/workspaces").json()[0]["id"])


def set_subscription(
    container,
    ws_id: uuid.UUID,
    code: PlanCode,  # type: ignore[no-untyped-def]
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
) -> None:
    with container.session_factory() as db:
        sub = db.execute(
            select(Subscription).where(Subscription.workspace_id == ws_id)
        ).scalar_one()
        sub.plan_id = get_plan(db, code).id
        sub.status = status
        db.commit()


def test_free_plan_entitlements_come_from_data(client) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    body = client.get("/api/v1/me/entitlements").json()
    assert body["plan"]["code"] == "FREE"
    assert body["quotas"]["backtests_per_day"] == 5
    assert body["quotas"]["paper_accounts"] == 1
    assert body["features"]["shared_strategies"] is False


def test_pro_is_unlimited_and_team_shares(client, container) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    ws = workspace_id(client)
    set_subscription(container, ws, PlanCode.PRO)
    body = client.get("/api/v1/me/entitlements").json()
    assert body["plan"]["code"] == "PRO"
    assert body["quotas"]["backtests_per_day"] is None  # unlimited
    set_subscription(container, ws, PlanCode.TEAM)
    assert client.get("/api/v1/me/entitlements").json()["features"]["shared_strategies"] is True


def test_canceled_subscription_falls_back_to_free(client, container) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    set_subscription(container, workspace_id(client), PlanCode.PRO, SubscriptionStatus.CANCELED)
    assert client.get("/api/v1/me/entitlements").json()["plan"]["code"] == "FREE"


def test_quota_and_feature_enforcement(client, container) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    ws = workspace_id(client)
    with container.session_factory() as db:
        ent = get_entitlements(db, ws)
    ensure_quota(ent, "backtests_per_day", current_usage=4)
    with pytest.raises(QuotaExceeded) as exc:
        ensure_quota(ent, "backtests_per_day", current_usage=5)
    assert exc.value.extra["limit"] == 5
    with pytest.raises(FeatureNotAvailable):
        ensure_feature(ent, "shared_strategies")
    with pytest.raises(KeyError):
        ensure_quota(ent, "not_a_real_key", current_usage=0)
    with pytest.raises(KeyError):
        ensure_quota(ent, "shared_strategies", current_usage=0)  # a feature, not a quota


def test_workspace_isolation_between_tenants(client, make_client) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client, email="ana@example.com", name="Ana")
    other = make_client()
    register_and_login(other, email="bob@example.com", name="Bob")
    anas_ws = workspace_id(client)

    assert [w["id"] for w in other.get("/api/v1/me/workspaces").json()] != [str(anas_ws)]
    # Bob cannot read Ana's workspace: 404 (existence is not revealed).
    response = other.get("/api/v1/me/entitlements", params={"workspace_id": str(anas_ws)})
    assert response.status_code == 404
    assert (
        client.get("/api/v1/me/entitlements", params={"workspace_id": str(anas_ws)}).status_code
        == 200
    )


def test_analytics_sink_pseudonymises_and_respects_opt_out(client, container) -> None:  # type: ignore[no-untyped-def]
    register_and_login(client)
    ws = workspace_id(client)
    user_id = uuid.UUID(client.get("/api/v1/me").json()["id"])
    sink = DatabaseAnalyticsSink(secret=container.secret, clock=container.clock)
    with container.session_factory() as db:
        sink.track(
            db,
            "strategy_created",
            workspace_id=ws,
            user_id=user_id,
            properties={"schema_version": 1},
        )
        db.commit()
        event = db.execute(select(AnalyticsEvent)).scalar_one()
        assert event.user_ref
        assert str(user_id) not in event.user_ref
        assert event.properties == {"schema_version": 1}

        db.get(Workspace, ws).analytics_enabled = False  # type: ignore[union-attr]
        db.commit()
        sink.track(db, "strategy_created", workspace_id=ws, user_id=user_id)
        db.commit()
        assert len(db.execute(select(AnalyticsEvent)).scalars().all()) == 1
