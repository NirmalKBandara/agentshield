import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import SecurityEvent
from app.red_team.service import SCENARIOS, SCENARIOS_BY_ID, RedTeamScenario, run_scenario

router = APIRouter(prefix="/red-team", tags=["red-team"])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]


class ScenarioResponse(BaseModel):
    id: str
    name: str
    category: str
    description: str
    payload: dict[str, Any]
    requested_action: dict[str, Any]


class RunRequest(BaseModel):
    scenario_id: str = Field(min_length=1, max_length=80)


class RunResponse(BaseModel):
    security_event_id: uuid.UUID
    request_id: str
    scenario_id: str
    payload: dict[str, Any]
    requested_action: dict[str, Any]
    triggered_controls: list[str]
    reason: str
    score: int
    decision: Literal["block"]
    created_at: datetime


def _scenario_response(scenario: RedTeamScenario) -> ScenarioResponse:
    return ScenarioResponse(
        id=scenario.id,
        name=scenario.name,
        category=scenario.category,
        description=scenario.description,
        payload=scenario.payload,
        requested_action=scenario.requested_action,
    )


@router.get("/scenarios", response_model=list[ScenarioResponse])
async def list_scenarios() -> list[ScenarioResponse]:
    return [_scenario_response(scenario) for scenario in SCENARIOS]


@router.post("/run", response_model=RunResponse)
async def run_attack(
    payload: RunRequest,
    request: Request,
    session: SessionDependency,
) -> RunResponse:
    scenario = SCENARIOS_BY_ID.get(payload.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Red-team scenario not found")

    result = await run_scenario(scenario, request.state.request_id)
    event = SecurityEvent(
        event_type="red_team_attack_blocked",
        severity="critical" if result.score >= 90 else "high",
        message=result.decision.reason,
        details={
            "request_id": request.state.request_id,
            "scenario_id": scenario.id,
            "category": scenario.category,
            "payload": scenario.payload,
            "requested_action": scenario.requested_action,
            "triggered_controls": result.triggered_controls,
            "decision": result.decision.outcome.upper(),
        },
        risk_score=result.score,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return RunResponse(
        security_event_id=event.id,
        request_id=request.state.request_id,
        scenario_id=scenario.id,
        payload=scenario.payload,
        requested_action=scenario.requested_action,
        triggered_controls=result.triggered_controls,
        reason=result.decision.reason,
        score=result.score,
        decision=result.decision.outcome,
        created_at=event.created_at,
    )
