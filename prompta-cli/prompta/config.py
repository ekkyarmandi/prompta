"""Configuration management for Prompta CLI."""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import keyring
import yaml
from dotenv import dotenv_values, load_dotenv


def _is_in_virtual_env() -> bool:
    """Check if Python is running in a virtual environment."""
    return (
        hasattr(sys, "real_prefix")  # virtualenv
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)  # venv
        or os.getenv("VIRTUAL_ENV") is not None  # environment variable
    )


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
        self.global_config_file = Path.home() / ".promptarc"

    def _get_config_dir(self) -> Path:
        """Get configuration directory from environment or default."""
        config_dir = os.getenv("PROMPTA_CONFIG_DIR")
        if config_dir:
            return Path(config_dir)
        return Path.home() / ".prompta"

    def ensure_global_config(self) -> None:
        """Ensure ~/.promptarc exists if prompta is installed outside virtual environment."""
        if not _is_in_virtual_env() and not self.global_config_file.exists():
            self.create_default_global_config()

    def create_default_global_config(self) -> None:
        """Create default ~/.promptarc configuration file."""
        default_config = {
            "api": {"url": "http://localhost:8000", "timeout": 30, "verify_ssl": True},
            "auth": {
                # Note: API key should be set via environment variables or prompta auth commands
                # "api_key": "your-api-key-here"  # Not recommended for security
            },
            "output": {
                "format": "table",  # table, json, yaml
                "color": True,
                "verbose": False,
            },
            "cache": {"enabled": True, "ttl": 300, "directory": "~/.prompta/cache"},
        }

        try:
            with open(self.global_config_file, "w") as f:
                yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
            print(f"✅ Created global configuration file at {self.global_config_file}")
        except Exception as e:
            print(f"❌ Failed to create global configuration file: {e}")

    def load(self) -> None:
        """Load configuration with priority: env vars > .env file > global config > defaults."""
        # 1. Start with default config
        self.config = Config()

        # 2. Load from global config (~/.promptarc) if no local .env file
        cwd_env_file = Path.cwd() / ".env"
        if not cwd_env_file.exists() and self.global_config_file.exists():
            try:
                with open(self.global_config_file) as f:
                    global_data = yaml.safe_load(f) or {}
                self.config = Config.from_dict(global_data)

                # Also load global API key if present (not recommended but supported)
                if "auth" in global_data and "api_key" in global_data["auth"]:
                    os.environ["PROMPTA_API_KEY"] = global_data["auth"]["api_key"]

            except Exception as e:
                # If global config is corrupted, continue with defaults
                print(f"Warning: Could not load global config: {e}")

        # 3. Load from local config directory (~/.prompta/config.yaml)
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    data = yaml.safe_load(f) or {}
                local_config = Config.from_dict(data)
                self._merge_configs(local_config)
            except Exception as e:
                print(f"Warning: Could not load local config: {e}")

        # 4. Override with environment variables and .env files (highest priority)
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
