"""Project management commands for Prompta CLI."""

import os
import json
from pathlib import Path
from typing import Optional

import click

from ..exceptions import (
    AuthenticationError,
    NotFoundError,
    PromptaAPIError,
    ValidationError,
)
from ..utils.auth import get_authenticated_client


def _normalize_prompt_location(location: str) -> str:
    """
    Normalize prompt location for file system use.

    Handles:
    - Tilde replacement (~/path -> ./path)
    - Preserves leading dots for hidden directories (.cursor/rules/file.md)
    - Removes explicit "./" prefix only

    Args:
        location: The original location from the prompt

    Returns:
        Normalized path suitable for file system operations
    """
    if location.startswith("~"):
        # Replace tilde with current directory prefix
        location = "./" + location[1:].lstrip("/")

    # Remove explicit "./" prefix but preserve other leading dots
    if location.startswith("./"):
        return location[2:]

    return location


@click.group(invoke_without_command=True)
@click.pass_context
def project_group(ctx):
    """Project management commands.
    
    Manage projects and download project files.
    
    Common commands:
      prompta project list              # List all projects
      prompta project show <name>       # Show project details
      prompta project download <name>   # Download project files
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@project_group.command("list")
@click.option("--query", help="Search term for name or description")
@click.option("--tags", help="Filter by tags (comma-separated)")
@click.option("--page", type=int, default=1, help="Page number (default: 1)")
@click.option("--page-size", type=int, default=20, help="Items per page (default: 20)")
@click.option("--api-key", help="API key to use for this request")
def list_command(
    query: Optional[str],
    tags: Optional[str],
    page: int,
    page_size: int,
    api_key: Optional[str],
):
    """List projects with search and filtering options."""
    try:
        client = get_authenticated_client(api_key)

        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]

        response = client.get_projects(
            query=query,
            tags=tag_list,
            page=page,
            page_size=page_size,
        )

        projects = response.get("projects", [])
        total = response.get("total", 0)
        total_pages = response.get("total_pages", 0)

        if not projects:
            click.echo("No projects found.")
            return

        # Display projects in a table format
        click.echo(f"{'ID':<36} {'Name':<30} {'Description':<40} {'Tags':<30}")
        click.echo("-" * 136)

        for project in projects:
            project_id = project["id"]
            name = (
                project["name"][:29] if len(project["name"]) > 29 else project["name"]
            )
            description = (
                project.get("description", "")[:39]
                if project.get("description")
                else ""
            )
            tags_str = ", ".join(project.get("tags", []))[:29]
            click.echo(f"{project_id:<36} {name:<30} {description:<40} {tags_str:<30}")

        # Show pagination info
        if total_pages > 1:
            click.echo()
            click.echo(f"Page {page} of {total_pages} (Total: {total} projects)")

    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@project_group.command("download")
@click.argument("identifier")
@click.option("--output", "-o", help="Output directory or file path")
@click.option("--api-key", help="API key to use for this request")
def download_command(
    identifier: str,
    output: Optional[str],
    api_key: Optional[str],
):
    """Download entire project by name or ID.

    Usage examples:
      prompta project download my-project      # Download project by name
      prompta project download {project_id}   # Download project by ID

    Note: If multiple projects have the same name, you must use the project ID.
    Use 'prompta project list' to list all projects with their IDs.
    """
    try:
        client = get_authenticated_client(api_key)

        # Try to determine what type of identifier this is
        # UUIDs are 36 characters with 4 dashes
        if len(identifier) == 36 and identifier.count("-") == 4:
            # Looks like a UUID - download project by ID
            try:
                return _download_project_by_id(client, identifier, output)
            except NotFoundError:
                click.echo(
                    f"❌ No project found with ID '{identifier}'.",
                    err=True,
                )
                raise click.ClickException("Project not found")
        else:
            # Try project name
            try:
                return _download_project_by_name(client, identifier, output)
            except NotFoundError:
                click.echo(
                    f"❌ No project found with name '{identifier}'.",
                    err=True,
                )
                raise click.ClickException("Project not found")
            except click.ClickException as e:
                # If it's a "multiple projects" error, re-raise it directly
                if "Multiple projects with same name" in str(e):
                    raise e
                else:
                    click.echo(
                        f"❌ No project found with name '{identifier}'.",
                        err=True,
                    )
                    raise click.ClickException("Project not found")

    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


def _download_project_by_id(client, project_id: str, output: Optional[str]):
    """Download entire project by ID."""
    project_info = client.get_project_by_id(project_id)
    project_name = project_info["name"]

    click.echo(f"📁 Downloading project: {project_name}")
    return _download_project_prompts(client, project_name, output)


def _download_project_by_name(client, project_name: str, output: Optional[str]):
    """Download entire project by name."""
    try:
        project_info = client.get_project_by_name(project_name)
        click.echo(f"📁 Downloading project: {project_name}")
        return _download_project_prompts(client, project_name, output)
    except ValidationError as e:
        # Handle case where multiple projects have the same name
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Multiple projects found with the same name")
    except PromptaAPIError as e:
        # Check if this is a "multiple projects" error from the API
        error_msg = str(e).lower()
        if "multiple" in error_msg and "project" in error_msg:
            # Try to get a list of projects and filter by name to show options
            try:
                response = client.get_projects(query=project_name)
                projects = response.get("projects", [])
                matching_projects = [p for p in projects if p["name"] == project_name]

                if len(matching_projects) > 1:
                    click.echo(
                        f"❌ Multiple projects found with name '{project_name}':",
                        err=True,
                    )
                    click.echo("Please use the project ID instead:", err=True)
                    for project in matching_projects:
                        click.echo(
                            f"  - {project['name']} (ID: {project['id']})", err=True
                        )
                        if project.get("description"):
                            click.echo(
                                f"    Description: {project['description']}", err=True
                            )
                    click.echo("\nUsage: prompta get {project_id}", err=True)
                    raise click.ClickException("Multiple projects with same name")
            except Exception:
                # Fallback to original error
                pass

        # Re-raise original error if we couldn't handle it
        raise e


def _download_project_prompts(client, project_name: str, output: Optional[str]):
    """Download all prompts from a project."""
    response = client.download_prompts_by_project(project_name, include_content=True)
    prompts = response.get("prompts", [])

    if not prompts:
        click.echo("❌ No prompts found in this project.")
        return

    # Determine output directory
    if output:
        output_dir = Path(output)
    else:
        output_dir = Path.cwd()

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save as individual files
    downloaded_count = 0
    for prompt in prompts:
        try:
            content = prompt["current_version"]["content"]

            # Use the helper function to properly normalize the location
            normalized_location = _normalize_prompt_location(prompt["location"])
            file_path = output_dir / normalized_location

            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content to file
            with open(file_path, "w") as f:
                f.write(content)

            downloaded_count += 1
            click.echo(f"  ✓ {prompt['name']} → {file_path}")

        except Exception as e:
            click.echo(f"  ❌ Failed to download {prompt['name']}: {e}", err=True)

    click.echo(
        f"✅ Downloaded {downloaded_count} of {len(prompts)} prompts to {output_dir}"
    )



@project_group.command("create")
@click.option("--name", required=True, help="Project name")
@click.option("--description", help="Project description")
@click.option("--tags", help="Project tags (comma-separated)")
@click.option("--public", is_flag=True, help="Make project public")
@click.option("--api-key", help="API key to use for this request")
def create_command(
    name: str,
    description: Optional[str],
    tags: Optional[str],
    public: bool,
    api_key: Optional[str],
):
    """Create a new project."""
    try:
        client = get_authenticated_client(api_key)

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]

        project_data = {
            "name": name,
            "description": description,
            "tags": tag_list,
            "is_public": public,
        }

        project = client.create_project(project_data)
        click.echo(f"✅ Created project '{name}' (ID: {project['id']})")

    except ValidationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Project creation failed")
    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@project_group.command("show")
@click.argument("identifier")
@click.option("--api-key", help="API key to use for this request")
def show_command(identifier: str, api_key: Optional[str]):
    """Show detailed information about a project."""
    try:
        client = get_authenticated_client(api_key)

        # Try to get by ID first (UUIDs are 36 characters)
        if len(identifier) == 36 and identifier.count("-") == 4:
            try:
                project = client.get_project_by_id(identifier)
            except NotFoundError:
                # Fallback to name search
                project = client.get_project_by_name(identifier)
        else:
            # Get by name
            project = client.get_project_by_name(identifier)

        # Display project information
        click.echo(f"📁 Project: {project['name']}")
        click.echo(f"ID: {project['id']}")
        if project.get("description"):
            click.echo(f"Description: {project['description']}")
        if project.get("tags"):
            click.echo(f"Tags: {', '.join(project['tags'])}")
        click.echo(f"Created: {project['created_at']}")
        click.echo(f"Updated: {project['updated_at']}")
        click.echo(f"Active: {'Yes' if project.get('is_active', True) else 'No'}")
        click.echo(f"Public: {'Yes' if project.get('is_public', False) else 'No'}")

    except NotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Project not found")
    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")
