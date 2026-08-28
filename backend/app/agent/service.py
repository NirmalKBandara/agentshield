import json
import time
from typing import Any

from pydantic import ValidationError

from app.agent.audit import ToolCallStore
from app.agent.providers import AgentProvider, build_provider
from app.agent.schemas import AgentDecision, AgentRunResponse
from app.core.config import get_settings
from app.models import ToolCall
from app.tools.registry import ToolRegistry, default_tool_registry


class InvalidModelOutputError(ValueError):
    pass


class ToolExecutionError(RuntimeError):
    """A known tool failed after its execution was attempted."""


def parse_decision(raw_output: str) -> AgentDecision:
    try:
        payload: Any = json.loads(raw_output)
        if not isinstance(payload, dict):
            raise ValueError("model output must be a JSON object")
        return AgentDecision.model_validate(payload)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise InvalidModelOutputError("Model returned an invalid structured decision") from exc


class AgentService:
    def __init__(
        self,
        provider: AgentProvider,
        registry: ToolRegistry,
        tool_call_store: ToolCallStore | None = None,
    ) -> None:
        self.provider = provider
        self.registry = registry
        self.tool_call_store = tool_call_store

    async def run(self, prompt: str, request_id: str = "untracked") -> AgentRunResponse:
        raw_output = await self.provider.decide(prompt, self.registry.schemas())
        decision = parse_decision(raw_output)
        result = None
        tool_call_id = None
        if decision.action == "tool":
            assert decision.tool_name is not None
            started = time.perf_counter()
            try:
                result = self.registry.execute(decision.tool_name, decision.arguments)
            except Exception as exc:
                tool_call = await self._record_tool_call(
                    request_id=request_id,
                    tool_name=decision.tool_name,
                    arguments=decision.arguments,
                    result={"error": str(exc), "error_type": type(exc).__name__},
                    status="failed",
                    started=started,
                )
                tool_call_id = tool_call.id if tool_call else None
                if isinstance(exc, (ValidationError, ValueError)):
                    raise
                raise ToolExecutionError(f"Tool {decision.tool_name} failed") from exc
            tool_call = await self._record_tool_call(
                request_id=request_id,
                tool_name=decision.tool_name,
                arguments=decision.arguments,
                result=result,
                status="succeeded",
                started=started,
            )
            tool_call_id = tool_call.id if tool_call else None
        return AgentRunResponse(
            decision=decision,
            tool_result=result,
            provider=self.provider.name,
            request_id=request_id,
            tool_call_id=tool_call_id,
        )

    async def _record_tool_call(
        self,
        *,
        request_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any] | None,
        status: str,
        started: float,
    ) -> ToolCall | None:
        if self.tool_call_store is None:
            return None
        return await self.tool_call_store.record(
            request_id=request_id,
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            status=status,
            duration_ms=max(0, round((time.perf_counter() - started) * 1000)),
        )


def build_agent_service(tool_call_store: ToolCallStore | None = None) -> AgentService:
    return AgentService(build_provider(get_settings()), default_tool_registry, tool_call_store)
