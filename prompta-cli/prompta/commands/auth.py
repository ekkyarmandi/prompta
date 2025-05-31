"""Authentication commands for Prompta CLI."""

import click

from ..client import PromptaClient
from ..config import ConfigManager
from ..exceptions import AuthenticationError, PromptaAPIError


@click.group()
def auth_group():
    """Authentication commands for managing API credentials."""
    pass


@auth_group.command("init")
def init_command():
    """Initialize CLI with API credentials."""
    click.echo("Enter your Prompta API key:")
    api_key = click.prompt("API Key", hide_input=True)

    try:
        # Load config and test the API key by making a simple request
        config_manager = ConfigManager()
        config_manager.load()
        client = PromptaClient(api_key=api_key, config=config_manager.config)
        client.get_prompts()  # Test connection

        # Save the API key if it works
        config_manager.set_api_key(api_key)

        click.echo("✅ API key saved successfully!")

    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API connection failed")


@auth_group.command("login")
def login_command():
    """Login with username and password."""
    username = click.prompt("Username")
    password = click.prompt("Password", hide_input=True)

    try:
        # Load config and login to get API key
        config_manager = ConfigManager()
        config_manager.load()
        client = PromptaClient(
            api_key="", config=config_manager.config
        )  # Temporary client for login
        response = client.login(username, password)
        api_key = response["api_key"]

        # Save the API key
        config_manager.set_api_key(api_key)

        click.echo("✅ Login successful!")

    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Login failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Login failed")


@auth_group.command("logout")
def logout_command():
    """Clear stored credentials."""
    config_manager = ConfigManager()
    config_manager.clear_api_key()
    click.echo("✅ Logged out successfully!")


@auth_group.command("status")
def status_command():
    """Show authentication status."""
    config_manager = ConfigManager()
    api_key = config_manager.get_api_key()

    if api_key:
        click.echo("✅ Authenticated")
        click.echo("API key is configured and ready to use.")
    else:
        click.echo("❌ Not authenticated")
        click.echo(
            "No API key found. Run 'Prompta auth init' to set up authentication."
        )


@auth_group.command("set-api-key")
@click.argument("api_key")
def set_api_key_command(api_key: str):
    """Set API key manually."""
    try:
        # Load config and test the API key by making a simple request
        config_manager = ConfigManager()
        config_manager.load()
        client = PromptaClient(api_key=api_key, config=config_manager.config)
        client.get_prompts()  # Test connection

        # Save the API key if it works
        config_manager.set_api_key(api_key)

        click.echo("✅ API key set successfully!")

    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Invalid API key")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API connection failed")
