import os
import uuid

import pytest
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Agent, User


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

        await session.delete(stored)
        await session.commit()
