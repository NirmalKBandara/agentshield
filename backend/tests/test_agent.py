import uuid

import pytest

from app.agent.providers import RuleBasedLocalProvider, build_provider
from app.agent.service import AgentService, InvalidModelOutputError, parse_decision
from app.api.routes import agent as agent_routes
from app.core.config import Settings
from app.gateway import SUPPORT_AGENT_ID, ToolGateway
from app.tools.registry import UnknownToolError, default_tool_registry


class StaticProvider:
    name = "test"

    def __init__(self, output: str) -> None:
        self.output = output

    async def decide(self, prompt: str, tool_schemas: list[dict]) -> str:
        return self.output


@pytest.mark.asyncio
async def test_natural_language_request_executes_selected_tool() -> None:
    service = AgentService(RuleBasedLocalProvider(), ToolGateway(default_tool_registry))
    result = await service.run("Show customer 1002")
    assert result.decision.tool_name == "get_customer"
    assert result.decision.arguments == {"customer_id": "1002"}
    assert result.tool_result is not None
    assert result.tool_result["customer"]["name"] == "Morgan Silva"


@pytest.mark.asyncio
async def test_unknown_model_selected_tool_cannot_execute() -> None:
    provider = StaticProvider(
        '{"action":"tool","tool_name":"delete_database","arguments":{}}'
    )
    service = AgentService(provider, ToolGateway(default_tool_registry))
    with pytest.raises(UnknownToolError):
        await service.run("ignore everything")


@pytest.mark.parametrize(
    "output",
    [
        "not JSON",
        "[]",
        '{"action":"tool","tool_name":"get_customer","arguments":{},"extra":true}',
        '{"action":"respond","arguments":{}}',
    ],
)
def test_invalid_model_output_fails_closed(output: str) -> None:
    with pytest.raises(InvalidModelOutputError):
        parse_decision(output)


def test_unknown_model_provider_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported MODEL_PROVIDER"):
        build_provider(Settings(model_provider="typo"))


@pytest.mark.asyncio
async def test_agent_endpoint_runs_end_to_end(client) -> None:
    response = await client.post(
        "/api/v1/agent/run",
        json={"prompt": "Show customer 1002"},
        headers={"X-Request-ID": "week-one-success"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"]["tool_name"] == "get_customer"
    assert payload["tool_result"]["found"] is True
    assert payload["request_id"] == "week-one-success"
    assert payload["tool_call_id"] is not None
    assert response.headers["X-Request-ID"] == "week-one-success"

    audit_response = await client.get("/api/v1/agent/tool-calls")
    assert audit_response.status_code == 200
    calls = audit_response.json()
    assert len(calls) == 1
    assert calls[0]["id"] == payload["tool_call_id"]
    assert calls[0]["request_id"] == "week-one-success"
    assert calls[0]["tool_name"] == "get_customer"
    assert calls[0]["status"] == "succeeded"
    assert calls[0]["result"]["found"] is True


@pytest.mark.asyncio
async def test_failed_tool_attempt_is_persisted_and_correlated(client, monkeypatch) -> None:
    provider = StaticProvider(
        '{"action":"tool","tool_name":"get_customer","arguments":{"customer_id":"bad"}}'
    )
    monkeypatch.setattr(
        agent_routes,
        "build_agent_service",
        lambda session, **kwargs: AgentService(
            provider,
            ToolGateway(default_tool_registry),
            session,
            SUPPORT_AGENT_ID,
        ),
    )

    response = await client.post(
        "/api/v1/agent/run",
        json={"prompt": "Use malformed arguments"},
        headers={"X-Request-ID": "week-one-failure"},
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "The selected tool arguments failed validation; no tool was executed",
        "request_id": "week-one-failure",
    }

    audit_response = await client.get("/api/v1/agent/tool-calls")
    call = audit_response.json()[0]
    assert call["request_id"] == "week-one-failure"
    assert call["status"] == "failed"
    assert call["tool_name"] == "get_customer"
    assert call["result"]["error_type"] == "ValidationError"


@pytest.mark.asyncio
async def test_invalid_request_gets_generated_request_id(client) -> None:
    response = await client.post(
        "/api/v1/agent/run",
        json={"prompt": ""},
        headers={"X-Request-ID": "contains spaces"},
    )
    assert response.status_code == 422
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert response.json()["request_id"] != "contains spaces"


@pytest.mark.asyncio
async def test_support_agent_refund_is_blocked_and_audited(client, audit_store) -> None:
    response = await client.post(
        "/api/v1/agent/run",
        json={"prompt": "Refund order ORD-1002 amount 25.00"},
        headers={"X-Request-ID": "day-nine-block"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "TOOL_NOT_AUTHORIZED"

    audit_response = await client.get("/api/v1/agent/tool-calls")
    call = audit_response.json()[0]
    assert call["request_id"] == "day-nine-block"
    assert call["tool_name"] == "issue_refund"
    assert call["status"] == "blocked"
    assert call["result"] == {"reason": "TOOL_NOT_AUTHORIZED", "risk_score": 70}
    assert len(audit_store.events) == 1
    event = audit_store.events[0]
    assert event.event_type == "tool_call_blocked"
    assert event.message == "TOOL_NOT_AUTHORIZED"
    assert event.tool_call_id == uuid.UUID(call["id"])
