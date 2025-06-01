from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application
    app_name: str = "Prompta API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./sqlite.db"

    # Security
    secret_key: str = (
        "your-super-secret-key-change-this-in-production-at-least-32-characters-long"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API Keys
    api_key_expire_days: int = 365

    # CORS - This will now properly handle comma-separated values from .env
    allowed_origins: List[str] = Field(default=["*"])

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60


settings = Settings()
