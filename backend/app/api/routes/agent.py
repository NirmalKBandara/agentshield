from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from app.agent.providers import ProviderError
from app.agent.schemas import AgentRunRequest, AgentRunResponse
from app.agent.service import InvalidModelOutputError, build_agent_service
from app.tools.registry import UnknownToolError

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(request: AgentRunRequest) -> AgentRunResponse:
    try:
        return await build_agent_service().run(request.prompt)
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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The selected tool arguments failed validation; no tool was executed",
        ) from exc
