from collections.abc import Sequence
from typing import Any

from app.gateway.controls import SecurityControl
from app.gateway.schemas import FinalDecision, SecurityContext, SecurityResult
from app.tools.registry import ToolRegistry


class GatewayBlockedError(PermissionError):
    def __init__(self, decision: FinalDecision) -> None:
        self.decision = decision
        super().__init__(decision.reason)


class ToolGateway:
    """The sole application-facing boundary for validating and invoking tools."""

    def __init__(
        self,
        registry: ToolRegistry,
        controls: Sequence[SecurityControl] = (),
    ) -> None:
        self._registry = registry
        self._controls = tuple(controls)

    def schemas(self) -> list[dict[str, Any]]:
        return self._registry.schemas()

    async def authorize(
        self,
        context: SecurityContext,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> FinalDecision:
        results: list[SecurityResult] = []
        for control in self._controls:
            try:
                result = await control.evaluate(context, tool_name, arguments)
            except Exception:
                result = SecurityResult(
                    control=control.name,
                    outcome="block",
                    reason=f"Security control {control.name} failed closed",
                    risk_score=100,
                )
            results.append(result)

        blocked = next((result for result in results if result.outcome == "block"), None)
        if blocked is not None:
            return FinalDecision(outcome="block", reason=blocked.reason, results=tuple(results))
        return FinalDecision(
            outcome="allow",
            reason="All configured security controls allowed the tool call",
            results=tuple(results),
        )

    async def execute(
        self,
        context: SecurityContext,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> tuple[FinalDecision, dict[str, Any]]:
        decision = await self.authorize(context, tool_name, arguments)
        if not decision.allowed:
            raise GatewayBlockedError(decision)
        return decision, self._registry._execute(tool_name, arguments)
