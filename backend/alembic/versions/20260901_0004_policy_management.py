"""Add configurable security policies and their immutable audit trail."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "20260901_0004"
down_revision: str | None = "20260829_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_POLICY_ID = uuid.UUID("a9e17000-0000-4000-8000-000000000301")
SEEDED_AT = datetime(2026, 9, 1, tzinfo=UTC)


def upgrade() -> None:
    op.create_table(
        "policy_audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.String(128), nullable=False),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("resource_type", sa.String(40), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("before", sa.JSON(), nullable=False),
        sa.Column("after", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_policy_audit_logs_action", "policy_audit_logs", ["action"])
    op.create_index("ix_policy_audit_logs_created_at", "policy_audit_logs", ["created_at"])
    op.create_index("ix_policy_audit_logs_request_id", "policy_audit_logs", ["request_id"])
    op.create_index("ix_policy_audit_logs_resource_id", "policy_audit_logs", ["resource_id"])

    policies = sa.table(
        "policies",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("rules", sa.JSON()),
        sa.column("priority", sa.Integer()),
        sa.column("is_enabled", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        policies,
        [
            {
                "id": DEFAULT_POLICY_ID,
                "name": "Default agent limits",
                "description": "Runtime refund and request-rate limits for the demo agent.",
                "rules": {"refund_limit": 100.0, "rate_limit_per_minute": 30},
                "priority": 100,
                "is_enabled": True,
                "created_at": SEEDED_AT,
                "updated_at": SEEDED_AT,
            }
        ],
    )


def downgrade() -> None:
    policies = sa.table("policies", sa.column("id", sa.Uuid()))
    op.execute(policies.delete().where(policies.c.id == DEFAULT_POLICY_ID))
    op.drop_table("policy_audit_logs")
