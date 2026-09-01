import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.agent.audit import get_tool_call_store
from app.gateway.permissions import SUPPORT_AGENT_ID, get_permission_store
from app.gateway.policies import get_policy_rule_store, policy_rate_limiter
from app.main import app
from app.models import SecurityEvent, ToolCall


class InMemoryToolCallStore:
    def __init__(self) -> None:
        self.calls: list[ToolCall] = []
        self.events: list[SecurityEvent] = []

    async def record(self, **values) -> ToolCall:
        call = ToolCall(id=uuid.uuid4(), created_at=datetime.now(UTC), **values)
        self.calls.append(call)
        return call

    async def record_blocked_event(self, **values) -> SecurityEvent:
        event = SecurityEvent(
            id=uuid.uuid4(),
            created_at=datetime.now(UTC),
            event_type="tool_call_blocked",
            severity="warning",
            message=values.pop("reason"),
            details={
                "request_id": values["request_id"],
                "agent_id": str(values["agent_id"]) if values["agent_id"] else None,
                "tool": values["tool_name"],
            },
            risk_score=values.pop("risk_score"),
            tool_call_id=values["tool_call_id"],
        )
        self.events.append(event)
        return event

    async def list_recent(self, limit: int) -> list[ToolCall]:
        return list(reversed(self.calls[-limit:]))


@pytest.fixture
def audit_store() -> InMemoryToolCallStore:
    return InMemoryToolCallStore()


@pytest_asyncio.fixture
async def client(audit_store: InMemoryToolCallStore):

    async def override_store():
        return audit_store

    class DemoPermissionStore:
        async def is_allowed(self, agent_id, tool_name):
            return agent_id == SUPPORT_AGENT_ID and tool_name != "issue_refund"

    async def override_permissions():
        return DemoPermissionStore()

    class DemoPolicyRuleStore:
        async def active_rules(self):
            return {"refund_limit": 100.0, "rate_limit_per_minute": 1_000}

    async def override_policy_rules():
        return DemoPolicyRuleStore()

    app.dependency_overrides[get_tool_call_store] = override_store
    app.dependency_overrides[get_permission_store] = override_permissions
    app.dependency_overrides[get_policy_rule_store] = override_policy_rules
    policy_rate_limiter.reset()
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as value:
            yield value
    finally:
        app.dependency_overrides.pop(get_tool_call_store, None)
        app.dependency_overrides.pop(get_permission_store, None)
        app.dependency_overrides.pop(get_policy_rule_store, None)
        policy_rate_limiter.reset()
