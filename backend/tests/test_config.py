from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_default_env_file_is_backend_env() -> None:
    env_file = Path(Settings.model_config["env_file"])
    assert env_file == Path(__file__).resolve().parents[1] / ".env"


def test_risk_thresholds_are_configurable_and_ordered() -> None:
    settings = Settings(
        risk_medium_threshold=20,
        risk_high_threshold=55,
        risk_critical_threshold=90,
    )
    assert settings.risk_threshold_values == (20, 55, 90)

    with pytest.raises(ValidationError, match="Risk thresholds must increase"):
        Settings(
            risk_medium_threshold=60,
            risk_high_threshold=50,
            risk_critical_threshold=80,
        )
