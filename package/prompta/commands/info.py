"""Info command for checking API status and configuration."""

import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import click
import httpx
from dotenv import dotenv_values

from ..config import ConfigManager
from ..client import PromptaClient
from .. import __version__


def _load_prompta() -> Dict[str, Any]:
    """Load configuration from ~/.prompta if it exists."""
    prompta_path = Path.home() / ".prompta"
    if prompta_path.exists():
        try:
            config = {}
            with open(prompta_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        # Remove quotes from value
                        value = value.strip().strip('"').strip("'")
                        config[key.strip()] = value
            return config
        except Exception as e:
            click.echo(f"⚠️  Warning: Could not read {prompta_path}: {e}")
            return {}
    return {}


def _get_config_sources(
    api_key_flag: Optional[str], api_url_flag: Optional[str]
) -> Dict[str, Any]:
    """Get configuration from all sources in priority order."""
    sources = {
        "api_key": {"value": None, "source": None},
        "api_url": {"value": None, "source": None},
    }

    # 1. CLI flags (highest priority)
    if api_key_flag:
        sources["api_key"]["value"] = api_key_flag
        sources["api_key"]["source"] = "CLI flag (--api-key)"

    if api_url_flag:
        sources["api_url"]["value"] = api_url_flag
        sources["api_url"]["source"] = "CLI flag (--api-url)"

    # 2. Environment variables
    if not sources["api_key"]["value"]:
        env_key = os.getenv("PROMPTA_API_KEY")
        if env_key:
            sources["api_key"]["value"] = env_key
            sources["api_key"]["source"] = "Environment variable (PROMPTA_API_KEY)"

    if not sources["api_url"]["value"]:
        env_url = os.getenv("PROMPTA_API_URL")
        if env_url:
            sources["api_url"]["value"] = env_url
            sources["api_url"]["source"] = "Environment variable (PROMPTA_API_URL)"

    # 3. .env file
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        try:
            env_values = dotenv_values(env_file)

            if not sources["api_key"]["value"] and env_values.get("PROMPTA_API_KEY"):
                sources["api_key"]["value"] = env_values["PROMPTA_API_KEY"]
                sources["api_key"]["source"] = f".env file ({env_file})"

            if not sources["api_url"]["value"] and env_values.get("PROMPTA_API_URL"):
                sources["api_url"]["value"] = env_values["PROMPTA_API_URL"]
                sources["api_url"]["source"] = f".env file ({env_file})"
        except Exception as e:
            click.echo(f"⚠️  Warning: Could not read .env file: {e}")

    # 4. ~/.prompta (lowest priority)
    prompta_config = _load_prompta()

    if not sources["api_url"]["value"] and prompta_config.get("PROMPTA_API_URL"):
        sources["api_url"]["value"] = prompta_config["PROMPTA_API_URL"]
        sources["api_url"]["source"] = f"~/.prompta file ({Path.home() / '.prompta'})"

    if not sources["api_key"]["value"] and prompta_config.get("PROMPTA_API_KEY"):
        sources["api_key"]["value"] = prompta_config["PROMPTA_API_KEY"]
        sources["api_key"]["source"] = f"~/.prompta file ({Path.home() / '.prompta'})"

    # Set defaults if nothing found
    if not sources["api_url"]["value"]:
        sources["api_url"]["value"] = "http://localhost:8000"
        sources["api_url"]["source"] = "Default value"

    return sources


def _check_api_status(api_url: str) -> Tuple[bool, str]:
    """Check if the API is live and accessible."""
    try:
        # Clean up the URL
        api_url = api_url.rstrip("/")

        # Try to hit a health endpoint or root endpoint
        with httpx.Client(timeout=10.0) as client:
            # Try common health check endpoints
            endpoints_to_try = ["/health", "/api/health", "/status", "/"]

            for endpoint in endpoints_to_try:
                try:
                    response = client.get(f"{api_url}{endpoint}")
                    if (
                        response.status_code < 500
                    ):  # Any non-server error response means API is responding
                        return True, f"API is responding (HTTP {response.status_code})"
                except httpx.RequestError:
                    continue

            # If none of the endpoints worked, try a basic connection
            try:
                response = client.get(api_url)
                return True, f"API is responding (HTTP {response.status_code})"
            except httpx.RequestError as e:
                return False, f"Connection failed: {str(e)}"

    except Exception as e:
        return False, f"Error checking API: {str(e)}"


def _check_api_key_status(api_key: Optional[str], api_url: str) -> Tuple[bool, str]:
    """Check if the API key is valid by making a test request."""
    if not api_key:
        return False, "No API key found"

    try:
        # Create a client and try to make an authenticated request
        config_manager = ConfigManager()
        config_manager.load()
        config_manager.config.api_url = api_url

        client = PromptaClient(api_key=api_key, config=config_manager.config)

        # Try to get user info or make a simple authenticated request
        try:
            user_info = client.get_user_info()
            if user_info:
                username = user_info.get("username", "Unknown")
                return True, f"API key is valid (authenticated as: {username})"
        except Exception:
            # If get_user_info doesn't work, try a simple prompts list request
            try:
                client.get_prompts(limit=1)
                return True, "API key is valid (authenticated successfully)"
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "Unauthorized" in error_msg:
                    return False, "API key is invalid (authentication failed)"
                elif "403" in error_msg or "Forbidden" in error_msg:
                    return False, "API key is valid but lacks permissions"
                else:
                    return False, f"API key validation failed: {error_msg}"

    except Exception as e:
        return False, f"Error validating API key: {str(e)}"


@click.command()
@click.option("--api-key", help="API key to use for checking authentication")
@click.option("--api-url", help="API URL to use for checking connection")
def info_command(api_key: Optional[str], api_url: Optional[str]):
    """Show information about API connection and authentication status.

    This command checks:
    - Whether the API server is responding
    - Whether API authentication is working
    """
    click.echo(f"📋 Prompta CLI Info (v{__version__})")
    click.echo("=" * 50)

    # Get configuration from all sources
    config_sources = _get_config_sources(api_key, api_url)
    current_api_url = config_sources["api_url"]["value"]
    current_api_key = config_sources["api_key"]["value"]

    # Check API connection
    click.echo("\n🌐 Server Connection:")
    is_live, status_msg = _check_api_status(current_api_url)
    status_icon = "✅" if is_live else "❌"
    click.echo(f"   {status_icon} {status_msg}")

    # Check API key authentication
    click.echo("\n🔐 API Authentication:")
    if current_api_key:
        if is_live:
            is_valid, key_status_msg = _check_api_key_status(
                current_api_key, current_api_url
            )
            key_status_icon = "✅" if is_valid else "❌"
            click.echo(f"   {key_status_icon} {key_status_msg}")
        else:
            click.echo("   ⏸️  Cannot validate (server not responding)")
    else:
        click.echo("   ❌ No API key configured")

    # Show quick help if there are issues
    if not is_live or not current_api_key:
        click.echo("\n💡 Quick Setup:")
        if not current_api_key:
            click.echo("   Set your API key:")
            click.echo("     export PROMPTA_API_KEY=your_api_key_here")
            click.echo("   Or add to .env file:")
            click.echo("     echo 'PROMPTA_API_KEY=your_api_key_here' >> .env")

        if not is_live:
            click.echo("   Configure your API URL:")
            click.echo("     export PROMPTA_API_URL=https://your-api-server.com")
