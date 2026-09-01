import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.main import app
from app.models import Agent, AgentPermission, Policy, PolicyAuditLog, Tool


class FakePolicySession:
    def __init__(self) -> None:
        now = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
        self.policy = Policy(
            id=uuid.uuid4(),
            name="Default agent limits",
            description="Runtime limits",
            rules={"refund_limit": 100.0, "rate_limit_per_minute": 30},
            priority=100,
            is_enabled=True,
            created_at=now,
            updated_at=now,
        )
        agent = Agent(
            id=uuid.uuid4(),
            owner_id=uuid.uuid4(),
            name="support-agent",
            system_prompt="Use approved tools",
        )
        tool = Tool(
            id=uuid.uuid4(),
            name="issue_refund",
            description="Demo refund",
            input_schema={},
        )
        self.permission = AgentPermission(
            id=uuid.uuid4(),
            agent_id=agent.id,
            tool_id=tool.id,
            allowed=False,
            created_at=now,
            updated_at=now,
        )
        self.permission.agent = agent
        self.permission.tool = tool
        self.audits: list[PolicyAuditLog] = []
        self.commits = 0

    async def scalars(self, statement):
        sql = str(statement)
        if "FROM agent_permissions" in sql:
            return [self.permission]
        if "FROM policy_audit_logs" in sql:
            return list(reversed(self.audits))
        return [self.policy]

    async def scalar(self, statement):
        return self.permission if "FROM agent_permissions" in str(statement) else self.policy

    def add(self, value):
        if isinstance(value, PolicyAuditLog):
            value.id = value.id or uuid.uuid4()
            value.created_at = value.created_at or datetime.now(UTC)
            self.audits.append(value)

    async def commit(self):
        self.commits += 1

    async def refresh(self, _):
        return None


@pytest.fixture
async def policy_client():
    session = FakePolicySession()

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client, session
    finally:
        app.dependency_overrides.pop(get_session, None)


async def test_list_policies_includes_limits_permissions_and_audits(policy_client) -> None:
    client, session = policy_client

    response = await client.get("/api/v1/policies")

    assert response.status_code == 200
    payload = response.json()
    assert payload["policies"][0]["refund_limit"] == 100.0
    assert payload["policies"][0]["rate_limit_per_minute"] == 30
    assert payload["permissions"][0]["tool_name"] == "issue_refund"
    assert payload["permissions"][0]["allowed"] is False
    assert payload["recent_changes"] == []
    assert session.commits == 0


async def test_update_limits_validates_persists_and_audits(policy_client) -> None:
    client, session = policy_client

    response = await client.patch(
        f"/api/v1/policies/{session.policy.id}/limits",
        json={"refund_limit": 250.5, "rate_limit_per_minute": 45},
        headers={"X-Request-ID": "policy-change-1", "X-Actor": "security-admin"},
    )

    assert response.status_code == 200
    assert response.json()["refund_limit"] == 250.5
    assert response.json()["rate_limit_per_minute"] == 45
    assert session.commits == 1
    assert len(session.audits) == 1
    audit = session.audits[0]
    assert audit.request_id == "policy-change-1"
    assert audit.actor == "security-admin"
    assert audit.action == "policy_limits_updated"
    assert audit.before["refund_limit"] == 100.0
    assert audit.after["refund_limit"] == 250.5


async def test_invalid_limits_are_rejected_without_audit(policy_client) -> None:
    client, session = policy_client

    response = await client.patch(
        f"/api/v1/policies/{session.policy.id}/limits",
        json={"refund_limit": 0, "rate_limit_per_minute": 1.5},
    )

    assert response.status_code == 422
    assert session.commits == 0
    assert session.audits == []


async def test_toggle_permission_persists_and_audits(policy_client) -> None:
    client, session = policy_client

    response = await client.patch(
        f"/api/v1/policies/permissions/{session.permission.id}",
        json={"allowed": True},
        headers={"X-Request-ID": "permission-change-1"},
    )

    assert response.status_code == 200
    assert response.json()["allowed"] is True
    assert session.permission.allowed is True
    assert session.commits == 1
    assert session.audits[0].action == "tool_permission_updated"
    assert session.audits[0].after == {
        "allowed": True,
        "agent": "support-agent",
        "tool": "issue_refund",
    }
