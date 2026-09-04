import uuid

import pytest

from app.gateway.policies import FixedWindowRateLimiter, PolicyLimitsControl
from app.gateway.schemas import SecurityContext


class StubPolicyRuleStore:
    def __init__(self, rules):
        self.rules = rules

    async def active_rules(self):
        return self.rules


@pytest.mark.asyncio
async def test_refund_above_configured_limit_is_blocked() -> None:
    control = PolicyLimitsControl(
        StubPolicyRuleStore({"refund_limit": 100.0, "rate_limit_per_minute": 10}),
        FixedWindowRateLimiter(),
    )

    result = await control.evaluate(
        SecurityContext(request_id="refund-policy", agent_id=uuid.uuid4()),
        "issue_refund",
        {"amount": "100.01"},
    )

    assert result.outcome == "block"
    assert result.reason == "REFUND_LIMIT_EXCEEDED"
    assert result.risk_score == 40
    assert "configured policy limit" in result.explanation


@pytest.mark.asyncio
async def test_configured_rate_limit_blocks_excess_call() -> None:
    agent_id = uuid.uuid4()
    control = PolicyLimitsControl(
        StubPolicyRuleStore({"refund_limit": 100.0, "rate_limit_per_minute": 1}),
        FixedWindowRateLimiter(window_seconds=60),
    )
    context = SecurityContext(request_id="rate-policy", agent_id=agent_id)

    allowed = await control.evaluate(context, "get_customer", {"customer_id": "1001"})
    blocked = await control.evaluate(context, "get_customer", {"customer_id": "1001"})

    assert allowed.outcome == "allow"
    assert blocked.outcome == "block"
    assert blocked.reason == "RATE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_missing_limits_leave_call_allowed() -> None:
    control = PolicyLimitsControl(StubPolicyRuleStore({}), FixedWindowRateLimiter())

    result = await control.evaluate(
        SecurityContext(request_id="no-policy"),
        "issue_refund",
        {"amount": "5000"},
    )

    assert result.outcome == "allow"
