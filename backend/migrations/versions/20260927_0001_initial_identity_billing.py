"""Initial schema: identity, workspaces, billing (plans/entitlements), audit, analytics.

Also seeds the plan catalogue (FREE / PRO / TEAM) and its entitlements: reference data that must
exist in every environment, so it lives in a migration rather than in the dev seed script.

Revision ID: 0001
Revises: (none)
Create Date: 2026-09-27 21:59:38.065394
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column(
            "code",
            sa.Enum(
                "FREE",
                "PRO",
                "TEAM",
                name="plan_code",
                native_enum=False,
                create_constraint=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("code IN ('FREE', 'PRO', 'TEAM')", name=op.f("ck_plans_plan_code")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plans")),
        sa.UniqueConstraint("code", name=op.f("uq_plans_code")),
    )
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.CheckConstraint("email = lower(email)", name=op.f("ck_users_email_lowercase")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "audit_log",
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=True),
        sa.Column("target_id", sa.String(length=64), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=256), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name=op.f("fk_audit_log_actor_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_log")),
    )
    op.create_index(
        "ix_audit_log_action_time", "audit_log", ["action", "occurred_at"], unique=False
    )
    op.create_index(
        "ix_audit_log_actor_time", "audit_log", ["actor_user_id", "occurred_at"], unique=False
    )
    op.create_table(
        "plan_entitlements",
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("int_value", sa.Integer(), nullable=True),
        sa.Column("bool_value", sa.Boolean(), nullable=True),
        sa.CheckConstraint(
            "NOT (int_value IS NOT NULL AND bool_value IS NOT NULL)",
            name=op.f("ck_plan_entitlements_single_value_kind"),
        ),
        sa.CheckConstraint(
            "int_value IS NULL OR int_value >= 0",
            name=op.f("ck_plan_entitlements_int_value_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["plans.id"],
            name=op.f("fk_plan_entitlements_plan_id_plans"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("plan_id", "key", name=op.f("pk_plan_entitlements")),
    )
    op.create_table(
        "sessions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=256), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_sessions_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_sessions_token_hash")),
    )
    op.create_index(
        "ix_sessions_user_id_active", "sessions", ["user_id", "revoked_at"], unique=False
    )
    op.create_table(
        "user_tokens",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "purpose",
            sa.Enum(
                "PASSWORD_RESET",
                "EMAIL_VERIFICATION",
                name="token_purpose",
                native_enum=False,
                create_constraint=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "purpose IN ('PASSWORD_RESET', 'EMAIL_VERIFICATION')",
            name=op.f("ck_user_tokens_token_purpose"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_user_tokens_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_user_tokens_token_hash")),
    )
    op.create_index(
        "ix_user_tokens_user_purpose", "user_tokens", ["user_id", "purpose"], unique=False
    )
    op.create_table(
        "workspaces",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "PERSONAL",
                "TEAM",
                name="workspace_kind",
                native_enum=False,
                create_constraint=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column(
            "analytics_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "kind IN ('PERSONAL', 'TEAM')", name=op.f("ck_workspaces_workspace_kind")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_workspaces_owner_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workspaces")),
    )
    op.create_table(
        "analytics_events",
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=True),
        sa.Column("user_ref", sa.String(length=32), nullable=True),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_analytics_events_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_analytics_events")),
    )
    op.create_index(
        "ix_analytics_events_name_time", "analytics_events", ["name", "occurred_at"], unique=False
    )
    op.create_table(
        "subscriptions",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE",
                "TRIALING",
                "PAST_DUE",
                "CANCELED",
                name="subscription_status",
                native_enum=False,
                create_constraint=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_customer_id", sa.String(length=128), nullable=True),
        sa.Column("provider_subscription_id", sa.String(length=128), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'TRIALING', 'PAST_DUE', 'CANCELED')",
            name=op.f("ck_subscriptions_subscription_status"),
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["plans.id"],
            name=op.f("fk_subscriptions_plan_id_plans"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_subscriptions_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subscriptions")),
        sa.UniqueConstraint("workspace_id", name=op.f("uq_subscriptions_workspace_id")),
    )
    op.create_table(
        "workspace_members",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "OWNER",
                "ADMIN",
                "MEMBER",
                "VIEWER",
                name="workspace_role",
                native_enum=False,
                create_constraint=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('OWNER', 'ADMIN', 'MEMBER', 'VIEWER')",
            name=op.f("ck_workspace_members_workspace_role"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_workspace_members_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_workspace_members_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("workspace_id", "user_id", name=op.f("pk_workspace_members")),
    )
    op.create_index(
        op.f("ix_workspace_members_user_id"), "workspace_members", ["user_id"], unique=False
    )
    _seed_plans()


# Initial plan catalogue. NULL int_value = unlimited quota. Later changes to limits are new
# data migrations (or an admin tool), never code changes in components.
PLANS = {
    "FREE": (
        "Free",
        {
            "backtests_per_day": 5,
            "paper_accounts": 1,
            "max_workspace_members": 1,
            "shared_strategies": False,
        },
    ),
    "PRO": (
        "Pro",
        {
            "backtests_per_day": None,
            "paper_accounts": None,
            "max_workspace_members": 1,
            "shared_strategies": False,
        },
    ),
    "TEAM": (
        "Team",
        {
            "backtests_per_day": None,
            "paper_accounts": None,
            "max_workspace_members": 20,
            "shared_strategies": True,
        },
    ),
}
PLAN_NAMESPACE = uuid.UUID("6f1c7a52-6c55-4a3e-9c1e-0a7f3f2b9d10")


def _seed_plans() -> None:
    plans = sa.table(
        "plans",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
    )
    ents = sa.table(
        "plan_entitlements",
        sa.column("plan_id", sa.Uuid()),
        sa.column("key", sa.String()),
        sa.column("int_value", sa.Integer()),
        sa.column("bool_value", sa.Boolean()),
    )
    plan_rows, ent_rows = [], []
    for code, (name, values) in PLANS.items():
        plan_id = uuid.uuid5(PLAN_NAMESPACE, code)  # deterministic ids across environments
        plan_rows.append({"id": plan_id, "code": code, "name": name})
        for key, value in values.items():
            is_bool = isinstance(value, bool)
            ent_rows.append(
                {
                    "plan_id": plan_id,
                    "key": key,
                    "int_value": None if is_bool else value,
                    "bool_value": value if is_bool else None,
                }
            )
    op.bulk_insert(plans, plan_rows)
    op.bulk_insert(ents, ent_rows)


def downgrade() -> None:
    op.drop_index(op.f("ix_workspace_members_user_id"), table_name="workspace_members")
    op.drop_table("workspace_members")
    op.drop_table("subscriptions")
    op.drop_index("ix_analytics_events_name_time", table_name="analytics_events")
    op.drop_table("analytics_events")
    op.drop_table("workspaces")
    op.drop_index("ix_user_tokens_user_purpose", table_name="user_tokens")
    op.drop_table("user_tokens")
    op.drop_index("ix_sessions_user_id_active", table_name="sessions")
    op.drop_table("sessions")
    op.drop_table("plan_entitlements")
    op.drop_index("ix_audit_log_actor_time", table_name="audit_log")
    op.drop_index("ix_audit_log_action_time", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_table("users")
    op.drop_table("plans")
