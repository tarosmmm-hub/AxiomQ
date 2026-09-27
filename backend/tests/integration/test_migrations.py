from __future__ import annotations

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from axiomq_api.db.models import Base
from tests.conftest import TEST_DATABASE_URL, run_alembic

pytestmark = pytest.mark.integration


def test_models_match_migrations(db_engine) -> None:  # type: ignore[no-untyped-def]
    with db_engine.connect() as conn:
        diff = compare_metadata(
            MigrationContext.configure(conn, opts={"compare_type": True}), Base.metadata
        )
    assert diff == [], f"Models and migrations diverge: {diff}"


def test_downgrade_and_upgrade_roundtrip(db_engine, clean_db) -> None:  # type: ignore[no-untyped-def]
    run_alembic(TEST_DATABASE_URL, "downgrade", "base")
    run_alembic(TEST_DATABASE_URL, "upgrade", "head")
