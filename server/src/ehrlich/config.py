import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="EHRLICH_",
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
    )

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-6"
    director_model: str = "claude-opus-4-6"
    researcher_model: str = "claude-sonnet-4-5-20250929"
    summarizer_model: str = "claude-haiku-4-5-20251001"
    summarizer_threshold: int = 2000
    max_iterations: int = 50
    max_iterations_per_phase: int = 10
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    db_path: str = "data/ehrlich.db"

    @property
    def has_api_key(self) -> bool:
        return bool(self.anthropic_api_key) or bool(os.environ.get("ANTHROPIC_API_KEY"))


def get_settings() -> Settings:
    return Settings()
