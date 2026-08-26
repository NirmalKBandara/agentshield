from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "agentshield-api"


class ReadinessResponse(HealthResponse):
    database: Literal["connected"] = "connected"
