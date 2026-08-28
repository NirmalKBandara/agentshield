import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["tool", "respond"]
    tool_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    response: str | None = None

    @model_validator(mode="after")
    def enforce_action_shape(self) -> "AgentDecision":
        if self.action == "tool" and (not self.tool_name or self.response is not None):
            raise ValueError("tool decisions require tool_name and may not include response")
        if self.action == "respond" and (self.response is None or self.tool_name is not None):
            raise ValueError("respond decisions require response and may not include tool_name")
        if self.action == "respond" and self.arguments:
            raise ValueError("respond decisions may not include tool arguments")
        return self


class AgentRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    prompt: str = Field(min_length=1, max_length=4000)


class AgentRunResponse(BaseModel):
    status: Literal["completed"] = "completed"
    decision: AgentDecision
    tool_result: dict[str, Any] | None = None
    provider: str
    request_id: str
    tool_call_id: uuid.UUID | None = None


class ToolCallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    request_id: str
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None
    status: str
    duration_ms: int | None
    created_at: datetime
