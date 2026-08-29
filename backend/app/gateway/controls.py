from typing import Any, Protocol

from app.gateway.schemas import SecurityContext, SecurityResult


class SecurityControl(Protocol):
    """One independently testable check in the gateway decision pipeline."""

    name: str

    async def evaluate(
        self,
        context: SecurityContext,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> SecurityResult: ...
