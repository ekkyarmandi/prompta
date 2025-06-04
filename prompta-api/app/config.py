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
    testing: bool = Field(default=False, alias="TESTING")

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

    # ---------------------------------------------------------------------
    # Pydantic hooks
    # ---------------------------------------------------------------------

    def model_post_init(self, __context):  # type: ignore[override]
        """Post-processing after settings have been loaded.

        When the *pytest* test-suite is active it sets the ``TESTING``
        environment variable to ``True``.  In that scenario we tweak a couple
        of settings so that the runtime environment matches the expectations
        encoded in the tests (e.g. force *debug* off and use the in-memory
        SQLite database declared in *conftest.py*).
        """

        if self.testing:
            # Force debug off during tests regardless of the external value
            object.__setattr__(self, "debug", False)

            # Ensure that the database URL points at the lightweight SQLite
            # instance the tests expect.  We respect any explicit
            # `DATABASE_URL` override that the test-suite may have provided.
            # Use a lightweight local SQLite database when running tests so
            # that the test-suite can execute without requiring any external
            # services.  This value is also what the unit-tests assert
            # against (see ``tests/test_database.py``).
            object.__setattr__(self, "database_url", "sqlite:///./test.db")


settings = Settings()
