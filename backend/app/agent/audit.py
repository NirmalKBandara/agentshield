import uuid
from collections.abc import Sequence
from decimal import Decimal
from typing import Annotated, Any, Protocol

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import SecurityEvent, ToolCall


class ToolCallStore(Protocol):
    async def record(
        self,
        *,
        request_id: str,
        agent_id: uuid.UUID | None,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any] | None,
        status: str,
        duration_ms: int,
    ) -> ToolCall: ...

    async def record_blocked_event(
        self,
        *,
        tool_call_id: uuid.UUID,
        request_id: str,
        agent_id: uuid.UUID | None,
        tool_name: str,
        reason: str,
        risk_score: int,
    ) -> SecurityEvent: ...

    async def list_recent(self, limit: int) -> Sequence[ToolCall]: ...


class SqlAlchemyToolCallStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        request_id: str,
        agent_id: uuid.UUID | None,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any] | None,
        status: str,
        duration_ms: int,
    ) -> ToolCall:
        tool_call = ToolCall(
            request_id=request_id,
            agent_id=agent_id,
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            status=status,
            duration_ms=duration_ms,
        )
        self.session.add(tool_call)
        await self.session.commit()
        await self.session.refresh(tool_call)
        return tool_call

    async def record_blocked_event(
        self,
        *,
        tool_call_id: uuid.UUID,
        request_id: str,
        agent_id: uuid.UUID | None,
        tool_name: str,
        reason: str,
        risk_score: int,
    ) -> SecurityEvent:
        event = SecurityEvent(
            tool_call_id=tool_call_id,
            event_type="tool_call_blocked",
            severity="warning",
            message=reason,
            details={
                "request_id": request_id,
                "agent_id": str(agent_id) if agent_id else None,
                "tool": tool_name,
                "reason": reason,
            },
            risk_score=Decimal(risk_score),
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def list_recent(self, limit: int) -> Sequence[ToolCall]:
        rows = await self.session.scalars(
            select(ToolCall).order_by(ToolCall.created_at.desc()).limit(limit)
        )
        return list(rows)


SessionDependency = Annotated[AsyncSession, Depends(get_session)]


async def get_tool_call_store(session: SessionDependency) -> ToolCallStore:
    return SqlAlchemyToolCallStore(session)
