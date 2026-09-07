import ipaddress
import json
import re
import unicodedata
from typing import Any
from urllib.parse import urlsplit

from app.gateway.risk import ReasonCode, result_for
from app.gateway.schemas import SecurityContext, SecurityResult


def _normalize_security_text(value: str) -> str:
    """Normalize compatibility forms and remove invisible formatting controls."""
    normalized = unicodedata.normalize("NFKC", value)
    return "".join(character for character in normalized if unicodedata.category(character) != "Cf")


def _parse_legacy_ipv4(hostname: str) -> ipaddress.IPv4Address | None:
    """Parse the non-canonical IPv4 forms accepted by common URL clients."""

    def parse_component(component: str) -> int:
        if not component or component.startswith(("+", "-")):
            raise ValueError
        if component.casefold().startswith("0x"):
            return int(component[2:], 16)
        if len(component) > 1 and component.startswith("0"):
            return int(component[1:], 8)
        return int(component, 10)

    try:
        parts = hostname.split(".")
        if len(parts) > 4:
            return None
        values = [parse_component(part) for part in parts]
        limits = {
            1: (0xFFFFFFFF,),
            2: (0xFF, 0xFFFFFF),
            3: (0xFF, 0xFF, 0xFFFF),
            4: (0xFF, 0xFF, 0xFF, 0xFF),
        }[len(values)]
        if any(value > limit for value, limit in zip(values, limits, strict=True)):
            return None
        if len(values) == 1:
            packed = values[0]
        elif len(values) == 2:
            packed = (values[0] << 24) | values[1]
        elif len(values) == 3:
            packed = (values[0] << 24) | (values[1] << 16) | values[2]
        else:
            packed = sum(
                value << shift
                for value, shift in zip(values, (24, 16, 8, 0), strict=True)
            )
        return ipaddress.IPv4Address(packed)
    except (KeyError, ValueError):
        return None


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
        prompt = _normalize_security_text(context.user_prompt).casefold()
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
        content = _normalize_security_text(
            f"{context.user_prompt} {json.dumps(arguments, default=str, ensure_ascii=False)}"
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
            normalized_hostname = hostname.casefold().rstrip(".") if hostname else ""
            try:
                if normalized_hostname.isdecimal():
                    address = ipaddress.ip_address(int(normalized_hostname))
                else:
                    address = ipaddress.ip_address(normalized_hostname) if hostname else None
            except ValueError:
                address = _parse_legacy_ipv4(normalized_hostname) if hostname else None
            unsafe_hostname = normalized_hostname == "localhost" or normalized_hostname.endswith(
                ".localhost"
            )
            encoded_hostname = "%" in normalized_hostname
            unsafe_address = address is not None and not address.is_global
            if unsafe_hostname or encoded_hostname or unsafe_address:
                return result_for(
                    control=self.name,
                    outcome="block",
                    reason=ReasonCode.UNSAFE_NETWORK_DESTINATION,
                )
        return result_for(control=self.name, outcome="allow", reason="DESTINATION_ALLOWED")
