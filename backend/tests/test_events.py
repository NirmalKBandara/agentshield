import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.main import app
from app.models import Agent, SecurityEvent, ToolCall


class FakeEventSession:
    def __init__(
        self,
        events: list[SecurityEvent],
        detail: SecurityEvent | None = None,
        tool_calls: list[ToolCall] | None = None,
    ) -> None:
        self.events = events
        self.detail = detail
        self.tool_calls = tool_calls
        self.statements = []

    async def scalars(self, statement):
        self.statements.append(statement)
        return self.tool_calls if self.tool_calls is not None else self.events

    async def scalar(self, statement):
        self.statements.append(statement)
        return self.detail


def make_event(*, linked: bool = True) -> SecurityEvent:
    call_id = uuid.uuid4()
    call = ToolCall(
        id=call_id,
        request_id="request-123",
        tool_name="issue_refund",
        arguments={"amount": 500},
        status="blocked",
        created_at=datetime(2026, 8, 31, 10, 0, tzinfo=UTC),
    )
    event = SecurityEvent(
        id=uuid.uuid4(),
        tool_call_id=call_id if linked else None,
        event_type="tool_call_blocked",
        severity="high",
        message="Refund exceeds policy limit",
        details={
            "tool": "issue_refund",
            "reason": "Policy limit is 100",
            "request_id": "request-123",
        },
        risk_score=Decimal("87.50"),
        created_at=datetime(2026, 8, 31, 10, 1, tzinfo=UTC),
    )
    if linked:
        event.tool_call = call
    return event


def make_tool_call() -> ToolCall:
    agent_id = uuid.uuid4()
    agent = Agent(
        id=agent_id,
        owner_id=uuid.uuid4(),
        name="Support Agent",
        description=None,
        system_prompt="Help customers",
    )
    call = ToolCall(
        id=uuid.uuid4(),
        request_id="request-sensitive",
        agent_id=agent_id,
        tool_name="issue_refund",
        arguments={
            "amount": 25,
            "password": "do-not-return",
            "customer": {
                "access-token": "nested-secret",
                "contacts": [{"email": "user@example.com", "api_key": "raw-key"}],
            },
        },
        result={"reason": "POLICY_LIMIT", "risk_score": 80},
        status="blocked",
        duration_ms=12,
        created_at=datetime(2026, 8, 31, 11, 0, tzinfo=UTC),
    )
    call.agent = agent
    call.security_events = [
        SecurityEvent(
            id=uuid.uuid4(),
            tool_call_id=call.id,
            event_type="tool_call_blocked",
            severity="high",
            message="Blocked",
            details={},
            risk_score=Decimal("80"),
            created_at=datetime(2026, 8, 31, 11, 1, tzinfo=UTC),
        ),
        SecurityEvent(
            id=uuid.uuid4(),
            tool_call_id=call.id,
            event_type="sensitive_data",
            severity="warning",
            message="Sensitive data",
            details={},
            risk_score=Decimal("45"),
            created_at=datetime(2026, 8, 31, 11, 2, tzinfo=UTC),
        ),
    ]
    return call


@pytest.fixture
def event_session() -> FakeEventSession:
    event = make_event()
    return FakeEventSession([event], detail=event)


@pytest.fixture
async def event_client(event_session: FakeEventSession):
    async def override_session():
        yield event_session

    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_session, None)


async def test_list_security_events_exposes_inspection_fields(
    event_client: AsyncClient, event_session: FakeEventSession
) -> None:
    response = await event_client.get(
        "/api/v1/security-events",
        params={
            "severity": "high",
            "event_type": "tool_call_blocked",
            "tool": "issue_refund",
            "decision": "BLOCK",
            "min_risk_score": 50,
            "limit": 25,
            "offset": 10,
            "tool_call_id": str(event_session.events[0].tool_call_id),
        },
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(event_session.events[0].id),
            "event_type": "tool_call_blocked",
            "threat_category": "tool_call_blocked",
            "severity": "high",
            "risk_level": "high",
            "message": "Refund exceeds policy limit",
            "reason": "Policy limit is 100",
            "risk_score": 87.5,
            "tool_call_id": str(event_session.events[0].tool_call_id),
            "tool": "issue_refund",
            "decision": "BLOCK",
            "created_at": "2026-08-31T10:01:00Z",
            "details": {
                "tool": "issue_refund",
                "reason": "Policy limit is 100",
                "request_id": "request-123",
            },
        }
    ]

    sql = str(event_session.statements[0].compile(compile_kwargs={"literal_binds": True}))
    assert "security_events.severity = 'high'" in sql
    assert "security_events.event_type = 'tool_call_blocked'" in sql
    assert "tool_calls.tool_name = 'issue_refund'" in sql
    assert "tool_calls.status = 'blocked'" in sql
    assert "security_events.risk_score >= 50.0" in sql
    assert f"security_events.tool_call_id = '{event_session.events[0].tool_call_id.hex}'" in sql
    assert "LIMIT 25" in sql
    assert "OFFSET 10" in sql


async def test_list_security_events_validates_filters(event_client: AsyncClient) -> None:
    invalid_severity = await event_client.get(
        "/api/v1/security-events", params={"severity": "urgent"}
    )
    invalid_decision = await event_client.get(
        "/api/v1/security-events", params={"decision": "deny"}
    )
    invalid_limit = await event_client.get("/api/v1/security-events", params={"limit": 201})
    invalid_risk = await event_client.get(
        "/api/v1/security-events", params={"min_risk_score": 101}
    )
    invalid_offset = await event_client.get(
        "/api/v1/security-events", params={"offset": -1}
    )
    invalid_tool_call_id = await event_client.get(
        "/api/v1/security-events", params={"tool_call_id": "not-a-uuid"}
    )

    assert invalid_severity.status_code == 422
    assert invalid_decision.status_code == 422
    assert invalid_limit.status_code == 422
    assert invalid_risk.status_code == 422
    assert invalid_offset.status_code == 422
    assert invalid_tool_call_id.status_code == 422


async def test_get_security_event_returns_detail(
    event_client: AsyncClient, event_session: FakeEventSession
) -> None:
    event = event_session.events[0]
    response = await event_client.get(f"/api/v1/security-events/{event.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(event.id)
    assert response.json()["reason"] == "Policy limit is 100"
    assert response.json()["decision"] == "BLOCK"
    assert event.id.hex in str(
        event_session.statements[0].compile(compile_kwargs={"literal_binds": True})
    )


async def test_get_security_event_returns_404(event_session: FakeEventSession) -> None:
    event_session.detail = None

    async def override_session():
        yield event_session

    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/security-events/{uuid.uuid4()}")
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 404
    assert response.json()["detail"] == "Security event not found"


async def test_get_security_event_rejects_malformed_id(event_client: AsyncClient) -> None:
    response = await event_client.get("/api/v1/security-events/not-a-uuid")

    assert response.status_code == 422


async def test_list_tool_calls_returns_typed_sanitized_audit_fields() -> None:
    call = make_tool_call()
    session = FakeEventSession([], tool_calls=[call])

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/tool-calls",
                params={
                    "agent_id": str(call.agent_id),
                    "agent": "Support Agent",
                    "tool": "issue_refund",
                    "decision": "BLOCK",
                    "limit": 25,
                    "offset": 5,
                },
            )
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 200
    payload = response.json()[0]
    assert payload == {
        "id": str(call.id),
        "request_id": "request-sensitive",
        "agent_id": str(call.agent_id),
        "agent_name": "Support Agent",
        "tool_name": "issue_refund",
        "status": "blocked",
        "decision": "BLOCK",
        "risk_score": 80.0,
        "duration_ms": 12,
        "created_at": "2026-08-31T11:00:00Z",
        "arguments": {
            "amount": 25,
            "password": "***MASKED***",
            "customer": {
                "access-token": "***MASKED***",
                "contacts": [{"email": "user@example.com", "api_key": "***MASKED***"}],
            },
        },
        "result": {"reason": "POLICY_LIMIT", "risk_score": 80},
        "security_event_id": str(call.security_events[0].id),
    }
    assert "do-not-return" not in response.text
    assert "nested-secret" not in response.text
    assert "raw-key" not in response.text

    sql = str(session.statements[0].compile(compile_kwargs={"literal_binds": True}))
    assert f"tool_calls.agent_id = '{call.agent_id.hex}'" in sql
    assert "agents.name = 'Support Agent'" in sql
    assert "tool_calls.tool_name = 'issue_refund'" in sql
    assert "tool_calls.status = 'blocked'" in sql
    assert "LIMIT 25" in sql
    assert "OFFSET 5" in sql


async def test_list_tool_calls_selects_highest_risk_event_with_latest_tiebreak() -> None:
    call = make_tool_call()
    latest_high_risk = SecurityEvent(
        id=uuid.uuid4(),
        tool_call_id=call.id,
        event_type="tool_call_blocked",
        severity="critical",
        message="Escalated",
        details={},
        risk_score=Decimal("80"),
        created_at=datetime(2026, 8, 31, 11, 3, tzinfo=UTC),
    )
    call.security_events.append(latest_high_risk)
    session = FakeEventSession([], tool_calls=[call])

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/tool-calls")
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 200
    assert response.json()[0]["risk_score"] == 80.0
    assert response.json()[0]["security_event_id"] == str(latest_high_risk.id)


async def test_list_tool_calls_validates_filters_and_pagination() -> None:
    session = FakeEventSession([], tool_calls=[])

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            responses = [
                await client.get("/api/v1/tool-calls", params={"status": "unknown"}),
                await client.get("/api/v1/tool-calls", params={"decision": "DENY"}),
                await client.get("/api/v1/tool-calls", params={"agent_id": "bad-id"}),
                await client.get("/api/v1/tool-calls", params={"limit": 0}),
                await client.get("/api/v1/tool-calls", params={"offset": -1}),
                await client.get(
                    "/api/v1/tool-calls", params={"tool": "a", "tool_name": "b"}
                ),
                await client.get(
                    "/api/v1/tool-calls", params={"status": "failed", "decision": "ALLOW"}
                ),
            ]
    finally:
        app.dependency_overrides.pop(get_session, None)

    assert [response.status_code for response in responses] == [422] * len(responses)
