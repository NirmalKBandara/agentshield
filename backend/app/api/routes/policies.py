import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.models import AgentPermission, Policy, PolicyAuditLog

router = APIRouter(prefix="/policies", tags=["policies"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]


class PolicyResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    refund_limit: float
    rate_limit_per_minute: int
    priority: int
    is_enabled: bool
    updated_at: datetime


class PermissionResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    agent_name: str
    tool_id: uuid.UUID
    tool_name: str
    allowed: bool
    updated_at: datetime


class PolicyAuditResponse(BaseModel):
    id: uuid.UUID
    request_id: str
    actor: str
    action: str
    resource_type: str
    resource_id: uuid.UUID
    before: dict[str, Any]
    after: dict[str, Any]
    created_at: datetime


class PolicyOverviewResponse(BaseModel):
    policies: list[PolicyResponse]
    permissions: list[PermissionResponse]
    recent_changes: list[PolicyAuditResponse]


class PolicyUpdate(BaseModel):
    refund_limit: float | None = Field(default=None, gt=0, le=10_000)
    rate_limit_per_minute: int | None = Field(default=None, ge=1, le=1_000)

    @model_validator(mode="after")
    def contains_change(self) -> "PolicyUpdate":
        if self.refund_limit is None and self.rate_limit_per_minute is None:
            raise ValueError("At least one policy setting is required")
        return self


class PermissionUpdate(BaseModel):
    allowed: bool


def _policy_response(policy: Policy) -> PolicyResponse:
    rules = policy.rules or {}
    return PolicyResponse(
        id=policy.id,
        name=policy.name,
        description=policy.description,
        refund_limit=float(rules.get("refund_limit", 100)),
        rate_limit_per_minute=int(rules.get("rate_limit_per_minute", 30)),
        priority=policy.priority,
        is_enabled=policy.is_enabled,
        updated_at=policy.updated_at,
    )


def _permission_response(permission: AgentPermission) -> PermissionResponse:
    return PermissionResponse(
        id=permission.id,
        agent_id=permission.agent_id,
        agent_name=permission.agent.name,
        tool_id=permission.tool_id,
        tool_name=permission.tool.name,
        allowed=permission.allowed,
        updated_at=permission.updated_at,
    )


def _audit_response(audit: PolicyAuditLog) -> PolicyAuditResponse:
    return PolicyAuditResponse.model_validate(audit, from_attributes=True)


def _audit(
    *,
    request: Request,
    actor: str,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID,
    before: dict[str, Any],
    after: dict[str, Any],
) -> PolicyAuditLog:
    return PolicyAuditLog(
        request_id=request.state.request_id,
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before=before,
        after=after,
    )


@router.get("", response_model=PolicyOverviewResponse)
async def list_policies(session: SessionDependency) -> PolicyOverviewResponse:
    policies = list(await session.scalars(select(Policy).order_by(Policy.priority, Policy.name)))
    permissions = list(
        await session.scalars(
            select(AgentPermission)
            .options(selectinload(AgentPermission.agent), selectinload(AgentPermission.tool))
            .order_by(AgentPermission.agent_id, AgentPermission.tool_id)
        )
    )
    audits = list(
        await session.scalars(
            select(PolicyAuditLog)
            .order_by(desc(PolicyAuditLog.created_at), desc(PolicyAuditLog.id))
            .limit(20)
        )
    )
    return PolicyOverviewResponse(
        policies=[_policy_response(policy) for policy in policies],
        permissions=[_permission_response(permission) for permission in permissions],
        recent_changes=[_audit_response(audit) for audit in audits],
    )


@router.patch("/{policy_id}/limits", response_model=PolicyResponse)
async def update_policy(
    policy_id: uuid.UUID,
    payload: PolicyUpdate,
    request: Request,
    session: SessionDependency,
    actor: Annotated[str, Header(alias="X-Actor", min_length=1, max_length=120)] = (
        "dashboard-user"
    ),
) -> PolicyResponse:
    policy = await session.scalar(select(Policy).where(Policy.id == policy_id))
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    before = dict(policy.rules or {})
    after = dict(before)
    if payload.refund_limit is not None:
        after["refund_limit"] = payload.refund_limit
    if payload.rate_limit_per_minute is not None:
        after["rate_limit_per_minute"] = payload.rate_limit_per_minute

    if after != before:
        policy.rules = after
        session.add(
            _audit(
                request=request,
                actor=actor,
                action="policy_limits_updated",
                resource_type="policy",
                resource_id=policy.id,
                before=before,
                after=after,
            )
        )
        await session.commit()
        await session.refresh(policy)
    return _policy_response(policy)


@router.patch("/permissions/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: uuid.UUID,
    payload: PermissionUpdate,
    request: Request,
    session: SessionDependency,
    actor: Annotated[str, Header(alias="X-Actor", min_length=1, max_length=120)] = (
        "dashboard-user"
    ),
) -> PermissionResponse:
    permission = await session.scalar(
        select(AgentPermission)
        .options(selectinload(AgentPermission.agent), selectinload(AgentPermission.tool))
        .where(AgentPermission.id == permission_id)
    )
    if permission is None:
        raise HTTPException(status_code=404, detail="Tool permission not found")

    before = {"allowed": permission.allowed}
    after = {"allowed": payload.allowed}
    if after != before:
        permission.allowed = payload.allowed
        session.add(
            _audit(
                request=request,
                actor=actor,
                action="tool_permission_updated",
                resource_type="agent_permission",
                resource_id=permission.id,
                before=before,
                after={**after, "agent": permission.agent.name, "tool": permission.tool.name},
            )
        )
        await session.commit()
        await session.refresh(permission)
    return _permission_response(permission)
