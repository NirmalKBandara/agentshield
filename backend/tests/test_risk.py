import pytest

from app.gateway import RiskThresholds, SecurityResult, assess_risk, risk_level_for
from app.gateway.risk import ReasonCode, result_for


@pytest.mark.parametrize(
    ("score", "level"),
    [
        (-1, "low"),
        (0, "low"),
        (29, "low"),
        (30, "medium"),
        (59, "medium"),
        (60, "high"),
        (79, "high"),
        (80, "critical"),
        (100, "critical"),
        (101, "critical"),
    ],
)
def test_risk_level_boundaries(score: int, level: str) -> None:
    assert risk_level_for(score) == level


def test_risk_level_uses_custom_thresholds() -> None:
    thresholds = RiskThresholds(medium=20, high=40, critical=90)
    assert risk_level_for(45, thresholds) == "high"
    assert risk_level_for(89, thresholds) == "high"
    assert risk_level_for(90, thresholds) == "critical"


@pytest.mark.parametrize(
    "values",
    [(0, 60, 80), (30, 30, 80), (30, 90, 80), (30, 60, 101)],
)
def test_invalid_thresholds_are_rejected(values: tuple[int, int, int]) -> None:
    with pytest.raises(ValueError, match="must increase"):
        RiskThresholds(*values)


def test_multiple_signals_aggregate_and_cap_at_one_hundred() -> None:
    results = [
        result_for(
            control="prompt", outcome="block", reason=ReasonCode.PROMPT_INJECTION
        ),
        result_for(
            control="permission", outcome="block", reason=ReasonCode.TOOL_NOT_AUTHORIZED
        ),
        result_for(
            control="network", outcome="block", reason=ReasonCode.UNSAFE_NETWORK_DESTINATION
        ),
    ]

    assessment = assess_risk(results)

    assert assessment.score == 100
    assert assessment.level == "critical"
    assert assessment.reason_codes == (
        "PROMPT_INJECTION_DETECTED",
        "TOOL_NOT_AUTHORIZED",
        "UNSAFE_NETWORK_DESTINATION",
    )
    assert "instruction-override" in assessment.explanation
    assert "not authorized" in assessment.explanation


def test_duplicate_reason_does_not_inflate_score() -> None:
    result = result_for(
        control="permission", outcome="block", reason=ReasonCode.TOOL_NOT_AUTHORIZED
    )
    assessment = assess_risk([result, result])
    assert assessment.score == 50
    assert assessment.reason_codes == ("TOOL_NOT_AUTHORIZED",)


def test_unknown_blocking_reason_gets_conservative_fallback() -> None:
    result = SecurityResult(control="custom", outcome="block", reason="CUSTOM_BLOCK")
    assessment = assess_risk([result])
    assert assessment.score == 50
    assert assessment.level == "medium"


def test_allow_results_do_not_contribute_risk() -> None:
    result = result_for(control="prompt", outcome="allow", reason="NO_PROMPT_INJECTION")
    assessment = assess_risk([result])
    assert result.risk_score == 0
    assert assessment.score == 0
    assert assessment.level == "low"
    assert assessment.reason_codes == ()
