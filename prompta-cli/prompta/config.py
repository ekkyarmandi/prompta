"""Configuration management for Prompta CLI."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import keyring
import yaml
from decouple import Config as DecoupleConfig, RepositoryEnv


@dataclass
class Config:
    """Configuration data class for Prompta CLI."""

    # API Configuration
    api_url: str = "https://prompta.ekky.dev"
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
    use_keyring: bool = True
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
            if "use_keyring" in security:
                config.use_keyring = security["use_keyring"]
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
                "use_keyring": self.use_keyring,
                "verify_ssl": self.verify_ssl,
            },
        }


class ConfigManager:
    """Manages configuration loading, saving, and API key storage."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize ConfigManager.

        Args:
            config_dir: Custom configuration directory. If None, uses default.
        """
        self.config_dir = config_dir or self._get_config_dir()
        self.config = Config()
        self.config_file = self.config_dir / "config.yaml"

    def _get_config_dir(self) -> Path:
        """Get configuration directory from environment or default."""
        config_dir = os.getenv("RURU_CONFIG_DIR")
        if config_dir:
            return Path(config_dir)
        return Path.home() / ".prompta"

    def load(self) -> None:
        """Load configuration from file and environment variables."""
        # Load from file first
        if self.config_file.exists():
            with open(self.config_file) as f:
                data = yaml.safe_load(f) or {}
            self.config = Config.from_dict(data)

        # Override with environment variables
        env_config = self._get_config_from_env()
        self._merge_configs(env_config)

    def save(self) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        with open(self.config_file, "w") as f:
            yaml.dump(self.config.to_dict(), f, default_flow_style=False)

    def _get_config_from_env(self) -> Config:
        """Get configuration from environment variables."""
        config = Config()

        # Create decouple config that looks for .env files in current directory
        env_config = self._create_env_config()

        # API configuration
        config.api_url = env_config("RURU_API_URL", default=config.api_url)
        config.api_timeout = env_config(
            "RURU_API_TIMEOUT", default=config.api_timeout, cast=int
        )

        # Output configuration
        config.output_format = env_config(
            "RURU_OUTPUT_FORMAT", default=config.output_format
        )
        config.color = not env_config("RURU_NO_COLOR", default=False, cast=bool)
        config.verbose = env_config("RURU_VERBOSE", default=config.verbose, cast=bool)

        # Cache configuration
        config.cache_enabled = env_config(
            "RURU_CACHE_ENABLED", default=config.cache_enabled, cast=bool
        )
        config.cache_ttl = env_config(
            "RURU_CACHE_TTL", default=config.cache_ttl, cast=int
        )

        return config

    def _create_env_config(self):
        """Create a decouple config that looks for .env files in current directory."""
        # Look for .env file in current working directory first
        cwd_env_file = Path.cwd() / ".env"
        if cwd_env_file.exists():
            return DecoupleConfig(RepositoryEnv(str(cwd_env_file)))

        # Fallback to default decouple behavior using environment variables only
        from decouple import config as default_config

        return default_config

    def _merge_configs(self, env_config: Config) -> None:
        """Merge environment configuration with file configuration."""
        # Override with values from environment variables or .env files
        # Check if the value is different from the default
        default_config = Config()

        if env_config.api_url != default_config.api_url:
            self.config.api_url = env_config.api_url
        if env_config.api_timeout != default_config.api_timeout:
            self.config.api_timeout = env_config.api_timeout
        if env_config.output_format != default_config.output_format:
            self.config.output_format = env_config.output_format
        if env_config.color != default_config.color:
            self.config.color = env_config.color
        if env_config.verbose != default_config.verbose:
            self.config.verbose = env_config.verbose
        if env_config.cache_enabled != default_config.cache_enabled:
            self.config.cache_enabled = env_config.cache_enabled
        if env_config.cache_ttl != default_config.cache_ttl:
            self.config.cache_ttl = env_config.cache_ttl

    def get_api_key(self, explicit_key: Optional[str] = None) -> Optional[str]:
        """Get API key with priority: explicit > env var > .env file > keyring.

        Args:
            explicit_key: Explicitly provided API key (highest priority)

        Returns:
            API key if found, None otherwise
        """
        # 1. Explicit key has highest priority
        if explicit_key:
            return explicit_key

        # 2. Environment variable
        env_key = os.getenv("RURU_API_KEY")
        if env_key:
            return env_key

        # 3. .env file in current directory
        env_config = self._create_env_config()
        try:
            dotenv_key = env_config("RURU_API_KEY", default=None)
            if dotenv_key:
                return dotenv_key
        except Exception:
            # .env file might not exist or be readable
            pass

        # 4. Keyring storage (if enabled)
        if self.config.use_keyring:
            try:
                return keyring.get_password("prompta", "api_key")
            except Exception:
                # Keyring might not be available on all systems
                return None

        return None

    def set_api_key(self, api_key: str) -> None:
        """Store API key in keyring.

        Args:
            api_key: API key to store
        """
        if self.config.use_keyring:
            keyring.set_password("prompta", "api_key", api_key)

    def clear_api_key(self) -> None:
        """Clear API key from keyring."""
        if self.config.use_keyring:
            try:
                keyring.delete_password("prompta", "api_key")
            except keyring.errors.PasswordDeleteError:
                # Key doesn't exist, that's fine
                pass
