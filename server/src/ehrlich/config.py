import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "EHRLICH_"}

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    max_iterations: int = 50
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def has_api_key(self) -> bool:
        return bool(self.anthropic_api_key) or bool(os.environ.get("ANTHROPIC_API_KEY"))


def get_settings() -> Settings:
    return Settings()
