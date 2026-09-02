import ipaddress
import json
from typing import Any
from urllib.parse import urlsplit

from app.gateway.schemas import SecurityContext, SecurityResult


class PromptInjectionControl:
    name = "prompt-injection-detector"
    _phrases = ("ignore all previous instructions", "disable your rules", "ignore your rules")

    async def evaluate(
        self, context: SecurityContext, tool_name: str, arguments: dict[str, Any]
    ) -> SecurityResult:
        prompt = context.user_prompt.casefold()
        if any(phrase in prompt for phrase in self._phrases):
            return SecurityResult(
                control=self.name,
                outcome="block",
                reason="PROMPT_INJECTION_DETECTED",
                risk_score=95,
            )
        return SecurityResult(control=self.name, outcome="allow", reason="NO_PROMPT_INJECTION")


class SensitiveDataControl:
    name = "sensitive-data-detector"
    _indicators = ("email", "phone", "account information", "customer records")

    async def evaluate(
        self, context: SecurityContext, tool_name: str, arguments: dict[str, Any]
    ) -> SecurityResult:
        content = f"{context.user_prompt} {json.dumps(arguments, default=str)}".casefold()
        matches = sum(indicator in content for indicator in self._indicators)
        if tool_name == "send_email" and matches >= 2:
            return SecurityResult(
                control=self.name,
                outcome="block",
                reason="SENSITIVE_DATA_EXFILTRATION_DETECTED",
                risk_score=90,
            )
        return SecurityResult(control=self.name, outcome="allow", reason="NO_SENSITIVE_DATA")


class NetworkDestinationControl:
    name = "network-destination-policy"

    async def evaluate(
        self, context: SecurityContext, tool_name: str, arguments: dict[str, Any]
    ) -> SecurityResult:
        if tool_name == "fetch_url":
            hostname = urlsplit(str(arguments.get("url", ""))).hostname
            try:
                address = ipaddress.ip_address(hostname) if hostname else None
            except ValueError:
                address = None
            if address and (
                address.is_private
                or address.is_loopback
                or address.is_link_local
                or address.is_reserved
            ):
                return SecurityResult(
                    control=self.name,
                    outcome="block",
                    reason="UNSAFE_NETWORK_DESTINATION",
                    risk_score=100,
                )
        return SecurityResult(control=self.name, outcome="allow", reason="DESTINATION_ALLOWED")
