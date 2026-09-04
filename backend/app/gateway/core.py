from collections.abc import Sequence
from typing import Any

from app.gateway.controls import SecurityControl
from app.gateway.risk import DEFAULT_THRESHOLDS, ReasonCode, RiskThresholds, assess_risk, result_for
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
        thresholds: RiskThresholds = DEFAULT_THRESHOLDS,
    ) -> None:
        self._registry = registry
        self._controls = tuple(controls)
        self._thresholds = thresholds

    def schemas(self) -> list[dict[str, Any]]:
        return self._registry.schemas()

    async def authorize(
        self,
        context: SecurityContext,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> FinalDecision:
        results: list[SecurityResult] = []
        if not self._registry.contains(tool_name):
            results.append(
                result_for(
                    control="tool-registry",
                    outcome="block",
                    reason=ReasonCode.UNKNOWN_TOOL,
                )
            )
        for control in self._controls:
            try:
                result = await control.evaluate(context, tool_name, arguments)
            except Exception:
                result = result_for(
                    control=control.name,
                    outcome="block",
                    reason=ReasonCode.SECURITY_CONTROL_FAILURE,
                    explanation=(
                        f"Security control {control.name} failed, so the gateway denied the "
                        "request safely."
                    ),
                )
            results.append(result)

        assessment = assess_risk(results, self._thresholds)
        if assessment.reason_codes:
            return FinalDecision(
                outcome="block",
                reason=assessment.reason_codes[0],
                results=tuple(results),
                risk_score=assessment.score,
                risk_level=assessment.level,
                reason_codes=assessment.reason_codes,
                explanation=assessment.explanation,
            )
        return FinalDecision(
            outcome="allow",
            reason="All configured security controls allowed the tool call",
            results=tuple(results),
            risk_score=assessment.score,
            risk_level=assessment.level,
            reason_codes=assessment.reason_codes,
            explanation=assessment.explanation,
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
