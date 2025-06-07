"""Export and download commands for Prompta CLI."""

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
def export_group(ctx):
    """Export and download commands.
    
    Download prompts, projects, and bulk export functionality.
    
    Common commands:
      prompta export project <name>     # Export entire project
      prompta export prompt <name>      # Export single prompt
      prompta export all --tags <tags>  # Export by criteria
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@export_group.command("project")
@click.argument("project_name")
@click.option("--output", "-o", help="Output directory (default: current directory)")
@click.option("--format", type=click.Choice(["files", "json"]), default="files", help="Export format")
@click.option("--include-metadata", is_flag=True, help="Include metadata in JSON export")
@click.option("--api-key", help="API key to use for this request")
def project_command(
    project_name: str,
    output: Optional[str],
    format: str,
    include_metadata: bool,
    api_key: Optional[str],
):
    """Export entire project by name.
    
    Downloads all prompts from a project either as individual files
    or as a single JSON export.
    """
    try:
        client = get_authenticated_client(api_key)
        
        click.echo(f"📁 Exporting project: {project_name}")
        
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

        if format == "json":
            # Export as JSON file
            export_data = {
                "project_name": project_name,
                "exported_at": response.get("exported_at"),
                "total_prompts": len(prompts),
                "prompts": []
            }
            
            for prompt in prompts:
                prompt_data = {
                    "name": prompt["name"],
                    "location": prompt["location"],
                    "content": prompt["current_version"]["content"]
                }
                
                if include_metadata:
                    prompt_data.update({
                        "description": prompt.get("description"),
                        "tags": prompt.get("tags", []),
                        "created_at": prompt.get("created_at"),
                        "updated_at": prompt.get("updated_at"),
                        "version_number": prompt["current_version"]["version_number"],
                        "commit_message": prompt["current_version"].get("commit_message")
                    })
                
                export_data["prompts"].append(prompt_data)
            
            # Create output directory and write JSON
            output_dir.mkdir(parents=True, exist_ok=True)
            json_file = output_dir / f"{project_name}.json"
            
            with open(json_file, "w") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            click.echo(f"✅ Exported {len(prompts)} prompts to {json_file}")
        
        else:
            # Export as individual files
            output_dir.mkdir(parents=True, exist_ok=True)
            downloaded_count = 0
            
            for prompt in prompts:
                try:
                    content = prompt["current_version"]["content"]
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
                    click.echo(f"  ❌ Failed to export {prompt['name']}: {e}", err=True)

            click.echo(f"✅ Exported {downloaded_count} of {len(prompts)} prompts to {output_dir}")

    except NotFoundError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Project not found")
    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@export_group.command("prompt")
@click.argument("identifier")
@click.option("--output", "-o", help="Output file path")
@click.option("--project-id", help="Project ID (required if multiple prompts have the same name)")
@click.option("--api-key", help="API key to use for this request")
def prompt_command(
    identifier: str,
    output: Optional[str],
    project_id: Optional[str],
    api_key: Optional[str],
):
    """Export a single prompt to a local file."""
    try:
        client = get_authenticated_client(api_key)
        prompt = client.get_prompt(identifier, project_id)

        # Determine output path
        if output:
            output_path = Path(output)
        else:
            normalized_location = _normalize_prompt_location(prompt["location"])
            output_path = Path(normalized_location)

        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content to file
        content = prompt["current_version"]["content"]
        with open(output_path, "w") as f:
            f.write(content)

        click.echo(f"✅ Exported prompt '{prompt['name']}' to {output_path}")

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


@export_group.command("all")
@click.option("--tags", help="Filter by tags (comma-separated)")
@click.option("--query", help="Search term for name or description")
@click.option("--location", help="Filter by location pattern")
@click.option("--output", "-o", help="Output directory (default: current directory)")
@click.option("--format", type=click.Choice(["files", "json"]), default="files", help="Export format")
@click.option("--include-metadata", is_flag=True, help="Include metadata in JSON export")
@click.option("--api-key", help="API key to use for this request")
def all_command(
    tags: Optional[str],
    query: Optional[str],
    location: Optional[str],
    output: Optional[str],
    format: str,
    include_metadata: bool,
    api_key: Optional[str],
):
    """Export prompts matching specified criteria.
    
    Export multiple prompts based on tags, search query, or location patterns.
    """
    try:
        client = get_authenticated_client(api_key)

        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]

        # Build filter description
        filters = []
        if query:
            filters.append(f"query: '{query}'")
        if tag_list:
            filters.append(f"tags: {', '.join(tag_list)}")
        if location:
            filters.append(f"location: '{location}'")
        
        filter_desc = ", ".join(filters) if filters else "no filters (all prompts)"
        click.echo(f"📦 Exporting prompts with {filter_desc}")

        # Get prompts using search or list depending on query
        if query:
            prompts = client.search_prompts(query)
            
            # Apply additional filters client-side
            if tag_list:
                prompts = [
                    p for p in prompts
                    if any(tag in p.get("tags", []) for tag in tag_list)
                ]
            if location:
                prompts = [
                    p for p in prompts
                    if location.lower() in p.get("location", "").lower()
                ]
        else:
            # Use regular get_prompts with filters
            prompts = client.get_prompts(
                tags=tag_list,
                location=location,
                limit=1000  # Get a large batch
            )

        if not prompts:
            click.echo("❌ No prompts found matching the specified criteria.")
            return

        # Determine output directory
        if output:
            output_dir = Path(output)
        else:
            output_dir = Path.cwd()

        if format == "json":
            # Export as JSON file
            export_data = {
                "exported_at": None,  # Could add timestamp here
                "filters": {
                    "query": query,
                    "tags": tag_list,
                    "location": location
                },
                "total_prompts": len(prompts),
                "prompts": []
            }
            
            for prompt in prompts:
                prompt_data = {
                    "name": prompt["name"],
                    "location": prompt["location"],
                    "content": prompt["current_version"]["content"]
                }
                
                if include_metadata:
                    prompt_data.update({
                        "description": prompt.get("description"),
                        "tags": prompt.get("tags", []),
                        "created_at": prompt.get("created_at"),
                        "updated_at": prompt.get("updated_at"),
                        "version_number": prompt["current_version"]["version_number"],
                        "commit_message": prompt["current_version"].get("commit_message")
                    })
                
                export_data["prompts"].append(prompt_data)
            
            # Create output directory and write JSON
            output_dir.mkdir(parents=True, exist_ok=True)
            json_file = output_dir / "prompts_export.json"
            
            with open(json_file, "w") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            click.echo(f"✅ Exported {len(prompts)} prompts to {json_file}")
        
        else:
            # Export as individual files
            output_dir.mkdir(parents=True, exist_ok=True)
            exported_count = 0
            
            for prompt in prompts:
                try:
                    content = prompt["current_version"]["content"]
                    normalized_location = _normalize_prompt_location(prompt["location"])
                    file_path = output_dir / normalized_location

                    # Create parent directories if they don't exist
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    # Write content to file
                    with open(file_path, "w") as f:
                        f.write(content)

                    exported_count += 1
                    click.echo(f"  ✓ {prompt['name']} → {file_path}")

                except Exception as e:
                    click.echo(f"  ❌ Failed to export {prompt['name']}: {e}", err=True)

            click.echo(f"✅ Exported {exported_count} of {len(prompts)} prompts to {output_dir}")

    except AuthenticationError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("Authentication failed")
    except PromptaAPIError as e:
        click.echo(f"❌ {e}", err=True)
        raise click.ClickException("API request failed")


@click.command()
@click.argument("identifier", required=False)
@click.option("--project", "-p", help="Download entire project by name")
@click.option("--output", "-o", help="Output directory or file path")
@click.option("--api-key", help="API key to use for this request")
def get_command(
    identifier: Optional[str],
    project: Optional[str],
    output: Optional[str],
    api_key: Optional[str],
):
    """Download prompt files or entire projects.

    Usage examples:
      prompta get {project_id}          # Download entire project by ID
      prompta get {prompt_id}           # Download individual prompt by ID
      prompta get {prompt-name}         # Download individual prompt by name
      prompta get --project {project-name}  # Download entire project by name

    Note: If multiple projects have the same name, you must use the project ID.
    Use 'prompta project list' to list all projects with their IDs.
    """
    try:
        client = get_authenticated_client(api_key)

        # Validate that exactly one of identifier or project is provided
        if not identifier and not project:
            click.echo(
                "❌ Error: You must specify either IDENTIFIER as argument or use --project with project name.",
                err=True,
            )
            raise click.ClickException("Missing identifier")

        if identifier and project:
            click.echo(
                "❌ Error: Cannot specify both IDENTIFIER argument and --project option. Use one or the other.",
                err=True,
            )
            raise click.ClickException("Conflicting identifiers")

        # If --project option is used, download entire project by name
        if project:
            return _download_project_by_name(client, project, output)

        # Try to determine what type of identifier this is
        # UUIDs are 36 characters with 4 dashes
        if len(identifier) == 36 and identifier.count("-") == 4:
            # Looks like a UUID - try project first, then prompt
            try:
                return _download_project_by_id(client, identifier, output)
            except NotFoundError:
                # Not a project, try as prompt
                return _download_prompt_by_id(client, identifier, output)
        else:
            # Not a UUID - try prompt name first, then project name
            try:
                return _download_prompt_by_name(client, identifier, output)
            except NotFoundError:
                # Not a prompt, try as project name
                try:
                    return _download_project_by_name(client, identifier, output)
                except NotFoundError:
                    click.echo(
                        f"❌ No project or prompt found with identifier '{identifier}'.",
                        err=True,
                    )
                    raise click.ClickException("Resource not found")
                except click.ClickException as e:
                    # If it's a "multiple projects" error, re-raise it directly
                    if "Multiple projects with same name" in str(e):
                        raise e
                    else:
                        click.echo(
                            f"❌ No project or prompt found with identifier '{identifier}'.",
                            err=True,
                        )
                        raise click.ClickException("Resource not found")

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


def _download_prompt_by_id(client, prompt_id: str, output: Optional[str]):
    """Download individual prompt by ID."""
    prompt = client.get_prompt_by_id(prompt_id)
    return _download_single_prompt(prompt, output)


def _download_prompt_by_name(client, prompt_name: str, output: Optional[str]):
    """Download individual prompt by name."""
    prompt = client.get_prompt_by_name(prompt_name)
    return _download_single_prompt(prompt, output)


def _download_single_prompt(prompt: dict, output: Optional[str]):
    """Download a single prompt to file."""
    # Determine output path
    if output:
        output_path = Path(output)
    else:
        normalized_location = _normalize_prompt_location(prompt["location"])
        output_path = Path(normalized_location)

    # Create parent directories if they don't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write content to file
    content = prompt["current_version"]["content"]
    with open(output_path, "w") as f:
        f.write(content)

    click.echo(f"✅ Downloaded prompt '{prompt['name']}' to {output_path}")