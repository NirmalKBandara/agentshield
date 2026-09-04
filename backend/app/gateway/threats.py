import ipaddress
import json
import re
import unicodedata
from typing import Any
from urllib.parse import urlsplit

from app.gateway.risk import ReasonCode, result_for
from app.gateway.schemas import SecurityContext, SecurityResult


class PromptInjectionControl:
    name = "prompt-injection-detector"
    _patterns = (
        re.compile(r"\bignore\s+(?:all\s+)?(?:previous|prior|system)\s+instructions?\b"),
        re.compile(r"\b(?:disable|bypass|override)\s+(?:your\s+)?(?:rules|guardrails|policy)\b"),
        re.compile(r"\b(?:reveal|print|show)\s+(?:the\s+)?system\s+prompt\b"),
    )

    async def evaluate(
        self, context: SecurityContext, tool_name: str, arguments: dict[str, Any]
    ) -> SecurityResult:
        prompt = unicodedata.normalize("NFKC", context.user_prompt).casefold()
        if any(pattern.search(prompt) for pattern in self._patterns):
            return result_for(
                control=self.name,
                outcome="block",
                reason=ReasonCode.PROMPT_INJECTION,
            )
        return result_for(control=self.name, outcome="allow", reason="NO_PROMPT_INJECTION")


class SensitiveDataControl:
    name = "sensitive-data-detector"
    _indicators = (
        re.compile(r"\be-?mail(?: address)?\b"),
        re.compile(r"\bphone(?: number)?\b"),
        re.compile(r"\baccount (?:information|details|number)\b"),
        re.compile(r"\bcustomer records?\b"),
    )

    async def evaluate(
        self, context: SecurityContext, tool_name: str, arguments: dict[str, Any]
    ) -> SecurityResult:
        content = unicodedata.normalize(
            "NFKC", f"{context.user_prompt} {json.dumps(arguments, default=str)}"
        ).casefold()
        matches = sum(pattern.search(content) is not None for pattern in self._indicators)
        if tool_name == "send_email" and matches >= 2:
            return result_for(
                control=self.name,
                outcome="block",
                reason=ReasonCode.SENSITIVE_DATA_EXFILTRATION,
            )
        return result_for(control=self.name, outcome="allow", reason="NO_SENSITIVE_DATA")


class NetworkDestinationControl:
    name = "network-destination-policy"

    async def evaluate(
        self, context: SecurityContext, tool_name: str, arguments: dict[str, Any]
    ) -> SecurityResult:
        if tool_name == "fetch_url":
            hostname = urlsplit(str(arguments.get("url", ""))).hostname
            try:
                if hostname and hostname.isdecimal():
                    address = ipaddress.ip_address(int(hostname))
                else:
                    address = ipaddress.ip_address(hostname) if hostname else None
            except ValueError:
                address = None
            normalized_hostname = hostname.casefold().rstrip(".") if hostname else ""
            unsafe_hostname = normalized_hostname == "localhost" or normalized_hostname.endswith(
                ".localhost"
            )
            unsafe_address = address and (
                address.is_private
                or address.is_loopback
                or address.is_link_local
                or address.is_reserved
            )
            if unsafe_hostname or unsafe_address:
                return result_for(
                    control=self.name,
                    outcome="block",
                    reason=ReasonCode.UNSAFE_NETWORK_DESTINATION,
                )
        return result_for(control=self.name, outcome="allow", reason="DESTINATION_ALLOWED")
