"""Create the Day 2 AgentShield schema."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260828_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "agents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tools",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("input_schema", sa.JSON(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tools_name", "tools", ["name"], unique=True)
    op.create_table(
        "policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        *timestamp_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "agent_permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("tool_id", sa.Uuid(), nullable=False),
        sa.Column("allowed", sa.Boolean(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "tool_id", name="uq_agent_permission"),
    )
    op.create_table(
        "tool_calls",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=True),
        sa.Column("tool_name", sa.String(80), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tool_calls_agent_created", "tool_calls", ["agent_id", "created_at"])
    op.create_index("ix_tool_calls_created_at", "tool_calls", ["created_at"])
    op.create_index("ix_tool_calls_status", "tool_calls", ["status"])
    op.create_index("ix_tool_calls_tool_name", "tool_calls", ["tool_name"])
    op.create_table(
        "security_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tool_call_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tool_call_id"], ["tool_calls.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_security_events_created_at", "security_events", ["created_at"])
    op.create_index("ix_security_events_event_type", "security_events", ["event_type"])
    op.create_index("ix_security_events_severity", "security_events", ["severity"])


def downgrade() -> None:
    op.drop_table("security_events")
    op.drop_table("tool_calls")
    op.drop_table("agent_permissions")
    op.drop_table("policies")
    op.drop_table("tools")
    op.drop_table("agents")
    op.drop_table("users")
