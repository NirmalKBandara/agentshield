import pytest

from app.agent.providers import RuleBasedLocalProvider, build_provider
from app.agent.service import AgentService, InvalidModelOutputError, parse_decision
from app.core.config import Settings
from app.tools.registry import UnknownToolError, default_tool_registry


class StaticProvider:
    name = "test"

    def __init__(self, output: str) -> None:
        self.output = output

    async def decide(self, prompt: str, tool_schemas: list[dict]) -> str:
        return self.output


@pytest.mark.asyncio
async def test_natural_language_request_executes_selected_tool() -> None:
    service = AgentService(RuleBasedLocalProvider(), default_tool_registry)
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
    service = AgentService(provider, default_tool_registry)
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
    response = await client.post("/api/v1/agent/run", json={"prompt": "Show customer 1002"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"]["tool_name"] == "get_customer"
    assert payload["tool_result"]["found"] is True
