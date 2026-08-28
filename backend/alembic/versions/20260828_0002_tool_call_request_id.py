"""Add correlation IDs to tool-call audit records."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260828_0002"
down_revision: str | None = "20260828_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tool_calls",
        sa.Column("request_id", sa.String(length=128), nullable=True),
    )
    op.execute("UPDATE tool_calls SET request_id = 'legacy-' || id::text WHERE request_id IS NULL")
    op.alter_column("tool_calls", "request_id", nullable=False)
    op.create_index("ix_tool_calls_request_id", "tool_calls", ["request_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tool_calls_request_id", table_name="tool_calls")
    op.drop_column("tool_calls", "request_id")
