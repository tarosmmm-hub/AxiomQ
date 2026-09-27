from __future__ import annotations

import pytest

from axiomq_api.modules.analytics.events import (
    EVENT_PROPERTIES,
    InvalidAnalyticsEvent,
    validate_event,
)


def test_catalogue_contains_required_events() -> None:
    required = {
        "strategy_created",
        "backtest_started",
        "backtest_completed",
        "experiment_saved",
        "paper_account_created",
    }
    assert required <= set(EVENT_PROPERTIES)


def test_accepts_allow_listed_scalar_properties() -> None:
    assert validate_event("backtest_completed", {"status": "SUCCEEDED", "duration_ms": 12}) == {
        "status": "SUCCEEDED",
        "duration_ms": 12,
    }


def test_rejects_unknown_event() -> None:
    with pytest.raises(InvalidAnalyticsEvent, match="Unknown"):
        validate_event("page_viewed", {})


def test_rejects_non_allow_listed_property() -> None:
    # e.g. an email or the strategy spec must never end up in analytics
    with pytest.raises(InvalidAnalyticsEvent, match="not allowed"):
        validate_event("strategy_created", {"email": "ana@example.com"})


def test_rejects_non_scalar_values() -> None:
    with pytest.raises(InvalidAnalyticsEvent, match="scalar"):
        validate_event("strategy_created", {"strategy_id": {"nested": 1}})  # type: ignore[dict-item]
