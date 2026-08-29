"""Seed the Day 9 support agent, demo tools, and least-privilege permissions."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

revision: str = "20260829_0003"
down_revision: str | None = "20260828_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_ID = uuid.UUID("a9e17000-0000-4000-8000-000000000000")
AGENT_ID = uuid.UUID("a9e17000-0000-4000-8000-000000000001")
TOOL_IDS = {
    "get_customer": uuid.UUID("a9e17000-0000-4000-8000-000000000101"),
    "send_email": uuid.UUID("a9e17000-0000-4000-8000-000000000102"),
    "issue_refund": uuid.UUID("a9e17000-0000-4000-8000-000000000103"),
    "fetch_url": uuid.UUID("a9e17000-0000-4000-8000-000000000104"),
}
SEEDED_AT = datetime(2026, 8, 29, tzinfo=UTC)


def upgrade() -> None:
    users = sa.table(
        "users",
        sa.column("id", sa.Uuid()),
        sa.column("email", sa.String()),
        sa.column("display_name", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    agents = sa.table(
        "agents",
        sa.column("id", sa.Uuid()),
        sa.column("owner_id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("system_prompt", sa.Text()),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    tools = sa.table(
        "tools",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("input_schema", sa.JSON()),
        sa.column("is_enabled", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    permissions = sa.table(
        "agent_permissions",
        sa.column("id", sa.Uuid()),
        sa.column("agent_id", sa.Uuid()),
        sa.column("tool_id", sa.Uuid()),
        sa.column("allowed", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    op.bulk_insert(
        users,
        [
            {
                "id": USER_ID,
                "email": "support-agent@agentshield.local",
                "display_name": "AgentShield Demo",
                "is_active": True,
                "created_at": SEEDED_AT,
                "updated_at": SEEDED_AT,
            }
        ],
    )
    op.bulk_insert(
        agents,
        [
            {
                "id": AGENT_ID,
                "owner_id": USER_ID,
                "name": "support-agent",
                "description": "Least-privilege support demo agent",
                "system_prompt": "Use only tools authorized by AgentShield.",
                "is_active": True,
                "created_at": SEEDED_AT,
                "updated_at": SEEDED_AT,
            }
        ],
    )
    for name, tool_id in TOOL_IDS.items():
        op.execute(
            tools.insert().values(
                id=tool_id,
                name=name,
                description=f"AgentShield controlled demo tool: {name}",
                input_schema=sa.cast(op.inline_literal('{"type": "object"}'), sa.JSON()),
                is_enabled=True,
                created_at=SEEDED_AT,
                updated_at=SEEDED_AT,
            )
        )
    op.bulk_insert(
        permissions,
        [
            {
                "id": uuid.UUID(f"a9e17000-0000-4000-8000-{index:012d}"),
                "agent_id": AGENT_ID,
                "tool_id": tool_id,
                "allowed": name != "issue_refund",
                "created_at": SEEDED_AT,
                "updated_at": SEEDED_AT,
            }
            for index, (name, tool_id) in enumerate(TOOL_IDS.items(), start=201)
        ],
    )


def downgrade() -> None:
    permissions = sa.table(
        "agent_permissions",
        sa.column("agent_id", sa.Uuid()),
    )
    tools = sa.table("tools", sa.column("id", sa.Uuid()))
    agents = sa.table("agents", sa.column("id", sa.Uuid()))
    users = sa.table("users", sa.column("id", sa.Uuid()))

    op.execute(permissions.delete().where(permissions.c.agent_id == AGENT_ID))
    op.execute(tools.delete().where(tools.c.id.in_(tuple(TOOL_IDS.values()))))
    op.execute(agents.delete().where(agents.c.id == AGENT_ID))
    op.execute(users.delete().where(users.c.id == USER_ID))
