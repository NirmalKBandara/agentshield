import os
import uuid

import pytest
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Agent, ToolCall, User


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "1",
    reason="set RUN_POSTGRES_TESTS=1 with a migrated PostgreSQL database",
)
async def test_migrated_postgres_supports_create_and_read() -> None:
    email = f"ci-{uuid.uuid4()}@example.test"
    async with SessionLocal() as session:
        user = User(email=email, display_name="PostgreSQL CI")
        user.agents.append(Agent(name="PostgreSQL Agent", system_prompt="Use demo tools"))
        session.add(user)
        await session.commit()

        stored = await session.scalar(select(User).where(User.email == email))
        assert stored is not None
        assert stored.display_name == "PostgreSQL CI"

        tool_call = ToolCall(
            request_id=f"postgres-{uuid.uuid4()}",
            tool_name="get_customer",
            arguments={"customer_id": "1002"},
            result={"found": True},
            status="succeeded",
            duration_ms=1,
        )
        session.add(tool_call)
        await session.commit()
        stored_call = await session.scalar(
            select(ToolCall).where(ToolCall.request_id == tool_call.request_id)
        )
        assert stored_call is not None
        assert stored_call.status == "succeeded"

        await session.delete(stored)
        await session.delete(stored_call)
        await session.commit()
