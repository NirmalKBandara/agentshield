from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from app.gateway.schemas import RiskLevel, SecurityResult


class ReasonCode(StrEnum):
    PROMPT_INJECTION = "PROMPT_INJECTION_DETECTED"
    TOOL_NOT_AUTHORIZED = "TOOL_NOT_AUTHORIZED"
    SENSITIVE_DATA_EXFILTRATION = "SENSITIVE_DATA_EXFILTRATION_DETECTED"
    UNSAFE_NETWORK_DESTINATION = "UNSAFE_NETWORK_DESTINATION"
    REFUND_LIMIT_EXCEEDED = "REFUND_LIMIT_EXCEEDED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    UNKNOWN_TOOL = "UNKNOWN_TOOL"
    SECURITY_CONTROL_FAILURE = "SECURITY_CONTROL_FAILURE"


@dataclass(frozen=True)
class RiskSignal:
    weight: int
    explanation: str


# Weights reflect impact and confidence for this MVP. Keeping them in one table
# makes score changes reviewable and prevents controls from drifting apart.
RISK_SIGNALS: dict[str, RiskSignal] = {
    ReasonCode.PROMPT_INJECTION: RiskSignal(
        40, "The prompt contains an instruction-override pattern."
    ),
    ReasonCode.TOOL_NOT_AUTHORIZED: RiskSignal(
        50, "The agent is not authorized to use the requested tool."
    ),
    ReasonCode.SENSITIVE_DATA_EXFILTRATION: RiskSignal(
        60,
        "Sensitive data was detected in a request that sends content to an external target.",
    ),
    ReasonCode.UNSAFE_NETWORK_DESTINATION: RiskSignal(
        60, "The URL resolves to a private, loopback, link-local, or reserved address."
    ),
    ReasonCode.REFUND_LIMIT_EXCEEDED: RiskSignal(
        40, "The requested refund exceeds the configured policy limit."
    ),
    ReasonCode.RATE_LIMIT_EXCEEDED: RiskSignal(
        20, "The agent exceeded its configured request rate."
    ),
    ReasonCode.UNKNOWN_TOOL: RiskSignal(
        50, "The requested tool is not registered with the gateway."
    ),
    ReasonCode.SECURITY_CONTROL_FAILURE: RiskSignal(
        100, "A security control failed, so the gateway denied the request safely."
    ),
}

DEFAULT_BLOCK_SIGNAL = RiskSignal(
    50, "A security control blocked the request for an unclassified reason."
)


@dataclass(frozen=True)
class RiskAssessment:
    score: int
    level: RiskLevel
    reason_codes: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class RiskThresholds:
    medium: int = 30
    high: int = 60
    critical: int = 80

    def __post_init__(self) -> None:
        if not 0 < self.medium < self.high < self.critical <= 100:
            raise ValueError("Risk thresholds must increase between 0 and 100")


DEFAULT_THRESHOLDS = RiskThresholds()


def risk_level_for(
    score: int, thresholds: RiskThresholds = DEFAULT_THRESHOLDS
) -> RiskLevel:
    normalized = max(0, min(100, score))
    if normalized >= thresholds.critical:
        return "critical"
    if normalized >= thresholds.high:
        return "high"
    if normalized >= thresholds.medium:
        return "medium"
    return "low"


def result_for(
    *,
    control: str,
    outcome: Literal["allow", "block"],
    reason: str,
    explanation: str | None = None,
) -> SecurityResult:
    signal = RISK_SIGNALS.get(reason, DEFAULT_BLOCK_SIGNAL)
    resolved_explanation = explanation
    if resolved_explanation is None:
        resolved_explanation = (
            signal.explanation
            if outcome == "block"
            else "The control found no blocking security signal."
        )
    return SecurityResult(
        control=control,
        outcome=outcome,
        reason=reason,
        explanation=resolved_explanation,
        risk_score=signal.weight if outcome == "block" else 0,
    )


def assess_risk(
    results: Sequence[SecurityResult],
    thresholds: RiskThresholds = DEFAULT_THRESHOLDS,
) -> RiskAssessment:
    blocked = [result for result in results if result.outcome == "block"]
    contributions: dict[str, int] = {}
    for result in blocked:
        fallback = RISK_SIGNALS.get(result.reason, DEFAULT_BLOCK_SIGNAL).weight
        contribution = result.risk_score or fallback
        contributions[result.reason] = max(contributions.get(result.reason, 0), contribution)
    score = min(100, sum(contributions.values()))
    reason_codes = tuple(dict.fromkeys(result.reason for result in blocked))
    explanations = tuple(dict.fromkeys(result.explanation for result in blocked))

    if explanations:
        explanation = " ".join(explanations)
    else:
        explanation = "No blocking security signals were detected."

    return RiskAssessment(
        score=score,
        level=risk_level_for(score, thresholds),
        reason_codes=reason_codes,
        explanation=explanation,
    )
