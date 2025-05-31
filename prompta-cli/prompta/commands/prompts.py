"""Prompt management commands for Prompta CLI."""

from pathlib import Path
from typing import List, Optional

import click

from ..exceptions import AuthenticationError, NotFoundError, PromptaAPIError
from ..utils.auth import get_authenticated_client


@click.group()
def prompts_group():
    """Prompt management commands for creating, updating, and managing prompts."""
    pass


@prompts_group.command("list")
@click.option("--tags", help="Filter by tags (comma-separated)")
@click.option("--location", help="Filter by location")
@click.option("--api-key", help="API key to use for this request")
def list_command(tags: Optional[str], location: Optional[str], api_key: Optional[str]):
    """List all prompts."""
    try:
        client = get_authenticated_client(api_key)

        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]

        prompts = client.get_prompts(tags=tag_list, location=location)

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

    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@prompts_group.command("get")
@click.argument("name")
@click.option("--output", "-o", help="Output file path")
@click.option("--api-key", help="API key to use for this request")
def get_command(name: str, output: Optional[str], api_key: Optional[str]):
    """Download a prompt to a local file."""
    try:
        client = get_authenticated_client(api_key)
        prompt = client.get_prompt_by_name(name)

        # Determine output path
        output_path = Path(output) if output else Path(prompt["location"])

        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content to file
        content = prompt["current_version"]["content"]
        with open(output_path, "w") as f:
            f.write(content)

        click.echo(f"✅ Downloaded '{name}' to {output_path}")

    except NotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Prompt not found")
    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@prompts_group.command("show")
@click.argument("name")
@click.option(
    "--version", "-v", type=int, help="Show specific version (defaults to current)"
)
@click.option("--no-syntax", is_flag=True, help="Disable syntax highlighting")
@click.option("--api-key", help="API key to use for this request")
def show_command(
    name: str, version: Optional[int], no_syntax: bool, api_key: Optional[str]
):
    """Display prompt content in the terminal."""
    try:
        from rich.console import Console
        from rich.syntax import Syntax
        from rich.panel import Panel

        client = get_authenticated_client(api_key)
        prompt = client.get_prompt_by_name(name)

        # Get the content to display
        if version is not None:
            # Get specific version
            versions = client.get_versions(prompt["id"])
            version_data = next(
                (v for v in versions if v["version_number"] == version), None
            )
            if not version_data:
                click.echo(
                    f"❌ Version {version} not found for prompt '{name}'", err=True
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


@prompts_group.command("download")
@click.option("--project", help="Filter by project name")
@click.option("--directory", help="Filter by directory pattern")
@click.option("--tags", help="Filter by tags (comma-separated)")
@click.option("--output", "-o", help="Output directory (defaults to current directory)")
@click.option(
    "--format",
    type=click.Choice(["json", "zip"]),
    default="json",
    help="Download format",
)
@click.option(
    "--no-content", is_flag=True, help="Exclude prompt content from JSON response"
)
@click.option("--api-key", help="API key to use for this request")
def download_command(
    project: Optional[str],
    directory: Optional[str],
    tags: Optional[str],
    output: Optional[str],
    format: str,
    no_content: bool,
    api_key: Optional[str],
):
    """Download prompts with filtering options."""
    try:
        from tqdm import tqdm
        import json
        import zipfile
        import io

        client = get_authenticated_client(api_key)

        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]

        # Set output directory
        output_dir = Path(output) if output else Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        if format == "zip":
            # Download as ZIP
            click.echo("📦 Downloading prompts as ZIP...")
            zip_content = client.download_prompts_zip(
                project_name=project, directory=directory, tags=tag_list
            )

            # Generate filename
            filename_parts = []
            if project:
                filename_parts.append(f"project-{project}")
            if directory:
                filename_parts.append(f"dir-{directory.replace('/', '-')}")
            if tag_list:
                filename_parts.append(f"tags-{'-'.join(tag_list)}")

            if not filename_parts:
                filename_parts.append("all-prompts")

            filename = f"prompta-prompts-{'-'.join(filename_parts)}.zip"
            zip_path = output_dir / filename

            with open(zip_path, "wb") as f:
                f.write(zip_content)

            click.echo(f"✅ Downloaded ZIP file to {zip_path}")

        else:
            # Download as JSON
            click.echo("📄 Downloading prompts as JSON...")
            response = client.download_prompts(
                project_name=project,
                directory=directory,
                tags=tag_list,
                include_content=not no_content,
                format="json",
            )

            prompts = response.get("prompts", [])
            total = response.get("total", 0)
            filters_applied = response.get("filters_applied", {})

            if total == 0:
                click.echo("No prompts found matching the criteria.")
                return

            # Generate filename
            filename_parts = []
            if project:
                filename_parts.append(f"project-{project}")
            if directory:
                filename_parts.append(f"dir-{directory.replace('/', '-')}")
            if tag_list:
                filename_parts.append(f"tags-{'-'.join(tag_list)}")

            if not filename_parts:
                filename_parts.append("all-prompts")

            filename = f"prompta-prompts-{'-'.join(filename_parts)}.json"
            json_path = output_dir / filename

            # Save JSON file
            with open(json_path, "w") as f:
                json.dump(response, f, indent=2, default=str)

            click.echo(f"✅ Downloaded {total} prompt(s) to {json_path}")

            # Show applied filters
            if filters_applied:
                click.echo("\nFilters applied:")
                for key, value in filters_applied.items():
                    if value:
                        click.echo(f"  {key}: {value}")

            # Optionally save individual files
            if not no_content and click.confirm("\nSave individual prompt files?"):
                prompts_dir = output_dir / "prompts"
                prompts_dir.mkdir(exist_ok=True)

                with tqdm(total=len(prompts), desc="Saving files") as pbar:
                    for prompt in prompts:
                        if prompt.get("current_version", {}).get("content"):
                            # Create safe filename
                            safe_name = "".join(
                                c
                                for c in prompt["name"]
                                if c.isalnum() or c in (" ", "-", "_")
                            ).rstrip()
                            file_path = prompts_dir / f"{safe_name}.txt"

                            # Add metadata header
                            metadata = f"""# Prompt: {prompt['name']}
# Description: {prompt.get('description', 'No description')}
# Location: {prompt['location']}
# Tags: {', '.join(prompt.get('tags', [])) if prompt.get('tags') else 'No tags'}
# Created: {prompt['created_at']}
# Updated: {prompt['updated_at']}
# Version: {prompt['current_version']['version_number']}

"""
                            content = metadata + prompt["current_version"]["content"]

                            with open(file_path, "w") as f:
                                f.write(content)

                        pbar.update(1)

                click.echo(f"✅ Saved individual files to {prompts_dir}")

    except ImportError:
        click.echo(
            "❌ Missing required dependency 'tqdm'. Install with: pip install tqdm",
            err=True,
        )
        raise click.ClickException("Missing dependency")
    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except NotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("No prompts found")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@prompts_group.command("download-project")
@click.argument("project_name")
@click.option("--output", "-o", help="Output directory (defaults to current directory)")
@click.option("--no-content", is_flag=True, help="Exclude prompt content from response")
@click.option("--api-key", help="API key to use for this request")
def download_project_command(
    project_name: str,
    output: Optional[str],
    no_content: bool,
    api_key: Optional[str],
):
    """Download all prompts from a specific project."""
    try:
        import json
        from tqdm import tqdm

        client = get_authenticated_client(api_key)

        # Set output directory
        output_dir = Path(output) if output else Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        click.echo(f"📄 Downloading prompts from project '{project_name}'...")
        response = client.download_prompts_by_project(
            project_name=project_name, include_content=not no_content
        )

        prompts = response.get("prompts", [])
        total = response.get("total", 0)

        if total == 0:
            click.echo(f"No prompts found in project '{project_name}'.")
            return

        # Save JSON file
        filename = f"prompta-project-{project_name}.json"
        json_path = output_dir / filename

        with open(json_path, "w") as f:
            json.dump(response, f, indent=2, default=str)

        click.echo(
            f"✅ Downloaded {total} prompt(s) from project '{project_name}' to {json_path}"
        )

        # Optionally save individual files
        if not no_content and click.confirm("\nSave individual prompt files?"):
            project_dir = output_dir / f"project-{project_name}"
            project_dir.mkdir(exist_ok=True)

            with tqdm(total=len(prompts), desc="Saving files") as pbar:
                for prompt in prompts:
                    if prompt.get("current_version", {}).get("content"):
                        # Create safe filename
                        safe_name = "".join(
                            c
                            for c in prompt["name"]
                            if c.isalnum() or c in (" ", "-", "_")
                        ).rstrip()
                        file_path = project_dir / f"{safe_name}.txt"

                        # Add metadata header
                        metadata = f"""# Prompt: {prompt['name']}
# Description: {prompt.get('description', 'No description')}
# Location: {prompt['location']}
# Tags: {', '.join(prompt.get('tags', [])) if prompt.get('tags') else 'No tags'}
# Created: {prompt['created_at']}
# Updated: {prompt['updated_at']}
# Version: {prompt['current_version']['version_number']}

"""
                        content = metadata + prompt["current_version"]["content"]

                        with open(file_path, "w") as f:
                            f.write(content)

                    pbar.update(1)

            click.echo(f"✅ Saved individual files to {project_dir}")

    except ImportError:
        click.echo(
            "❌ Missing required dependency 'tqdm'. Install with: pip install tqdm",
            err=True,
        )
        raise click.ClickException("Missing dependency")
    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except NotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Project not found")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@prompts_group.command("download-directory")
@click.argument("directory_pattern")
@click.option("--output", "-o", help="Output directory (defaults to current directory)")
@click.option("--no-content", is_flag=True, help="Exclude prompt content from response")
@click.option("--api-key", help="API key to use for this request")
def download_directory_command(
    directory_pattern: str,
    output: Optional[str],
    no_content: bool,
    api_key: Optional[str],
):
    """Download all prompts from a specific directory pattern."""
    try:
        import json
        from tqdm import tqdm

        client = get_authenticated_client(api_key)

        # Set output directory
        output_dir = Path(output) if output else Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        click.echo(
            f"📄 Downloading prompts from directory pattern '{directory_pattern}'..."
        )
        response = client.download_prompts_by_directory(
            directory=directory_pattern, include_content=not no_content
        )

        prompts = response.get("prompts", [])
        total = response.get("total", 0)

        if total == 0:
            click.echo(
                f"No prompts found matching directory pattern '{directory_pattern}'."
            )
            return

        # Save JSON file
        safe_dir_name = directory_pattern.replace("/", "-").replace("*", "wildcard")
        filename = f"prompta-directory-{safe_dir_name}.json"
        json_path = output_dir / filename

        with open(json_path, "w") as f:
            json.dump(response, f, indent=2, default=str)

        click.echo(
            f"✅ Downloaded {total} prompt(s) from directory '{directory_pattern}' to {json_path}"
        )

        # Optionally save individual files
        if not no_content and click.confirm("\nSave individual prompt files?"):
            dir_name = f"directory-{safe_dir_name}"
            prompts_dir = output_dir / dir_name
            prompts_dir.mkdir(exist_ok=True)

            with tqdm(total=len(prompts), desc="Saving files") as pbar:
                for prompt in prompts:
                    if prompt.get("current_version", {}).get("content"):
                        # Create safe filename
                        safe_name = "".join(
                            c
                            for c in prompt["name"]
                            if c.isalnum() or c in (" ", "-", "_")
                        ).rstrip()
                        file_path = prompts_dir / f"{safe_name}.txt"

                        # Add metadata header
                        metadata = f"""# Prompt: {prompt['name']}
# Description: {prompt.get('description', 'No description')}
# Location: {prompt['location']}
# Tags: {', '.join(prompt.get('tags', [])) if prompt.get('tags') else 'No tags'}
# Created: {prompt['created_at']}
# Updated: {prompt['updated_at']}
# Version: {prompt['current_version']['version_number']}

"""
                        content = metadata + prompt["current_version"]["content"]

                        with open(file_path, "w") as f:
                            f.write(content)

                    pbar.update(1)

            click.echo(f"✅ Saved individual files to {prompts_dir}")

    except ImportError:
        click.echo(
            "❌ Missing required dependency 'tqdm'. Install with: pip install tqdm",
            err=True,
        )
        raise click.ClickException("Missing dependency")
    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except NotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Directory not found")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@prompts_group.command("download-tags")
@click.argument("tags")
@click.option("--output", "-o", help="Output directory (defaults to current directory)")
@click.option("--no-content", is_flag=True, help="Exclude prompt content from response")
@click.option("--api-key", help="API key to use for this request")
def download_tags_command(
    tags: str,
    output: Optional[str],
    no_content: bool,
    api_key: Optional[str],
):
    """Download all prompts matching specific tags (comma-separated)."""
    try:
        import json
        from tqdm import tqdm

        client = get_authenticated_client(api_key)

        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")]

        # Set output directory
        output_dir = Path(output) if output else Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        click.echo(f"📄 Downloading prompts with tags: {', '.join(tag_list)}...")
        response = client.download_prompts_by_tags(
            tags=tag_list, include_content=not no_content
        )

        prompts = response.get("prompts", [])
        total = response.get("total", 0)

        if total == 0:
            click.echo(f"No prompts found with tags: {', '.join(tag_list)}.")
            return

        # Save JSON file
        filename = f"prompta-tags-{'-'.join(tag_list)}.json"
        json_path = output_dir / filename

        with open(json_path, "w") as f:
            json.dump(response, f, indent=2, default=str)

        click.echo(
            f"✅ Downloaded {total} prompt(s) with tags '{', '.join(tag_list)}' to {json_path}"
        )

        # Optionally save individual files
        if not no_content and click.confirm("\nSave individual prompt files?"):
            tags_dir = output_dir / f"tags-{'-'.join(tag_list)}"
            tags_dir.mkdir(exist_ok=True)

            with tqdm(total=len(prompts), desc="Saving files") as pbar:
                for prompt in prompts:
                    if prompt.get("current_version", {}).get("content"):
                        # Create safe filename
                        safe_name = "".join(
                            c
                            for c in prompt["name"]
                            if c.isalnum() or c in (" ", "-", "_")
                        ).rstrip()
                        file_path = tags_dir / f"{safe_name}.txt"

                        # Add metadata header
                        metadata = f"""# Prompt: {prompt['name']}
# Description: {prompt.get('description', 'No description')}
# Location: {prompt['location']}
# Tags: {', '.join(prompt.get('tags', [])) if prompt.get('tags') else 'No tags'}
# Created: {prompt['created_at']}
# Updated: {prompt['updated_at']}
# Version: {prompt['current_version']['version_number']}

"""
                        content = metadata + prompt["current_version"]["content"]

                        with open(file_path, "w") as f:
                            f.write(content)

                    pbar.update(1)

            click.echo(f"✅ Saved individual files to {tags_dir}")

    except ImportError:
        click.echo(
            "❌ Missing required dependency 'tqdm'. Install with: pip install tqdm",
            err=True,
        )
        raise click.ClickException("Missing dependency")
    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except NotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Tags not found")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")
