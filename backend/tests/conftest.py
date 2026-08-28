import uuid
from datetime import UTC, datetime

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.agent.audit import get_tool_call_store
from app.main import app
from app.models import ToolCall


class InMemoryToolCallStore:
    def __init__(self) -> None:
        self.calls: list[ToolCall] = []

    async def record(self, **values) -> ToolCall:
        call = ToolCall(id=uuid.uuid4(), created_at=datetime.now(UTC), **values)
        self.calls.append(call)
        return call

    async def list_recent(self, limit: int) -> list[ToolCall]:
        return list(reversed(self.calls[-limit:]))


@pytest_asyncio.fixture
async def client():
    store = InMemoryToolCallStore()

    async def override_store():
        return store

    app.dependency_overrides[get_tool_call_store] = override_store
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as value:
            yield value
    finally:
        app.dependency_overrides.pop(get_tool_call_store, None)
