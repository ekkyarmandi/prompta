"""Main CLI entry point for Prompta."""

import click

from . import __version__
from .commands.info import info_command
from .commands.projects import projects_command, get_command

from .commands.prompts import (
    list_command,
    show_command,
    #     save_command,
    #     delete_command,
)


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit")
@click.pass_context
def cli(ctx: click.Context, version: bool) -> None:
    """Prompta - A powerful CLI tool for managing and versioning prompts across projects.

    Prompta helps developers manage, version, and sync prompt files
    across multiple projects with a simple command-line interface.
    """
    if version:
        click.echo(f"prompta version {__version__}")
        return

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Prompts related commands
cli.add_command(list_command, name="list")
cli.add_command(show_command, name="show")
# cli.add_command(save_command, name="save")
# cli.add_command(delete_command, name="delete")

# Project related commands
cli.add_command(info_command, name="info")
cli.add_command(projects_command, name="projects")
cli.add_command(get_command, name="get")


if __name__ == "__main__":
    cli()
