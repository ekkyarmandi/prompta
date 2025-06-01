from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator
from decouple import config


class Settings(BaseSettings):
    # Application
    app_name: str = "Prompta API"
    app_version: str = "1.0.0"
    debug: bool = config("DEBUG", default=False, cast=bool)

    # Database
    database_url: str = config("DATABASE_URL", default="sqlite:///./prompta.db")

    # Security
    secret_key: str = config(
        "SECRET_KEY",
        default="your-super-secret-key-change-this-in-production-at-least-32-characters-long",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = config(
        "ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int
    )

    # API Keys
    api_key_expire_days: int = config("API_KEY_EXPIRE_DAYS", default=365, cast=int)

    # CORS
    allowed_origins: list = config(
        "ALLOWED_ORIGINS", default="*", cast=lambda v: v.split(",")
    )

    # Rate Limiting
    rate_limit_requests: int = config("RATE_LIMIT_REQUESTS", default=100, cast=int)
    rate_limit_window: int = config(
        "RATE_LIMIT_WINDOW", default=60, cast=int
    )  # seconds

    # @validator("secret_key")
    # def validate_secret_key(cls, v):
    #     if len(v) < 32:
    #         raise ValueError("SECRET_KEY must be at least 32 characters long")
    #     return v

    class Config:
        env_file = ".env"


settings = Settings()
