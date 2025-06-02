"""Configuration management for Prompta CLI."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import dotenv_values


@dataclass
class Config:
    """Configuration data class for Prompta CLI."""

    # API Configuration
    api_url: str = "http://localhost:8000"  # Default to local development
    api_timeout: int = 30

    # Default Settings
    default_location: str = "./"
    auto_create_dirs: bool = True
    sync_on_get: bool = False

    # Output Configuration
    output_format: str = "table"  # table, json, yaml
    color: bool = True
    verbose: bool = False

    # Cache Configuration
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutes
    cache_directory: str = "~/.prompta/cache"

    # Security Configuration
    verify_ssl: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        config = cls()

        # API configuration
        if "api" in data:
            api_config = data["api"]
            if "url" in api_config:
                config.api_url = api_config["url"]
            if "timeout" in api_config:
                config.api_timeout = api_config["timeout"]

        # Default settings
        if "defaults" in data:
            defaults = data["defaults"]
            if "location" in defaults:
                config.default_location = defaults["location"]
            if "auto_create_dirs" in defaults:
                config.auto_create_dirs = defaults["auto_create_dirs"]
            if "sync_on_get" in defaults:
                config.sync_on_get = defaults["sync_on_get"]

        # Output configuration
        if "output" in data:
            output = data["output"]
            if "format" in output:
                config.output_format = output["format"]
            if "color" in output:
                config.color = output["color"]
            if "verbose" in output:
                config.verbose = output["verbose"]

        # Cache configuration
        if "cache" in data:
            cache = data["cache"]
            if "enabled" in cache:
                config.cache_enabled = cache["enabled"]
            if "ttl" in cache:
                config.cache_ttl = cache["ttl"]
            if "directory" in cache:
                config.cache_directory = cache["directory"]

        # Security configuration
        if "security" in data:
            security = data["security"]
            if "verify_ssl" in security:
                config.verify_ssl = security["verify_ssl"]

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert Config to dictionary."""
        return {
            "api": {
                "url": self.api_url,
                "timeout": self.api_timeout,
            },
            "defaults": {
                "location": self.default_location,
                "auto_create_dirs": self.auto_create_dirs,
                "sync_on_get": self.sync_on_get,
            },
            "output": {
                "format": self.output_format,
                "color": self.color,
                "verbose": self.verbose,
            },
            "cache": {
                "enabled": self.cache_enabled,
                "ttl": self.cache_ttl,
                "directory": self.cache_directory,
            },
            "security": {
                "verify_ssl": self.verify_ssl,
            },
        }


class ConfigManager:
    """Manages configuration loading with simplified project-based approach."""

    def __init__(self):
        """Initialize ConfigManager."""
        self.config = Config()

    def load(self) -> None:
        """Load configuration with priority: env vars > .env file > ~/.prompta > defaults."""
        # 1. Start with default config
        self.config = Config()

        # 2. Load from ~/.prompta (lowest config priority)
        prompta_config = self._get_config_from_prompta()
        if prompta_config:
            self._merge_configs(prompta_config)

        # 3. Override with environment variables and .env files (highest priority)
        env_config = self._get_config_from_env()
        self._merge_configs(env_config)

    def _get_config_from_env(self) -> Config:
        """Get configuration from environment variables."""
        config = Config()

        # Create dotenv config that looks for .env files in current directory
        env_config = self._create_env_config()

        # API configuration
        config.api_url = env_config("PROMPTA_API_URL", default=config.api_url)
        config.api_timeout = env_config(
            "PROMPTA_API_TIMEOUT", default=config.api_timeout, cast=int
        )

        # Output configuration
        config.output_format = env_config(
            "PROMPTA_OUTPUT_FORMAT", default=config.output_format
        )
        config.color = not env_config("PROMPTA_NO_COLOR", default=False, cast=bool)
        config.verbose = env_config(
            "PROMPTA_VERBOSE", default=config.verbose, cast=bool
        )

        # Cache configuration
        config.cache_enabled = env_config(
            "PROMPTA_CACHE_ENABLED", default=config.cache_enabled, cast=bool
        )
        config.cache_ttl = env_config(
            "PROMPTA_CACHE_TTL", default=config.cache_ttl, cast=int
        )

        return config

    def _create_env_config(self):
        """Create a dotenv config that looks for .env files in current directory."""
        # Look for .env file in current working directory first
        cwd_env_file = Path.cwd() / ".env"
        if cwd_env_file.exists():
            # Load the .env file and return a config function
            env_values = dotenv_values(cwd_env_file)

            def env_config(key: str, default=None, cast=str):
                """Get value from .env file or environment with type casting."""
                # Priority: environment variable > .env file > default
                value = os.getenv(key) or env_values.get(key, default)
                if value == default:
                    return default
                if cast == bool:
                    return str(value).lower() in ("true", "1", "yes", "on")
                elif cast == int:
                    return int(value)
                elif cast == float:
                    return float(value)
                return cast(value)

            return env_config

        # Fallback to environment variables only
        def env_config(key: str, default=None, cast=str):
            """Get value from environment variables with type casting."""
            value = os.getenv(key, default)
            if value == default:
                return default
            if cast == bool:
                return str(value).lower() in ("true", "1", "yes", "on")
            elif cast == int:
                return int(value)
            elif cast == float:
                return float(value)
            return cast(value)

        return env_config

    def _get_config_from_prompta(self) -> Optional[Config]:
        """Get configuration from ~/.prompta file."""
        prompta_path = Path.home() / ".prompta"
        if not prompta_path.exists():
            return None

        try:
            config = Config()
            with open(prompta_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        # Remove quotes from value
                        value = value.strip().strip('"').strip("'")

                        if key.strip() == "PROMPTA_API_URL":
                            config.api_url = value

            return config
        except Exception:
            # File might not exist or be malformed
            return None

    def _merge_configs(self, other_config: Config) -> None:
        """Merge another configuration with the current one."""
        # Override with values from other_config
        # Only override if the other value is different from defaults
        default_config = Config()

        if other_config.api_url != default_config.api_url:
            self.config.api_url = other_config.api_url
        if other_config.api_timeout != default_config.api_timeout:
            self.config.api_timeout = other_config.api_timeout
        if other_config.output_format != default_config.output_format:
            self.config.output_format = other_config.output_format
        if other_config.color != default_config.color:
            self.config.color = other_config.color
        if other_config.verbose != default_config.verbose:
            self.config.verbose = other_config.verbose
        if other_config.cache_enabled != default_config.cache_enabled:
            self.config.cache_enabled = other_config.cache_enabled
        if other_config.cache_ttl != default_config.cache_ttl:
            self.config.cache_ttl = other_config.cache_ttl

    def get_api_key(self, explicit_key: Optional[str] = None) -> Optional[str]:
        """Get API key with priority: explicit > env var > .env file > ~/.prompta.

        Args:
            explicit_key: Explicitly provided API key (highest priority)

        Returns:
            API key if found, None otherwise
        """
        # 1. Explicit key has highest priority
        if explicit_key:
            return explicit_key

        # 2. Environment variable
        env_key = os.getenv("PROMPTA_API_KEY")
        if env_key:
            return env_key

        # 3. .env file in current directory
        env_config = self._create_env_config()
        try:
            dotenv_key = env_config("PROMPTA_API_KEY", default=None)
            if dotenv_key:
                return dotenv_key
        except Exception:
            # .env file might not exist or be readable
            pass

        # 4. ~/.prompta file
        prompta_path = Path.home() / ".prompta"
        if prompta_path.exists():
            try:
                with open(prompta_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            key, value = line.split("=", 1)
                            # Remove quotes from value
                            value = value.strip().strip('"').strip("'")

                            if key.strip() == "PROMPTA_API_KEY":
                                return value if value else None
            except Exception:
                # File might not exist or be malformed
                pass

        return None
