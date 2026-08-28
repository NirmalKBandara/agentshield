import json
from typing import Any

from pydantic import ValidationError

from app.agent.providers import AgentProvider, build_provider
from app.agent.schemas import AgentDecision, AgentRunResponse
from app.core.config import get_settings
from app.tools.registry import ToolRegistry, default_tool_registry


class InvalidModelOutputError(ValueError):
    pass


def parse_decision(raw_output: str) -> AgentDecision:
    try:
        payload: Any = json.loads(raw_output)
        if not isinstance(payload, dict):
            raise ValueError("model output must be a JSON object")
        return AgentDecision.model_validate(payload)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise InvalidModelOutputError("Model returned an invalid structured decision") from exc


class AgentService:
    def __init__(self, provider: AgentProvider, registry: ToolRegistry) -> None:
        self.provider = provider
        self.registry = registry

    async def run(self, prompt: str) -> AgentRunResponse:
        raw_output = await self.provider.decide(prompt, self.registry.schemas())
        decision = parse_decision(raw_output)
        result = None
        if decision.action == "tool":
            assert decision.tool_name is not None
            result = self.registry.execute(decision.tool_name, decision.arguments)
        return AgentRunResponse(
            decision=decision,
            tool_result=result,
            provider=self.provider.name,
        )


def build_agent_service() -> AgentService:
    return AgentService(build_provider(get_settings()), default_tool_registry)
