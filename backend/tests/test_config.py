from pathlib import Path

from app.core.config import Settings


def test_default_env_file_is_backend_env() -> None:
    env_file = Path(Settings.model_config["env_file"])
    assert env_file == Path(__file__).resolve().parents[1] / ".env"
