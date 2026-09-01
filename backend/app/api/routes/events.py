"""Security events and audit log API routes."""

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models import Agent, SecurityEvent, ToolCall

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


ToolCallStatus = Literal["requested", "succeeded", "blocked", "failed"]
ToolCallDecision = Literal["PENDING", "ALLOW", "BLOCK", "ERROR"]


class ToolCallResponse(BaseModel):
    """Stable, secret-safe public representation of an audited tool call."""

    id: uuid.UUID
    request_id: str
    agent_id: uuid.UUID | None
    agent_name: str | None
    tool_name: str
    status: str
    decision: ToolCallDecision
    risk_score: float = Field(ge=0, le=100)
    duration_ms: int | None
    created_at: datetime
    arguments: dict[str, Any]
    result: dict[str, Any] | None
    security_event_id: uuid.UUID | None


_MASK = "***MASKED***"
_SENSITIVE_ARGUMENT_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "card_number",
    "credit_card",
    "cvc",
    "cvv",
    "password",
    "passwd",
    "pin",
    "private_key",
    "refresh_token",
    "secret",
    "token",
    "access_token",
}


def _is_sensitive_argument_key(key: object) -> bool:
    normalized = str(key).strip().lower().replace("-", "_").replace(" ", "_")
    return normalized in _SENSITIVE_ARGUMENT_KEYS or normalized.endswith(
        ("_password", "_secret", "_token", "_api_key", "_card_number")
    )


def _sanitize_argument_value(value: Any) -> Any:
    """Return a recursively copied value with secret-bearing fields masked."""
    if isinstance(value, Mapping):
        return {
            str(key): _MASK if _is_sensitive_argument_key(key) else _sanitize_argument_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_sanitize_argument_value(item) for item in value]
    return value


def _tool_call_decision(status: str) -> ToolCallDecision:
    normalized = status.lower()
    if normalized in {"succeeded", "allowed", "allow"}:
        return "ALLOW"
    if normalized in {"blocked", "block"}:
        return "BLOCK"
    if normalized in {"failed", "error"}:
        return "ERROR"
    return "PENDING"


def _linked_security_event(tool_call: ToolCall) -> SecurityEvent | None:
    events = tool_call.security_events
    if not events:
        return None
    return max(
        events,
        key=lambda event: (float(event.risk_score), event.created_at, event.id.hex),
    )


def _tool_call_response(tool_call: ToolCall) -> ToolCallResponse:
    security_event = _linked_security_event(tool_call)
    risk_score = float(security_event.risk_score) if security_event else 0.0

    return ToolCallResponse(
        id=tool_call.id,
        request_id=tool_call.request_id,
        agent_id=tool_call.agent_id,
        agent_name=tool_call.agent.name if tool_call.agent else None,
        tool_name=tool_call.tool_name,
        status=tool_call.status,
        decision=_tool_call_decision(tool_call.status),
        risk_score=risk_score,
        duration_ms=tool_call.duration_ms,
        created_at=tool_call.created_at,
        arguments=_sanitize_argument_value(tool_call.arguments),
        result=tool_call.result,
        security_event_id=security_event.id if security_event else None,
    )


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
    tool_call_id: uuid.UUID | None = None,
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
    if tool_call_id is not None:
        query = query.where(SecurityEvent.tool_call_id == tool_call_id)

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


@router.get("/api/v1/tool-calls", response_model=list[ToolCallResponse])
async def list_all_tool_calls(
    session: Annotated[AsyncSession, Depends(get_session)],
    status: ToolCallStatus | None = None,
    decision: Literal["allow", "block", "ALLOW", "BLOCK"] | None = Query(None),
    tool_name: str | None = Query(None, min_length=1, max_length=80),
    tool: str | None = Query(None, min_length=1, max_length=80),
    agent_id: uuid.UUID | None = None,
    agent: str | None = Query(None, min_length=1, max_length=120),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ToolCallResponse]:
    """List auditable tool calls without exposing sensitive argument values."""
    if tool_name and tool and tool_name != tool:
        raise HTTPException(status_code=422, detail="tool and tool_name filters must match")
    if status and decision:
        decision_status = "succeeded" if decision.lower() == "allow" else "blocked"
        if status != decision_status:
            raise HTTPException(status_code=422, detail="status and decision filters must match")

    query = select(ToolCall).options(
        selectinload(ToolCall.agent), selectinload(ToolCall.security_events)
    )

    if status:
        query = query.where(ToolCall.status == status)
    if decision:
        decision_status = "succeeded" if decision.lower() == "allow" else "blocked"
        query = query.where(ToolCall.status == decision_status)
    selected_tool = tool_name or tool
    if selected_tool:
        query = query.where(ToolCall.tool_name == selected_tool)
    if agent_id:
        query = query.where(ToolCall.agent_id == agent_id)
    if agent:
        query = query.join(Agent, ToolCall.agent_id == Agent.id).where(Agent.name == agent)

    query = query.order_by(desc(ToolCall.created_at), desc(ToolCall.id)).offset(offset).limit(limit)
    tool_calls = await session.scalars(query)

    return [_tool_call_response(tool_call) for tool_call in tool_calls]
