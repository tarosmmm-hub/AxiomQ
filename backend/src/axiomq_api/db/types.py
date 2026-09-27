"""Column type helpers."""

from __future__ import annotations

from enum import Enum

from sqlalchemy import Enum as SAEnum


def str_enum(enum_cls: type[Enum], name: str) -> SAEnum:
    """Store enums as VARCHAR + CHECK constraint (not native PG enums: easier to migrate)."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=32,
        validate_strings=True,
        values_callable=lambda members: [m.value for m in members],
    )
