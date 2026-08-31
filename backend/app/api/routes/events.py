"""Security events and audit log API routes."""

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models import SecurityEvent, ToolCall

router = APIRouter(tags=["security"])


class SecurityEventResponse(BaseModel):
    """Stable public representation of a security event."""

    id: uuid.UUID
    event_type: str
    threat_category: str
    severity: str
    risk_level: str
    message: str
    reason: str
    risk_score: float
    tool_call_id: uuid.UUID | None
    tool: str | None
    decision: Literal["ALLOW", "BLOCK"] | None
    created_at: datetime
    details: dict[str, Any]


def _event_response(event: SecurityEvent) -> SecurityEventResponse:
    details = event.details or {}
    tool_call = event.tool_call
    tool = tool_call.tool_name if tool_call else details.get("tool")
    status = tool_call.status if tool_call else details.get("decision")

    decision: Literal["ALLOW", "BLOCK"] | None = None
    if isinstance(status, str):
        normalized_status = status.lower()
        if normalized_status in {"blocked", "block"}:
            decision = "BLOCK"
        elif normalized_status in {"succeeded", "allowed", "allow"}:
            decision = "ALLOW"
    if decision is None and event.event_type.endswith("_blocked"):
        decision = "BLOCK"

    reason = details.get("reason")
    if not isinstance(reason, str) or not reason:
        reason = event.message

    return SecurityEventResponse(
        id=event.id,
        event_type=event.event_type,
        threat_category=event.event_type,
        severity=event.severity,
        risk_level=event.severity,
        message=event.message,
        reason=reason,
        risk_score=float(event.risk_score),
        tool_call_id=event.tool_call_id,
        tool=tool if isinstance(tool, str) else None,
        decision=decision,
        created_at=event.created_at,
        details=details,
    )


@router.get("/api/v1/security-events", response_model=list[SecurityEventResponse])
async def list_security_events(
    session: Annotated[AsyncSession, Depends(get_session)],
    severity: Literal["low", "warning", "high", "critical"] | None = Query(None),
    event_type: str | None = Query(None, min_length=1, max_length=80),
    tool: str | None = Query(None, min_length=1, max_length=80),
    decision: Literal["allow", "block", "ALLOW", "BLOCK"] | None = Query(None),
    min_risk_score: float | None = Query(None, ge=0, le=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[SecurityEventResponse]:
    """List security events with optional filtering."""
    query = select(SecurityEvent).options(selectinload(SecurityEvent.tool_call))

    if severity:
        query = query.where(SecurityEvent.severity == severity)
    if event_type:
        query = query.where(SecurityEvent.event_type == event_type)
    if tool or decision:
        query = query.join(ToolCall, SecurityEvent.tool_call_id == ToolCall.id)
    if tool:
        query = query.where(ToolCall.tool_name == tool)
    if decision:
        status = "succeeded" if decision.lower() == "allow" else "blocked"
        query = query.where(ToolCall.status == status)
    if min_risk_score is not None:
        query = query.where(SecurityEvent.risk_score >= min_risk_score)

    query = (
        query.order_by(desc(SecurityEvent.created_at), desc(SecurityEvent.id))
        .offset(offset)
        .limit(limit)
    )
    events = await session.scalars(query)

    return [_event_response(event) for event in events]


@router.get("/api/v1/security-events/{event_id}", response_model=SecurityEventResponse)
async def get_security_event(
    event_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SecurityEventResponse:
    """Retrieve one security event for detailed inspection."""
    event = await session.scalar(
        select(SecurityEvent)
        .options(selectinload(SecurityEvent.tool_call))
        .where(SecurityEvent.id == event_id)
    )
    if event is None:
        raise HTTPException(status_code=404, detail="Security event not found")
    return _event_response(event)


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
