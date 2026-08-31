import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.main import app
from app.models import SecurityEvent, ToolCall


class FakeEventSession:
    def __init__(self, events: list[SecurityEvent], detail: SecurityEvent | None = None) -> None:
        self.events = events
        self.detail = detail
        self.statements = []

    async def scalars(self, statement):
        self.statements.append(statement)
        return self.events

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

    assert invalid_severity.status_code == 422
    assert invalid_decision.status_code == 422
    assert invalid_limit.status_code == 422
    assert invalid_risk.status_code == 422
    assert invalid_offset.status_code == 422


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
