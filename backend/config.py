"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API
    app_name: str = "Agent Orchestrator"
    debug: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Claude API
    anthropic_api_key: Optional[str] = None
    default_model: str = "claude-sonnet-4-20250514"

    # Database
    database_path: str = "data/orchestrator.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
