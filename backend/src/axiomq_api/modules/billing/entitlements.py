"""Catalogue of entitlement keys.

The *keys* (and whether each is a quota or a feature flag) live in code because code has to
enforce them. The *values* per plan live in the ``plan_entitlements`` table.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class EntitlementKind(StrEnum):
    QUOTA = "QUOTA"  # integer limit, NULL = unlimited
    FEATURE = "FEATURE"  # boolean flag


ENTITLEMENT_KEYS: Final[dict[str, EntitlementKind]] = {
    "backtests_per_day": EntitlementKind.QUOTA,
    "paper_accounts": EntitlementKind.QUOTA,
    "max_workspace_members": EntitlementKind.QUOTA,
    "shared_strategies": EntitlementKind.FEATURE,
}
