import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SecurityContext(BaseModel):
    """Trusted request identity and correlation data supplied to every control."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1, max_length=128)
    agent_id: uuid.UUID | None = None
    user_prompt: str = Field(default="", max_length=4000)


class SecurityResult(BaseModel):
    """The normalized result returned by one security control."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    control: str = Field(min_length=1, max_length=80)
    outcome: Literal["allow", "block"]
    reason: str = Field(min_length=1, max_length=500)
    risk_score: int = Field(default=0, ge=0, le=100)


class FinalDecision(BaseModel):
    """The gateway's authoritative decision after all controls have run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: Literal["allow", "block"]
    reason: str = Field(min_length=1, max_length=500)
    results: tuple[SecurityResult, ...] = ()

    @property
    def allowed(self) -> bool:
        return self.outcome == "allow"
