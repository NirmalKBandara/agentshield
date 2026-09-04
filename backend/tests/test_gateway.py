from typing import Any

import pytest

from app.gateway import GatewayBlockedError, SecurityContext, SecurityResult, ToolGateway
from app.tools.registry import default_tool_registry


class BlockingControl:
    name = "test-block"

    async def evaluate(
        self, context: SecurityContext, tool_name: str, arguments: dict[str, Any]
    ) -> SecurityResult:
        return SecurityResult(control=self.name, outcome="block", reason="Denied by test")


class BrokenControl:
    name = "test-broken"

    async def evaluate(
        self, context: SecurityContext, tool_name: str, arguments: dict[str, Any]
    ) -> SecurityResult:
        raise RuntimeError("control unavailable")


@pytest.mark.asyncio
async def test_gateway_returns_final_allow_decision_before_execution() -> None:
    gateway = ToolGateway(default_tool_registry)

    decision, result = await gateway.execute(
        SecurityContext(request_id="gateway-allow"),
        "get_customer",
        {"customer_id": "1001"},
    )

    assert decision.outcome == "allow"
    assert result["found"] is True


@pytest.mark.asyncio
async def test_gateway_does_not_invoke_tool_after_block(monkeypatch) -> None:
    gateway = ToolGateway(default_tool_registry, [BlockingControl()])
    invoked = False

    def unexpected_execution(*args) -> None:
        nonlocal invoked
        invoked = True

    monkeypatch.setattr(default_tool_registry, "_execute", unexpected_execution)

    with pytest.raises(GatewayBlockedError) as blocked:
        await gateway.execute(
            SecurityContext(request_id="gateway-block"),
            "get_customer",
            {"customer_id": "1001"},
        )

    assert blocked.value.decision.outcome == "block"
    assert invoked is False


@pytest.mark.asyncio
async def test_gateway_fails_closed_when_control_errors() -> None:
    gateway = ToolGateway(default_tool_registry, [BrokenControl()])

    with pytest.raises(GatewayBlockedError) as blocked:
        await gateway.execute(
            SecurityContext(request_id="gateway-error"),
            "get_customer",
            {"customer_id": "1001"},
        )

    assert blocked.value.decision.results[0].risk_score == 100
    assert blocked.value.decision.reason == "SECURITY_CONTROL_FAILURE"
    assert "failed" in blocked.value.decision.explanation
    assert blocked.value.decision.risk_level == "critical"


@pytest.mark.asyncio
async def test_unknown_tool_is_blocked_before_execution() -> None:
    gateway = ToolGateway(default_tool_registry)

    with pytest.raises(GatewayBlockedError) as blocked:
        await gateway.execute(
            SecurityContext(request_id="unknown-tool"),
            "delete_database",
            {},
        )

    assert blocked.value.decision.reason_codes == ("UNKNOWN_TOOL",)
    assert blocked.value.decision.risk_score == 50
    assert blocked.value.decision.risk_level == "medium"
