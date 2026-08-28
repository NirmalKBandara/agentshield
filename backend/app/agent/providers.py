import json
import re
from typing import Any, Protocol

import httpx

from app.core.config import Settings

SYSTEM_INSTRUCTIONS = """You are the demo AgentShield tool router.
Choose at most one supplied tool. Never invent a tool or argument.
Return JSON only using one of these exact shapes:
{"action":"tool","tool_name":"name","arguments":{...}}
{"action":"respond","arguments":{},"response":"message"}
Do not wrap JSON in Markdown. The tool layer validates every argument."""


class AgentProvider(Protocol):
    name: str

    async def decide(self, prompt: str, tool_schemas: list[dict[str, Any]]) -> str: ...


class ProviderError(RuntimeError):
    """A local model provider failed before a decision could be validated."""


class RuleBasedLocalProvider:
    """Deterministic, offline MVP provider used by default and in CI."""

    name = "local-rules"

    async def decide(self, prompt: str, tool_schemas: list[dict[str, Any]]) -> str:
        del tool_schemas
        customer = re.search(r"(?:customer|customer_id)\s*(?:#|id|is|=|:)?\s*(\d{4})", prompt, re.I)
        if customer:
            return json.dumps(
                {
                    "action": "tool",
                    "tool_name": "get_customer",
                    "arguments": {"customer_id": customer.group(1)},
                }
            )

        refund = re.search(
            r"refund(?:\s+order)?\s+(ORD-\d{4}).*?(?:\$|amount\s*)?(\d+(?:\.\d{1,2})?)",
            prompt,
            re.I,
        )
        if refund:
            return json.dumps(
                {
                    "action": "tool",
                    "tool_name": "issue_refund",
                    "arguments": {"order_id": refund.group(1).upper(), "amount": refund.group(2)},
                }
            )

        email_pattern = r"(?:email|send\s+(?:an\s+)?email\s+to)\s+([^\s,]+@[^\s,]+)"
        email = re.search(email_pattern, prompt, re.I)
        if email:
            message = re.split(
                r"\b(?:saying|message|body)\b\s*[:=]?", prompt, maxsplit=1, flags=re.I
            )
            has_body = len(message) == 2 and bool(message[1].strip())
            body = message[1].strip() if has_body else "Demo message"
            return json.dumps(
                {
                    "action": "tool",
                    "tool_name": "send_email",
                    "arguments": {"to": email.group(1).rstrip("."), "message": body},
                }
            )

        url = re.search(r"https?://[^\s]+", prompt, re.I)
        if url and re.search(r"\b(fetch|open|read|visit)\b", prompt, re.I):
            return json.dumps(
                {
                    "action": "tool",
                    "tool_name": "fetch_url",
                    "arguments": {"url": url.group(0).rstrip(".,)")},
                }
            )

        return json.dumps(
            {
                "action": "respond",
                "arguments": {},
                "response": "I could not map that request to one of the four demo tools.",
            }
        )


class OllamaProvider:
    name = "ollama"

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def decide(self, prompt: str, tool_schemas: list[dict[str, Any]]) -> str:
        user_prompt = f"Available tools:\n{json.dumps(tool_schemas)}\n\nUser request:\n{prompt}"
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "stream": False,
                        "format": "json",
                        "messages": [
                            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                            {"role": "user", "content": user_prompt},
                        ],
                    },
                )
                response.raise_for_status()
            payload = response.json()
            content = payload["message"]["content"]
            if not isinstance(content, str):
                raise TypeError("Ollama content must be a string")
            return content
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise ProviderError(
                "The local model provider is unavailable or returned an invalid envelope"
            ) from exc


def build_provider(settings: Settings) -> AgentProvider:
    provider_name = settings.model_provider.lower()
    if provider_name == "ollama":
        return OllamaProvider(settings.ollama_base_url, settings.ollama_model)
    if provider_name == "rules":
        return RuleBasedLocalProvider()
    raise ValueError(f"Unsupported MODEL_PROVIDER: {settings.model_provider}")
