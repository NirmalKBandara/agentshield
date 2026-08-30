"""Security events and audit log API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import SecurityEvent, ToolCall

router = APIRouter(tags=["security"])


@router.get("/api/v1/security-events", response_model=list[dict])
async def list_security_events(
    session: Annotated[AsyncSession, Depends(get_session)],
    severity: str | None = Query(None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict]:
    """List security events with optional filtering."""
    query = select(SecurityEvent).order_by(desc(SecurityEvent.created_at))

    if severity:
        query = query.where(SecurityEvent.severity == severity)

    query = query.limit(limit)
    events = await session.scalars(query)

    return [
        {
            "id": str(event.id),
            "event_type": event.event_type,
            "severity": event.severity,
            "message": event.message,
            "risk_score": float(event.risk_score),
            "tool_call_id": str(event.tool_call_id) if event.tool_call_id else None,
            "created_at": event.created_at.isoformat(),
            "details": event.details,
        }
        for event in events
    ]


@router.get("/api/v1/tool-calls", response_model=list[dict])
async def list_all_tool_calls(
    session: Annotated[AsyncSession, Depends(get_session)],
    status: str | None = Query(None),
    tool_name: str | None = Query(None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict]:
    """List tool calls with optional filtering by status or tool."""
    query = select(ToolCall).order_by(desc(ToolCall.created_at))

    if status:
        query = query.where(ToolCall.status == status)
    if tool_name:
        query = query.where(ToolCall.tool_name == tool_name)

    query = query.limit(limit)
    tool_calls = await session.scalars(query)

    return [
        {
            "id": str(tool_call.id),
            "request_id": tool_call.request_id,
            "agent_id": str(tool_call.agent_id) if tool_call.agent_id else None,
            "tool_name": tool_call.tool_name,
            "status": tool_call.status,
            "duration_ms": tool_call.duration_ms,
            "created_at": tool_call.created_at.isoformat(),
            "arguments": tool_call.arguments,
            "result": tool_call.result,
        }
        for tool_call in tool_calls
    ]
