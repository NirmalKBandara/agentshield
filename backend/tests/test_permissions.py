import uuid

import pytest

from app.gateway import GatewayBlockedError, SecurityContext, ToolGateway
from app.gateway.permissions import SUPPORT_AGENT_ID, ToolPermissionControl
from app.tools.registry import default_tool_registry


class StubPermissionStore:
    def __init__(self, permissions: dict[tuple[uuid.UUID, str], bool]) -> None:
        self.permissions = permissions

    async def is_allowed(self, agent_id: uuid.UUID, tool_name: str) -> bool:
        return self.permissions.get((agent_id, tool_name), False)


def permission_gateway(permissions: dict[tuple[uuid.UUID, str], bool]) -> ToolGateway:
    return ToolGateway(
        default_tool_registry,
        [ToolPermissionControl(StubPermissionStore(permissions))],
    )


@pytest.mark.asyncio
async def test_explicit_permission_allows_tool() -> None:
    gateway = permission_gateway({(SUPPORT_AGENT_ID, "get_customer"): True})

    decision, result = await gateway.execute(
        SecurityContext(request_id="permission-allow", agent_id=SUPPORT_AGENT_ID),
        "get_customer",
        {"customer_id": "1001"},
    )

    assert decision.allowed is True
    assert result["found"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("agent_id", "permissions"),
    [
        (SUPPORT_AGENT_ID, {(SUPPORT_AGENT_ID, "issue_refund"): False}),
        (SUPPORT_AGENT_ID, {}),
        (uuid.uuid4(), {(SUPPORT_AGENT_ID, "get_customer"): True}),
        (None, {(SUPPORT_AGENT_ID, "get_customer"): True}),
    ],
)
async def test_explicit_deny_and_missing_identity_or_permission_block(
    agent_id: uuid.UUID | None,
    permissions: dict[tuple[uuid.UUID, str], bool],
) -> None:
    gateway = permission_gateway(permissions)

    with pytest.raises(GatewayBlockedError) as blocked:
        await gateway.execute(
            SecurityContext(request_id="permission-block", agent_id=agent_id),
            "issue_refund" if agent_id == SUPPORT_AGENT_ID else "get_customer",
            {"order_id": "ORD-1002", "amount": 25}
            if agent_id == SUPPORT_AGENT_ID
            else {"customer_id": "1001"},
        )

    assert blocked.value.decision.reason == "TOOL_NOT_AUTHORIZED"
    assert blocked.value.decision.results[0].risk_score == 70
