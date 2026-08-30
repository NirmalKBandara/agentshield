"""Dashboard and analytics API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import SecurityEvent, ToolCall

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardSummary:
    def __init__(
        self,
        total_requests: int,
        allowed_requests: int,
        blocked_requests: int,
        high_risk_events: int,
        critical_events: int,
        most_attacked_tool: str | None,
        most_common_attack: str | None,
    ):
        self.total_requests = total_requests
        self.allowed_requests = allowed_requests
        self.blocked_requests = blocked_requests
        self.high_risk_events = high_risk_events
        self.critical_events = critical_events
        self.most_attacked_tool = most_attacked_tool
        self.most_common_attack = most_common_attack

    def dict(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "allowed_requests": self.allowed_requests,
            "blocked_requests": self.blocked_requests,
            "high_risk_events": self.high_risk_events,
            "critical_events": self.critical_events,
            "most_attacked_tool": self.most_attacked_tool,
            "most_common_attack": self.most_common_attack,
        }


@router.get("/summary", response_model=dict)
async def get_dashboard_summary(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Get dashboard summary statistics."""

    # Total requests
    total_requests = await session.scalar(select(func.count(ToolCall.id)))

    # Allowed vs blocked
    allowed_requests = await session.scalar(
        select(func.count(ToolCall.id)).where(ToolCall.status == "succeeded")
    )
    blocked_requests = await session.scalar(
        select(func.count(ToolCall.id)).where(ToolCall.status == "blocked")
    )

    # High-risk events
    high_risk_events = await session.scalar(
        select(func.count(SecurityEvent.id)).where(SecurityEvent.severity.in_(["high"]))
    )

    # Critical events
    critical_events = await session.scalar(
        select(func.count(SecurityEvent.id)).where(SecurityEvent.severity.in_(["critical"]))
    )

    # Most attacked tool
    most_attacked = await session.scalar(
        select(ToolCall.tool_name)
        .where(ToolCall.status == "blocked")
        .group_by(ToolCall.tool_name)
        .order_by(func.count(ToolCall.id).desc())
        .limit(1)
    )

    # Most common attack category
    most_common_attack = await session.scalar(
        select(SecurityEvent.event_type)
        .group_by(SecurityEvent.event_type)
        .order_by(func.count(SecurityEvent.id).desc())
        .limit(1)
    )

    summary = DashboardSummary(
        total_requests=total_requests or 0,
        allowed_requests=allowed_requests or 0,
        blocked_requests=blocked_requests or 0,
        high_risk_events=high_risk_events or 0,
        critical_events=critical_events or 0,
        most_attacked_tool=most_attacked,
        most_common_attack=most_common_attack,
    )

    return summary.dict()


@router.get("/recent-events", response_model=list[dict])
async def get_recent_security_events(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 20,
) -> list[dict]:
    """Get recent security events."""
    events = await session.scalars(
        select(SecurityEvent).order_by(SecurityEvent.created_at.desc()).limit(limit)
    )

    return [
        {
            "id": str(event.id),
            "event_type": event.event_type,
            "severity": event.severity,
            "message": event.message,
            "risk_score": float(event.risk_score),
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]
