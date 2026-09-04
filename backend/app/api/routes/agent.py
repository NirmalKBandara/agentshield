from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import ValidationError

from app.agent.audit import ToolCallStore, get_tool_call_store
from app.agent.providers import ProviderError
from app.agent.schemas import AgentRunRequest, AgentRunResponse, ToolCallResponse
from app.agent.service import InvalidModelOutputError, ToolExecutionError, build_agent_service
from app.core.config import get_settings
from app.gateway import (
    SUPPORT_AGENT_ID,
    GatewayBlockedError,
    NetworkDestinationControl,
    PolicyLimitsControl,
    PromptInjectionControl,
    RiskThresholds,
    SensitiveDataControl,
    ToolGateway,
    ToolPermissionControl,
)
from app.gateway.permissions import PermissionStore, get_permission_store
from app.gateway.policies import PolicyRuleStore, get_policy_rule_store
from app.models import ToolCall
from app.tools.registry import UnknownToolError, default_tool_registry

router = APIRouter(prefix="/agent", tags=["agent"])
ToolCallStoreDependency = Annotated[ToolCallStore, Depends(get_tool_call_store)]
PermissionStoreDependency = Annotated[PermissionStore, Depends(get_permission_store)]
PolicyRuleStoreDependency = Annotated[PolicyRuleStore, Depends(get_policy_rule_store)]


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    payload: AgentRunRequest,
    request: Request,
    tool_call_store: ToolCallStoreDependency,
    permission_store: PermissionStoreDependency,
    policy_rule_store: PolicyRuleStoreDependency,
) -> AgentRunResponse:
    request_id = request.state.request_id
    try:
        gateway = ToolGateway(
            default_tool_registry,
            [
                PromptInjectionControl(),
                SensitiveDataControl(),
                NetworkDestinationControl(),
                ToolPermissionControl(permission_store),
                PolicyLimitsControl(policy_rule_store),
            ],
            thresholds=RiskThresholds(*get_settings().risk_threshold_values),
        )
        return await build_agent_service(
            tool_call_store, gateway=gateway, agent_id=SUPPORT_AGENT_ID
        ).run(payload.prompt, request_id)
    except InvalidModelOutputError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The model produced an invalid decision; no tool was executed",
        ) from exc
    except ProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The configured local model provider failed; no tool was executed",
        ) from exc
    except UnknownToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The selected tool arguments failed validation; no tool was executed",
        ) from exc
    except GatewayBlockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.decision.reason,
        ) from exc
    except ToolExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The selected tool failed; the attempt was recorded",
        ) from exc


@router.get("/tool-calls", response_model=list[ToolCallResponse])
async def list_tool_calls(
    tool_call_store: ToolCallStoreDependency,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ToolCall]:
    """Return the newest gateway tool execution attempts, including blocked calls."""
    return list(await tool_call_store.list_recent(limit))
