from collections.abc import Sequence
from typing import Annotated, Any, Protocol

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import ToolCall


class ToolCallStore(Protocol):
    async def record(
        self,
        *,
        request_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any] | None,
        status: str,
        duration_ms: int,
    ) -> ToolCall: ...

    async def list_recent(self, limit: int) -> Sequence[ToolCall]: ...


class SqlAlchemyToolCallStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        request_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any] | None,
        status: str,
        duration_ms: int,
    ) -> ToolCall:
        tool_call = ToolCall(
            request_id=request_id,
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

    async def list_recent(self, limit: int) -> Sequence[ToolCall]:
        rows = await self.session.scalars(
            select(ToolCall).order_by(ToolCall.created_at.desc()).limit(limit)
        )
        return list(rows)


SessionDependency = Annotated[AsyncSession, Depends(get_session)]


async def get_tool_call_store(session: SessionDependency) -> ToolCallStore:
    return SqlAlchemyToolCallStore(session)
