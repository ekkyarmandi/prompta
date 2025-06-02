"""Prompt management commands for Prompta CLI."""

from pathlib import Path
from typing import List, Optional

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


@click.group()
def prompts_group():
    """Prompt management commands for creating, updating, and managing prompts."""
    pass


@click.command()
@click.option("--query", help="Search term for name or description")
@click.option("--tags", help="Filter by tags (comma-separated)")
@click.option("--location", help="Filter by location")
@click.option("--page", type=int, default=1, help="Page number (default: 1)")
@click.option("--page-size", type=int, default=20, help="Items per page (default: 20)")
@click.option("--api-key", help="API key to use for this request")
def list_command(
    query: Optional[str],
    tags: Optional[str],
    location: Optional[str],
    page: int,
    page_size: int,
    api_key: Optional[str],
):
    """List all prompts with search and filtering options."""
    try:
        client = get_authenticated_client(api_key)

        # Parse tags as a list for API compatibility
        tag_list = None
        if tags:
            # API expects a list of strings, not a single comma-separated string
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Attempt to get paginated prompts
        response = client.get_prompts(
            query=query,
            tags=tag_list if tag_list is not None else None,
            location=location,
            page=page,
            page_size=page_size,
        )

        # Support both paginated and legacy list responses
        if isinstance(response, dict):
            prompts = response.get("prompts", [])
            total = response.get("total", 0)
            total_pages = response.get("total_pages", 0)
        else:
            prompts = response
            total = len(prompts)
            total_pages = 1

        if not prompts:
            click.echo("No prompts found.")
            return

        # Display prompts in a table format
        click.echo(f"{'Name':<20} {'Location':<15} {'Tags':<20} {'Version':<8}")
        click.echo("-" * 70)

        for prompt in prompts:
            tags_str = ", ".join(prompt.get("tags", []))
            version = prompt.get("current_version", {}).get("version_number", "N/A")
            click.echo(
                f"{prompt['name']:<20} {prompt['location']:<15} {tags_str:<20} {version:<8}"
            )

        # Show pagination info if available
        if total_pages > 1:
            click.echo()
            click.echo(f"Page {page} of {total_pages} (Total: {total} prompts)")

    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@click.command()
@click.argument("identifier")
@click.option("--output", "-o", help="Output file path")
@click.option(
    "--project-id", help="Project ID (required if multiple prompts have the same name)"
)
@click.option("--api-key", help="API key to use for this request")
def get_command(
    identifier: str,
    output: Optional[str],
    project_id: Optional[str],
    api_key: Optional[str],
):
    """Download a prompt to a local file."""
    try:
        client = get_authenticated_client(api_key)
        prompt = client.get_prompt(identifier, project_id)

        # Determine output path
        if output:
            output_path = Path(output)
        else:
            # Use the helper function to properly normalize the location
            normalized_location = _normalize_prompt_location(prompt["location"])
            output_path = Path(normalized_location)

        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content to file
        content = prompt["current_version"]["content"]
        with open(output_path, "w") as f:
            f.write(content)

        click.echo(f"✅ Downloaded '{identifier}' to {output_path}")

    except NotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Prompt not found")
    except ValidationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Multiple prompts found")
    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@click.command()
@click.argument("identifier")
@click.option(
    "--version", "-v", type=int, help="Show specific version (defaults to current)"
)
@click.option("--no-syntax", is_flag=True, help="Disable syntax highlighting")
@click.option(
    "--project-id", help="Project ID (required if multiple prompts have the same name)"
)
@click.option("--api-key", help="API key to use for this request")
def show_command(
    identifier: str,
    version: Optional[int],
    no_syntax: bool,
    project_id: Optional[str],
    api_key: Optional[str],
):
    """Display prompt content in the terminal."""
    try:
        from rich.console import Console
        from rich.syntax import Syntax
        from rich.panel import Panel

        client = get_authenticated_client(api_key)
        prompt = client.get_prompt(identifier, project_id)

        # Get the content to display
        if version is not None:
            # Get specific version
            versions = client.get_versions(prompt["id"])
            version_data = next(
                (v for v in versions if v["version_number"] == version), None
            )
            if not version_data:
                click.echo(
                    f"❌ Version {version} not found for prompt '{identifier}'",
                    err=True,
                )
                raise click.ClickException("Version not found")
            content = version_data["content"]
            version_info = f"Version {version}"
        else:
            # Get current version
            content = prompt["current_version"]["content"]
            version_info = (
                f"Version {prompt['current_version']['version_number']} (current)"
            )

        console = Console()

        # Display prompt header
        header = f"📄 {prompt['name']} - {version_info}"
        if prompt.get("description"):
            header += f"\n{prompt['description']}"

        console.print(Panel(header, style="bold blue"))

        # Display metadata
        metadata = []
        metadata.append(f"📍 Location: {prompt['location']}")
        if prompt.get("tags"):
            metadata.append(f"🏷️  Tags: {', '.join(prompt['tags'])}")
        metadata.append(f"📅 Created: {prompt['created_at']}")
        metadata.append(f"🔄 Updated: {prompt['updated_at']}")

        console.print("\n".join(metadata))
        console.print()

        # Display content with syntax highlighting
        if no_syntax:
            console.print(content)
        else:
            # Try to detect file type from location for syntax highlighting
            file_ext = Path(prompt["location"]).suffix.lower()
            lexer_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".json": "json",
                ".yaml": "yaml",
                ".yml": "yaml",
                ".md": "markdown",
                ".sh": "bash",
                ".bash": "bash",
                ".zsh": "bash",
                ".fish": "fish",
                ".toml": "toml",
                ".ini": "ini",
                ".cfg": "ini",
                ".conf": "ini",
                ".xml": "xml",
                ".html": "html",
                ".css": "css",
                ".sql": "sql",
                ".dockerfile": "dockerfile",
                ".gitignore": "gitignore",
                ".cursorrules": "text",  # Special case for cursor rules
            }

            lexer = lexer_map.get(file_ext, "text")

            # Special handling for common prompt files
            if prompt["location"].endswith(".cursorrules") or "cursor" in prompt.get(
                "tags", []
            ):
                lexer = "markdown"  # Cursor rules often contain markdown-like content

            syntax = Syntax(content, lexer, theme="monokai", line_numbers=True)
            console.print(syntax)

    except NotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Prompt not found")
    except ValidationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Multiple prompts found")
    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")
    except ImportError:
        # Fallback if rich is not available
        click.echo(f"📄 {prompt['name']} - {version_info}")
        if prompt.get("description"):
            click.echo(f"{prompt['description']}")
        click.echo(f"Location: {prompt['location']}")
        if prompt.get("tags"):
            click.echo(f"Tags: {', '.join(prompt['tags'])}")
        click.echo()
        click.echo(content)


@prompts_group.command("save")
@click.argument("file_path")
@click.option("--name", help="Name for the prompt (defaults to filename)")
@click.option("--description", help="Description for the prompt")
@click.option("--tags", help="Tags for the prompt (comma-separated)")
@click.option("--message", help="Commit message for this version")
@click.option("--api-key", help="API key to use for this request")
def save_command(
    file_path: str,
    name: Optional[str],
    description: Optional[str],
    tags: Optional[str],
    message: Optional[str],
    api_key: Optional[str],
):
    """Upload a file as a prompt."""
    try:
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            click.echo(f"❌ File not found: {file_path}", err=True)
            raise click.ClickException("File not found")

        # Read file content
        with open(file_path_obj, "r") as f:
            content = f.read()

        # Determine prompt name
        prompt_name = name or file_path_obj.name

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]

        # Create prompt data
        prompt_data = {
            "name": prompt_name,
            "description": description,
            "location": str(file_path_obj),
            "tags": tag_list,
            "content": content,
            "commit_message": message,
        }

        client = get_authenticated_client(api_key)
        prompt = client.create_prompt(prompt_data)

        click.echo(f"✅ Saved '{prompt_name}' successfully!")

    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@prompts_group.command("delete")
@click.argument("name")
@click.option("--api-key", help="API key to use for this request")
def delete_command(name: str, api_key: Optional[str]):
    """Delete a prompt."""
    try:
        client = get_authenticated_client(api_key)
        prompt = client.get_prompt_by_name(name)

        # Confirm deletion
        if not click.confirm(f"Are you sure you want to delete '{name}'?"):
            click.echo("Cancelled.")
            return

        client.delete_prompt(prompt["id"])
        click.echo(f"✅ Deleted '{name}' successfully!")

    except NotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Prompt not found")
    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@prompts_group.command("info")
@click.argument("name")
@click.option("--api-key", help="API key to use for this request")
def info_command(name: str, api_key: Optional[str]):
    """Show prompt details."""
    try:
        client = get_authenticated_client(api_key)
        prompt = client.get_prompt_by_name(name)

        # Display prompt information
        click.echo(f"Name: {prompt['name']}")
        click.echo(f"Description: {prompt.get('description', 'N/A')}")
        click.echo(f"Location: {prompt['location']}")
        click.echo(f"Tags: {', '.join(prompt.get('tags', []))}")
        click.echo(f"Created: {prompt['created_at']}")
        click.echo(f"Updated: {prompt['updated_at']}")

        current_version = prompt.get("current_version", {})
        if current_version:
            click.echo(
                f"Current Version: {current_version.get('version_number', 'N/A')}"
            )
            click.echo(f"Version Created: {current_version.get('created_at', 'N/A')}")

    except NotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Prompt not found")
    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@prompts_group.command("search")
@click.argument("query")
@click.option("--api-key", help="API key to use for this request")
def search_command(query: str, api_key: Optional[str]):
    """Search prompts by content."""
    try:
        client = get_authenticated_client(api_key)
        prompts = client.search_prompts(query)

        if not prompts:
            click.echo("No prompts found matching your search.")
            return

        # Display search results
        click.echo(f"Found {len(prompts)} prompt(s):")
        click.echo()

        for prompt in prompts:
            click.echo(f"📄 {prompt['name']}")
            if prompt.get("description"):
                click.echo(f"   {prompt['description']}")
            click.echo(f"   Location: {prompt['location']}")
            if prompt.get("tags"):
                click.echo(f"   Tags: {', '.join(prompt['tags'])}")
            click.echo()

    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")
