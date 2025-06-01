"""Main CLI entry point for Prompta."""

import click

from . import __version__
from .commands.auth import auth_group, whoami_command, login_command, logout_command
from .config import ConfigManager
from .commands.prompts import (
    prompts_group,
    list_command,
    get_command,
    save_command,
    show_command,
    delete_command,
    info_command,
    search_command,
    download_command,
    download_project_command,
    download_directory_command,
    download_tags_command,
)

# Project management commands
from .commands.project import init_command


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit")
@click.pass_context
def cli(ctx: click.Context, version: bool) -> None:
    """Prompta - A powerful CLI tool for managing and versioning prompts across projects.

    Prompta helps developers manage, version, and sync prompt files (like .cursorrules)
    across multiple projects with a simple command-line interface.
    """
    if version:
        click.echo(f"prompta version {__version__}")
        return

    # Ensure global config is created if needed (only when installed outside virtual environment)
    config_manager = ConfigManager()
    config_manager.ensure_global_config()

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Add command groups
cli.add_command(auth_group, name="auth")
cli.add_command(prompts_group, name="prompts")

# Auth related commands
cli.add_command(whoami_command, name="whoami")
cli.add_command(login_command, name="login")
cli.add_command(logout_command, name="logout")

# Prompts related commands
cli.add_command(list_command, name="list")
cli.add_command(get_command, name="get")
cli.add_command(save_command, name="save")
cli.add_command(show_command, name="show")
cli.add_command(delete_command, name="delete")
cli.add_command(info_command, name="info")
cli.add_command(search_command, name="search")
cli.add_command(download_command, name="download")
cli.add_command(download_project_command, name="download-project")
cli.add_command(download_directory_command, name="download-directory")
cli.add_command(download_tags_command, name="download-tags")

# Project related commands
cli.add_command(init_command, name="init")


if __name__ == "__main__":
    cli()
