from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
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

    # CORS
    allowed_origins: str = "*"

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert allowed_origins string to list"""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    # @validator("secret_key")
    # def validate_secret_key(cls, v):
    #     if len(v) < 32:
    #         raise ValueError("SECRET_KEY must be at least 32 characters long")
    #     return v

    class Config:
        env_file = ".env"


settings = Settings()
