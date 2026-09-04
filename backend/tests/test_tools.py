from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.gateway import GatewayBlockedError, SecurityContext, ToolGateway
from app.tools.registry import default_tool_registry

gateway = ToolGateway(default_tool_registry)
context = SecurityContext(request_id="tool-test")


async def test_get_customer_returns_only_demo_record() -> None:
    _, result = await gateway.execute(context, "get_customer", {"customer_id": "1002"})
    assert result == {
        "found": True,
        "customer": {"id": "1002", "name": "Morgan Silva", "tier": "premium"},
    }


async def test_send_email_is_simulated() -> None:
    _, result = await gateway.execute(
        context,
        "send_email", {"to": "demo@example.test", "message": "Hello from a test"}
    )
    assert result["accepted"] is True
    assert result["delivery"] == "simulated"


async def test_issue_refund_is_simulated_and_bounded() -> None:
    _, result = await gateway.execute(
        context,
        "issue_refund", {"order_id": "ORD-1002", "amount": Decimal("25.00")}
    )
    assert result == {
        "issued": True,
        "processing": "simulated",
        "order_id": "ORD-1002",
        "amount": "25.00",
    }


async def test_fetch_url_uses_fixture_without_network_access() -> None:
    _, result = await gateway.execute(
        context,
        "fetch_url", {"url": "https://docs.agentshield.local/"}
    )
    assert result["fetched"] is True
    assert result["status_code"] == 200


@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    [
        ("get_customer", {"customer_id": "../../etc/passwd"}),
        ("send_email", {"to": "not-an-email", "message": "hello"}),
        ("issue_refund", {"order_id": "ORD-1002", "amount": -1}),
        ("fetch_url", {"url": "not-a-url"}),
    ],
)
async def test_invalid_arguments_never_reach_tool(tool_name: str, arguments: dict) -> None:
    with pytest.raises(ValidationError):
        await gateway.execute(context, tool_name, arguments)


async def test_unknown_tool_cannot_execute() -> None:
    with pytest.raises(GatewayBlockedError, match="UNKNOWN_TOOL") as blocked:
        await gateway.execute(context, "delete_database", {})
    assert blocked.value.decision.risk_score == 50


def test_registry_exposes_json_schemas() -> None:
    schemas = default_tool_registry.schemas()
    assert {schema["name"] for schema in schemas} == {
        "get_customer", "send_email", "issue_refund", "fetch_url"
    }
    assert all(schema["input_schema"]["additionalProperties"] is False for schema in schemas)
