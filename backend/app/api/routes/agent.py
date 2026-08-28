from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import ValidationError

from app.agent.audit import ToolCallStore, get_tool_call_store
from app.agent.providers import ProviderError
from app.agent.schemas import AgentRunRequest, AgentRunResponse, ToolCallResponse
from app.agent.service import InvalidModelOutputError, ToolExecutionError, build_agent_service
from app.models import ToolCall
from app.tools.registry import UnknownToolError

router = APIRouter(prefix="/agent", tags=["agent"])
ToolCallStoreDependency = Annotated[ToolCallStore, Depends(get_tool_call_store)]


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    payload: AgentRunRequest,
    request: Request,
    tool_call_store: ToolCallStoreDependency,
) -> AgentRunResponse:
    request_id = request.state.request_id
    try:
        return await build_agent_service(tool_call_store).run(payload.prompt, request_id)
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
    """Return the newest pre-gateway tool execution attempts for the Week 1 review."""
    return list(await tool_call_store.list_recent(limit))
