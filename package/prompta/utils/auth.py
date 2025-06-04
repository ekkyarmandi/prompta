"""Authentication utilities for CLI commands."""

from typing import Optional

from ..client import PromptaClient
from ..config import ConfigManager
from ..exceptions import AuthenticationError, ConfigurationError


def get_authenticated_client(api_key: Optional[str] = None) -> PromptaClient:
    """Get an authenticated client.

    Args:
        api_key: Optional API key to use. If not provided, will try to get from config.

    Returns:
        Authenticated PromptaClient instance

    Raises:
        AuthenticationError: If no API key is found or authentication fails
        ConfigurationError: If configuration is invalid
    """
    config_manager = ConfigManager()
    config_manager.load()  # Load configuration from file and environment

    if not api_key:
        api_key = config_manager.get_api_key()

        if not api_key:
            raise AuthenticationError(
                "No API key found. Set PROMPTA_API_KEY environment variable, "
                "add it to .env file, or use --api-key flag."
            )

    return PromptaClient(api_key=api_key, config=config_manager.config)
