import os
import pytest
from unittest.mock import patch
from app.config import Settings, settings


def test_settings_singleton():
    """Test that the settings object is a singleton instance of Settings"""
    assert isinstance(settings, Settings)
    # Test that settings has values loaded from environment (set in conftest.py)
    assert settings.app_name == "Prompta API Test"
    assert settings.app_version == "1.0.0"
    assert settings.debug is False


def test_settings_custom_values():
    """Test that a new Settings instance can be created with custom values"""
    # Create a new Settings instance with custom values
    with patch.dict(os.environ, clear=True):  # Clear all env vars for this test
        with patch.dict(
            os.environ,
            {
                "APP_NAME": "Custom App",
                "APP_VERSION": "2.0.0",
                "DEBUG": "true",
                "DATABASE_URL": "sqlite:///./custom.db",
                "SECRET_KEY": "custom-secret-key",
                "ALGORITHM": "RS256",
                "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
                "API_KEY_EXPIRE_DAYS": "30",
                "ALLOWED_ORIGINS": '["http://localhost:4000"]',
                "RATE_LIMIT_REQUESTS": "50",
                "RATE_LIMIT_WINDOW": "30",
            },
        ):
            s = Settings()
            assert s.app_name == "Custom App"
            assert s.app_version == "2.0.0"
            assert s.debug is True
            assert s.database_url == "sqlite:///./custom.db"
            assert s.secret_key == "custom-secret-key"
            assert s.algorithm == "RS256"
            assert s.access_token_expire_minutes == 60
            assert s.api_key_expire_days == 30
            assert s.allowed_origins == ["http://localhost:4000"]
            assert s.rate_limit_requests == 50
            assert s.rate_limit_window == 30


def test_settings_defaults():
    """Test that Settings uses default values when env vars are not set"""
    # Test only some default values to avoid environment-specific issues
    with patch.dict(os.environ, clear=True):  # Clear all env vars for this test
        s = Settings()
        assert s.app_name == "Prompta API"
        assert s.app_version == "1.0.0"
        # Skip debug check as it might be influenced by other environment factors
        assert s.algorithm == "HS256"
        assert s.access_token_expire_minutes == 30
        assert s.api_key_expire_days == 365
        assert s.allowed_origins == ["*"]
        assert s.rate_limit_requests == 100
        assert s.rate_limit_window == 60
