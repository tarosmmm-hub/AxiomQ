"""Catalogue of product analytics events and their allow-listed properties.

Rules (ARCHITECTURE §13): no PII, no strategy contents, scalar values only. Adding an event or a
property is a code change that goes through review.
"""

from __future__ import annotations

from typing import Final

Scalar = str | int | float | bool | None

EVENT_PROPERTIES: Final[dict[str, frozenset[str]]] = {
    "strategy_created": frozenset({"strategy_id", "schema_version", "universe_size", "timeframe"}),
    "backtest_started": frozenset({"backtest_id", "strategy_version_id", "timeframe", "market"}),
    "backtest_completed": frozenset({"backtest_id", "status", "duration_ms", "num_bars"}),
    "backtest_failed": frozenset({"backtest_id", "error_code"}),
    "experiment_saved": frozenset({"experiment_id", "is_rerun"}),
    "paper_account_created": frozenset({"paper_account_id", "feed_kind", "market"}),
}


class InvalidAnalyticsEvent(ValueError):
    pass


def validate_event(name: str, properties: dict[str, Scalar]) -> dict[str, Scalar]:
    allowed = EVENT_PROPERTIES.get(name)
    if allowed is None:
        raise InvalidAnalyticsEvent(f"Unknown analytics event: {name!r}")
    unknown = set(properties) - allowed
    if unknown:
        raise InvalidAnalyticsEvent(f"Properties not allowed for {name!r}: {sorted(unknown)}")
    for key, value in properties.items():
        if value is not None and not isinstance(value, str | int | float | bool):
            raise InvalidAnalyticsEvent(f"Property {key!r} must be a scalar")
    return dict(properties)
