"""Developer/operator commands: ``python -m axiomq_api.cli <command>``.

- ``seed``: development seed data (a verified demo user). Refuses to run in production.
  Plans/entitlements are *not* seeded here: they are reference data created by migrations.
  Market data seeds arrive in Phase 2 and are always labelled with their provenance.
- ``openapi``: print the OpenAPI schema (used to generate the frontend TypeScript client).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from sqlalchemy import select

from axiomq_api.core.config import Environment, RateLimitBackend, get_settings

DEMO_EMAIL = "demo@axiomq.local"


def seed() -> int:
    settings = get_settings()
    if settings.env is Environment.PRODUCTION:
        print("Refusing to seed demo data in production.", file=sys.stderr)
        return 1
    from axiomq_api.core.container import build_container
    from axiomq_api.modules.billing.service import create_free_subscription
    from axiomq_api.modules.identity.models import User
    from axiomq_api.modules.workspaces.service import create_personal_workspace

    password = os.environ.get("AXIOMQ_DEMO_PASSWORD", "axiomq-demo-password")
    container = build_container(settings)
    with container.session_factory() as db:
        if db.execute(select(User).where(User.email == DEMO_EMAIL)).scalar_one_or_none():
            print(f"Demo user already exists: {DEMO_EMAIL}")
            return 0
        user = User(
            email=DEMO_EMAIL,
            password_hash=container.passwords.hash(password),
            display_name="Demo",
            email_verified_at=container.clock.now(),
        )
        db.add(user)
        db.flush()
        workspace = create_personal_workspace(db, owner_id=user.id, display_name="Demo")
        create_free_subscription(db, workspace.id)
        db.commit()
    print(f"Created demo user {DEMO_EMAIL} (password from AXIOMQ_DEMO_PASSWORD or the default).")
    return 0


def openapi() -> int:
    os.environ.setdefault("AXIOMQ_RATE_LIMIT_BACKEND", RateLimitBackend.MEMORY.value)
    from axiomq_api.main import create_app

    get_settings.cache_clear()
    print(json.dumps(create_app().openapi(), indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="axiomq_api.cli")
    parser.add_argument("command", choices=["seed", "openapi"])
    args = parser.parse_args(argv)
    return seed() if args.command == "seed" else openapi()


if __name__ == "__main__":
    raise SystemExit(main())
