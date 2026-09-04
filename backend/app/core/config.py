from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AgentShield API"
    app_env: str = "development"
    database_url: str = (
        "postgresql+asyncpg://agentshield:agentshield_local_password@localhost:5432/agentshield"
    )
    cors_origins: str = "http://localhost:3000"
    model_provider: str = "rules"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    risk_medium_threshold: int = Field(default=30, ge=1, le=98)
    risk_high_threshold: int = Field(default=60, ge=2, le=99)
    risk_critical_threshold: int = Field(default=80, ge=3, le=100)

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_risk_thresholds(self) -> "Settings":
        if not (
            self.risk_medium_threshold
            < self.risk_high_threshold
            < self.risk_critical_threshold
        ):
            raise ValueError("Risk thresholds must increase between 0 and 100")
        return self

    @property
    def risk_threshold_values(self) -> tuple[int, int, int]:
        return (
            self.risk_medium_threshold,
            self.risk_high_threshold,
            self.risk_critical_threshold,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
