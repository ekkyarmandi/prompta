"""Prompt management commands for Prompta CLI."""

import shutil
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


@click.group(invoke_without_command=True)
@click.pass_context
def prompt_group(ctx):
    """Prompt management commands.
    
    Create, update, and manage prompts with version control.
    
    Common commands:
      prompta prompt list               # List all prompts
      prompta prompt show <name>        # Show prompt content
      prompta prompt create <file>      # Create prompt from file
      prompta prompt search <query>     # Search prompts by content
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@prompt_group.command("list")
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

        # Calculate offset from page and page_size
        offset = (page - 1) * page_size

        # Use search if query is provided, otherwise use regular get_prompts
        if query:
            # Use search function for query-based searches
            prompts = client.search_prompts(query)

            # Apply additional filters client-side if needed
            if tag_list:
                prompts = [
                    p
                    for p in prompts
                    if any(tag in p.get("tags", []) for tag in tag_list)
                ]
            if location:
                prompts = [
                    p
                    for p in prompts
                    if location.lower() in p.get("location", "").lower()
                ]

            # Apply pagination client-side for search results
            total = len(prompts)
            start_idx = offset
            end_idx = start_idx + page_size
            prompts = prompts[start_idx:end_idx]
            total_pages = (total + page_size - 1) // page_size
        else:
            # Use regular get_prompts with filters
            prompts = client.get_prompts(
                tags=tag_list if tag_list is not None else None,
                location=location,
                limit=page_size,
                offset=offset,
            )

            # For regular get_prompts, we don't get total count info
            # so we'll estimate based on returned results
            total = len(prompts) + offset  # This is an estimate
            total_pages = page if len(prompts) == page_size else page

        if not prompts:
            click.echo("No prompts found.")
            return

        # Calculate dynamic column widths based on content and terminal width
        # Prepare data for width calculation
        table_data = []
        for prompt in prompts:
            tags_str = ", ".join(prompt.get("tags", []))
            version = prompt.get("current_version", {}).get("version_number", "N/A")
            table_data.append(
                {
                    "name": prompt["name"],
                    "location": prompt["location"],
                    "tags": tags_str,
                    "version": str(version),
                }
            )

        # Get terminal width, default to 120 if not available
        try:
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 120

        # Set maximum table width (leave some margin)
        max_table_width = min(terminal_width - 4, 140)

        # Calculate initial column widths based on content
        name_width = max(len("Name"), max(len(row["name"]) for row in table_data), 12)
        location_width = max(
            len("Location"), max(len(row["location"]) for row in table_data), 10
        )
        tags_width = max(len("Tags"), max(len(row["tags"]) for row in table_data), 8)
        version_width = max(
            len("Version"), max(len(row["version"]) for row in table_data), 7
        )

        # Calculate separator width (│ + spaces)
        separator_width = 9  # 3 separators × 3 chars each
        total_content_width = (
            name_width + location_width + tags_width + version_width + separator_width
        )

        # If table is too wide, redistribute space
        if total_content_width > max_table_width:
            available_width = (
                max_table_width - separator_width - version_width
            )  # Keep version width fixed

            # Set minimum widths
            min_name_width = 15
            min_location_width = 12
            min_tags_width = 10

            # Calculate proportional widths
            total_min = min_name_width + min_location_width + min_tags_width
            remaining_width = available_width - total_min

            if remaining_width > 0:
                # Distribute remaining width proportionally
                name_extra = int(remaining_width * 0.35)  # 35% for name
                location_extra = int(remaining_width * 0.35)  # 35% for location
                tags_extra = (
                    remaining_width - name_extra - location_extra
                )  # remainder for tags

                name_width = min_name_width + name_extra
                location_width = min_location_width + location_extra
                tags_width = min_tags_width + tags_extra
            else:
                # Use minimum widths
                name_width = min_name_width
                location_width = min_location_width
                tags_width = min_tags_width
        else:
            # Apply reasonable maximum limits when there's plenty of space
            name_width = min(name_width, 35)
            location_width = min(location_width, 40)
            tags_width = min(tags_width, 45)

        # Display table header
        click.echo(
            f"{'Name':<{name_width}} │ {'Location':<{location_width}} │ {'Tags':<{tags_width}} │ {'Version':<{version_width}}"
        )
        click.echo(
            "─" * name_width
            + "─┼─"
            + "─" * location_width
            + "─┼─"
            + "─" * tags_width
            + "─┼─"
            + "─" * version_width
            + "─"
        )

        # Helper function for smart text truncation
        def smart_truncate(text: str, max_width: int) -> str:
            """Truncate text smartly, preferring word boundaries."""
            if len(text) <= max_width:
                return text

            if max_width <= 3:
                return "..."

            # Try to break at word boundary
            truncated = text[: max_width - 3]
            last_space = truncated.rfind(" ")

            # If we found a space and it's not too close to the beginning, use it
            if last_space > max_width * 0.6:
                return truncated[:last_space] + "..."
            else:
                return truncated + "..."

        # Display table rows
        for row in table_data:
            # Smart truncation for each field
            name = smart_truncate(row["name"], name_width)
            location = smart_truncate(row["location"], location_width)
            tags = smart_truncate(row["tags"], tags_width)
            version = row["version"][:version_width]  # Version should be short anyway

            click.echo(
                f"{name:<{name_width}} │ {location:<{location_width}} │ {tags:<{tags_width}} │ {version:<{version_width}}"
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


@prompt_group.group("version")
def version_group():
    """Version management commands for prompts."""
    pass


@version_group.command("list")
@click.argument("identifier")
@click.option("--project-id", help="Project ID (required if multiple prompts have the same name)")
@click.option("--api-key", help="API key to use for this request")
def list_versions_command(
    identifier: str,
    project_id: Optional[str],
    api_key: Optional[str],
):
    """List all versions of a prompt."""
    try:
        client = get_authenticated_client(api_key)
        prompt = client.get_prompt(identifier, project_id)
        versions = client.get_versions(prompt["id"])

        if not versions:
            click.echo("No versions found.")
            return

        click.echo(f"📄 Versions for prompt '{prompt['name']}':")
        click.echo()

        for version in versions:
            current = "✓" if version["is_current"] else " "
            click.echo(f"  {current} Version {version['version_number']}")
            click.echo(f"    Created: {version['created_at']}")
            if version.get("commit_message"):
                click.echo(f"    Message: {version['commit_message']}")
            click.echo()

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


@version_group.command("show")
@click.argument("identifier")
@click.argument("version_number", type=int)
@click.option("--project-id", help="Project ID (required if multiple prompts have the same name)")
@click.option("--no-syntax", is_flag=True, help="Disable syntax highlighting")
@click.option("--api-key", help="API key to use for this request")
def show_version_command(
    identifier: str,
    version_number: int,
    project_id: Optional[str],
    no_syntax: bool,
    api_key: Optional[str],
):
    """Show content of a specific version."""
    try:
        from rich.console import Console
        from rich.syntax import Syntax
        from rich.panel import Panel

        client = get_authenticated_client(api_key)
        prompt = client.get_prompt(identifier, project_id)
        
        # Get specific version
        versions = client.get_versions(prompt["id"])
        version_data = next(
            (v for v in versions if v["version_number"] == version_number), None
        )
        
        if not version_data:
            click.echo(
                f"❌ Version {version_number} not found for prompt '{identifier}'",
                err=True,
            )
            raise click.ClickException("Version not found")

        console = Console()

        # Display version header
        header = f"📄 {prompt['name']} - Version {version_number}"
        if version_data.get("commit_message"):
            header += f"\n{version_data['commit_message']}"

        console.print(Panel(header, style="bold blue"))

        # Display metadata
        metadata = []
        metadata.append(f"📍 Location: {prompt['location']}")
        metadata.append(f"📅 Created: {version_data['created_at']}")
        metadata.append(f"🔄 Current: {'Yes' if version_data['is_current'] else 'No'}")

        console.print("\n".join(metadata))
        console.print()

        # Display content with syntax highlighting
        content = version_data["content"]
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
                ".cursorrules": "text",
            }

            lexer = lexer_map.get(file_ext, "text")

            if prompt["location"].endswith(".cursorrules") or "cursor" in prompt.get("tags", []):
                lexer = "markdown"

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
        click.echo(f"📄 {prompt['name']} - Version {version_number}")
        if version_data.get("commit_message"):
            click.echo(f"Message: {version_data['commit_message']}")
        click.echo(f"Created: {version_data['created_at']}")
        click.echo()
        click.echo(content)


@version_group.command("create")
@click.argument("identifier")
@click.argument("file_path")
@click.option("--message", "-m", help="Commit message for this version")
@click.option("--project-id", help="Project ID (required if multiple prompts have the same name)")
@click.option("--api-key", help="API key to use for this request")
def create_version_command(
    identifier: str,
    file_path: str,
    message: Optional[str],
    project_id: Optional[str],
    api_key: Optional[str],
):
    """Create a new version from a file."""
    try:
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            click.echo(f"❌ File not found: {file_path}", err=True)
            raise click.ClickException("File not found")

        # Read file content
        with open(file_path_obj, "r") as f:
            content = f.read()

        client = get_authenticated_client(api_key)
        prompt = client.get_prompt(identifier, project_id)

        # Create version data
        version_data = {
            "content": content,
            "commit_message": message or f"Updated from {file_path}",
        }

        version = client.create_version(prompt["id"], version_data)
        click.echo(f"✅ Created version {version['version_number']} for '{prompt['name']}'")

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


@version_group.command("restore")
@click.argument("identifier")
@click.argument("version_number", type=int)
@click.option("--message", "-m", help="Commit message for the restore")
@click.option("--project-id", help="Project ID (required if multiple prompts have the same name)")
@click.option("--api-key", help="API key to use for this request")
def restore_version_command(
    identifier: str,
    version_number: int,
    message: Optional[str],
    project_id: Optional[str],
    api_key: Optional[str],
):
    """Restore a prompt to a specific version."""
    try:
        client = get_authenticated_client(api_key)
        prompt = client.get_prompt(identifier, project_id)

        # Confirm restore
        if not click.confirm(f"Restore '{prompt['name']}' to version {version_number}?"):
            click.echo("Cancelled.")
            return

        restore_data = {
            "version_number": version_number,
            "commit_message": message or f"Restored to version {version_number}",
        }

        new_version = client.restore_version(prompt["id"], version_number, restore_data)
        click.echo(f"✅ Restored '{prompt['name']}' to version {version_number}")
        click.echo(f"   Created new version {new_version['version_number']}")

    except NotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Prompt or version not found")
    except ValidationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Multiple prompts found")
    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@version_group.command("diff")
@click.argument("identifier")
@click.argument("version1", type=int)
@click.argument("version2", type=int)
@click.option("--project-id", help="Project ID (required if multiple prompts have the same name)")
@click.option("--api-key", help="API key to use for this request")
def diff_command(
    identifier: str,
    version1: int,
    version2: int,
    project_id: Optional[str],
    api_key: Optional[str],
):
    """Compare two versions of a prompt."""
    try:
        client = get_authenticated_client(api_key)
        prompt = client.get_prompt(identifier, project_id)

        diff = client.compare_versions(prompt["id"], version1, version2)
        
        if not diff:
            click.echo("❌ One or both versions not found", err=True)
            raise click.ClickException("Version not found")

        click.echo(f"📄 Diff for '{prompt['name']}' (v{version1} → v{version2}):")
        click.echo("=" * 60)
        click.echo(diff)

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


@prompt_group.command("get")
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


@prompt_group.command("show")
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


@prompt_group.command("create")
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
    """Create a prompt from a local file."""
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

        click.echo(f"✅ Created prompt '{prompt_name}' successfully (ID: {prompt['id']})")

    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@prompt_group.command("delete")
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


@prompt_group.command("info")
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


@prompt_group.command("search")
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
