from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from app.tools.demo import fetch_url, get_customer, issue_refund, send_email
from app.tools.schemas import (
    FetchUrlArguments,
    GetCustomerArguments,
    IssueRefundArguments,
    SendEmailArguments,
)

ToolHandler = Callable[[Any], dict[str, Any]]


class UnknownToolError(ValueError):
    pass


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    arguments_model: type[BaseModel]
    handler: ToolHandler

    def public_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.arguments_model.model_json_schema(),
        }


class ToolRegistry:
    def __init__(self, definitions: list[ToolDefinition]) -> None:
        self._definitions = {definition.name: definition for definition in definitions}

    def schemas(self) -> list[dict[str, Any]]:
        return [definition.public_schema() for definition in self._definitions.values()]

    def contains(self, name: str) -> bool:
        return name in self._definitions

    def _execute(self, name: str, raw_arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute after gateway authorization; application code must use ToolGateway."""
        definition = self._definitions.get(name)
        if definition is None:
            raise UnknownToolError(f"Unknown tool: {name}")
        arguments = definition.arguments_model.model_validate(raw_arguments)
        return definition.handler(arguments)


default_tool_registry = ToolRegistry(
    [
        ToolDefinition(
            "get_customer",
            "Look up one fictional customer by four-digit demo ID.",
            GetCustomerArguments,
            get_customer,
        ),
        ToolDefinition(
            "send_email",
            "Simulate sending an email. No message leaves the application.",
            SendEmailArguments,
            send_email,
        ),
        ToolDefinition(
            "issue_refund",
            "Simulate a refund against a fictional demo order.",
            IssueRefundArguments,
            issue_refund,
        ),
        ToolDefinition(
            "fetch_url",
            "Read a response from the fixed AgentShield demo URL fixtures.",
            FetchUrlArguments,
            fetch_url,
        ),
    ]
)
