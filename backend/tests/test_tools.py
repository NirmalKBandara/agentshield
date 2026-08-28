from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.tools.registry import UnknownToolError, default_tool_registry


def test_get_customer_returns_only_demo_record() -> None:
    result = default_tool_registry.execute("get_customer", {"customer_id": "1002"})
    assert result == {
        "found": True,
        "customer": {"id": "1002", "name": "Morgan Silva", "tier": "premium"},
    }


def test_send_email_is_simulated() -> None:
    result = default_tool_registry.execute(
        "send_email", {"to": "demo@example.test", "message": "Hello from a test"}
    )
    assert result["accepted"] is True
    assert result["delivery"] == "simulated"


def test_issue_refund_is_simulated_and_bounded() -> None:
    result = default_tool_registry.execute(
        "issue_refund", {"order_id": "ORD-1002", "amount": Decimal("25.00")}
    )
    assert result == {
        "issued": True,
        "processing": "simulated",
        "order_id": "ORD-1002",
        "amount": "25.00",
    }


def test_fetch_url_uses_fixture_without_network_access() -> None:
    result = default_tool_registry.execute(
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
def test_invalid_arguments_never_reach_tool(tool_name: str, arguments: dict) -> None:
    with pytest.raises(ValidationError):
        default_tool_registry.execute(tool_name, arguments)


def test_unknown_tool_cannot_execute() -> None:
    with pytest.raises(UnknownToolError, match="Unknown tool"):
        default_tool_registry.execute("delete_database", {})


def test_registry_exposes_json_schemas() -> None:
    schemas = default_tool_registry.schemas()
    assert {schema["name"] for schema in schemas} == {
        "get_customer", "send_email", "issue_refund", "fetch_url"
    }
    assert all(schema["input_schema"]["additionalProperties"] is False for schema in schemas)
