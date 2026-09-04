import asyncio
import time
from collections import defaultdict, deque
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any, Protocol

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.gateway.risk import ReasonCode, result_for
from app.gateway.schemas import SecurityContext, SecurityResult
from app.models import Policy


class PolicyRuleStore(Protocol):
    async def active_rules(self) -> Mapping[str, Any]: ...


class SqlAlchemyPolicyRuleStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def active_rules(self) -> Mapping[str, Any]:
        policies = await self.session.scalars(
            select(Policy).where(Policy.is_enabled.is_(True)).order_by(Policy.priority)
        )
        rules: dict[str, Any] = {}
        for policy in policies:
            rules.update(policy.rules or {})
        return rules


class FixedWindowRateLimiter:
    """Small single-process limiter suitable for the local MVP deployment."""

    def __init__(self, window_seconds: float = 60.0) -> None:
        self.window_seconds = window_seconds
        self._calls: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def consume(self, key: str, limit: int) -> bool:
        now = time.monotonic()
        async with self._lock:
            calls = self._calls[key]
            while calls and now - calls[0] >= self.window_seconds:
                calls.popleft()
            if len(calls) >= limit:
                return False
            calls.append(now)
            return True

    def reset(self) -> None:
        self._calls.clear()


policy_rate_limiter = FixedWindowRateLimiter()


class PolicyLimitsControl:
    name = "policy-limits"

    def __init__(
        self,
        store: PolicyRuleStore,
        rate_limiter: FixedWindowRateLimiter = policy_rate_limiter,
    ) -> None:
        self.store = store
        self.rate_limiter = rate_limiter

    async def evaluate(
        self,
        context: SecurityContext,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> SecurityResult:
        rules = await self.store.active_rules()

        if tool_name == "issue_refund" and "refund_limit" in rules:
            try:
                amount = Decimal(str(arguments.get("amount")))
                refund_limit = Decimal(str(rules["refund_limit"]))
            except (InvalidOperation, TypeError, ValueError):
                amount = refund_limit = Decimal("0")
            if amount > refund_limit:
                return result_for(
                    control=self.name,
                    outcome="block",
                    reason=ReasonCode.REFUND_LIMIT_EXCEEDED,
                )

        configured_rate = rules.get("rate_limit_per_minute")
        if isinstance(configured_rate, int) and configured_rate > 0:
            identity = str(context.agent_id) if context.agent_id else "anonymous"
            if not await self.rate_limiter.consume(identity, configured_rate):
                return result_for(
                    control=self.name,
                    outcome="block",
                    reason=ReasonCode.RATE_LIMIT_EXCEEDED,
                )

        return result_for(
            control=self.name,
            outcome="allow",
            reason="POLICY_LIMITS_SATISFIED",
        )


SessionDependency = Annotated[AsyncSession, Depends(get_session)]


async def get_policy_rule_store(session: SessionDependency) -> PolicyRuleStore:
    return SqlAlchemyPolicyRuleStore(session)
