"""Main CLI entry point for Prompta."""

import click

from . import __version__
from .commands.health import health_group, ping_command
from .commands.projects import project_group
from .commands.prompts import prompt_group
from .commands.export import export_group


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit")
@click.pass_context
def cli(ctx: click.Context, version: bool) -> None:
    """Prompta - A powerful CLI tool for managing and versioning prompts across projects.

    Prompta helps developers manage, version, and sync prompt files
    across multiple projects with a simple command-line interface.

    Common commands:
      prompta status                    # Check API connection and auth
      prompta prompt list               # List all prompts
      prompta prompt show <name>        # Show prompt content
      prompta project list              # List all projects

      prompta export project <name>     # Export project prompts
    """
    if version:
        click.echo(f"prompta version {__version__}")
        return

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Add command groups
cli.add_command(health_group, name="status")
cli.add_command(project_group, name="project")
cli.add_command(prompt_group, name="prompt")
cli.add_command(export_group, name="export")

# Add individual commands
cli.add_command(ping_command, name="ping")

# Add convenience aliases for common commands


@cli.command(hidden=True)
@click.argument("identifier", required=False)
@click.option("--project", "-p", help="Download entire project by name")
@click.option("--output", "-o", help="Output directory or file path")
@click.option("--api-key", help="API key to use for this request")
@click.pass_context
def get(ctx, identifier, project, output, api_key):
    """Alias for 'prompta export get'."""
    from .commands.export import get_command
    ctx.invoke(get_command, identifier=identifier, project=project, output=output, api_key=api_key)


@cli.command(hidden=True)
@click.option("--query", help="Search term for name or description")
@click.option("--tags", help="Filter by tags (comma-separated)")
@click.option("--location", help="Filter by location")
@click.option("--page", type=int, default=1, help="Page number (default: 1)")
@click.option("--page-size", type=int, default=20, help="Items per page (default: 20)")
@click.option("--api-key", help="API key to use for this request")
@click.pass_context
def list(ctx, query, tags, location, page, page_size, api_key):
    """Alias for 'prompta prompt list'."""
    from .commands.prompts import list_command
    ctx.invoke(list_command, query=query, tags=tags, location=location, page=page, page_size=page_size, api_key=api_key)


@cli.command(hidden=True)
@click.argument("identifier")
@click.option("--version", "-v", type=int, help="Show specific version (defaults to current)")
@click.option("--no-syntax", is_flag=True, help="Disable syntax highlighting")
@click.option("--project-id", help="Project ID (required if multiple prompts have the same name)")
@click.option("--api-key", help="API key to use for this request")
@click.pass_context
def show(ctx, identifier, version, no_syntax, project_id, api_key):
    """Alias for 'prompta prompt show'."""
    from .commands.prompts import show_command
    ctx.invoke(show_command, identifier=identifier, version=version, no_syntax=no_syntax, project_id=project_id, api_key=api_key)


if __name__ == "__main__":
    cli()