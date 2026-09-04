import uuid
from typing import Annotated, Any, Protocol

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.gateway.risk import ReasonCode, result_for
from app.gateway.schemas import SecurityContext, SecurityResult
from app.models import Agent, AgentPermission, Tool

SUPPORT_AGENT_ID = uuid.UUID("a9e17000-0000-4000-8000-000000000001")


class PermissionStore(Protocol):
    async def is_allowed(self, agent_id: uuid.UUID, tool_name: str) -> bool: ...


class SqlAlchemyPermissionStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def is_allowed(self, agent_id: uuid.UUID, tool_name: str) -> bool:
        allowed = await self.session.scalar(
            select(AgentPermission.allowed)
            .join(Agent, Agent.id == AgentPermission.agent_id)
            .join(Tool, Tool.id == AgentPermission.tool_id)
            .where(
                AgentPermission.agent_id == agent_id,
                Agent.is_active.is_(True),
                Tool.name == tool_name,
                Tool.is_enabled.is_(True),
            )
        )
        return allowed is True


class ToolPermissionControl:
    name = "tool-permission"

    def __init__(self, store: PermissionStore) -> None:
        self.store = store

    async def evaluate(
        self,
        context: SecurityContext,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> SecurityResult:
        if context.agent_id is not None and await self.store.is_allowed(
            context.agent_id, tool_name
        ):
            return result_for(
                control=self.name,
                outcome="allow",
                reason="TOOL_AUTHORIZED",
            )
        return result_for(
            control=self.name,
            outcome="block",
            reason=ReasonCode.TOOL_NOT_AUTHORIZED,
        )


SessionDependency = Annotated[AsyncSession, Depends(get_session)]


async def get_permission_store(session: SessionDependency) -> PermissionStore:
    return SqlAlchemyPermissionStore(session)
