"""Project-related commands (createproject)."""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import click

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _get_template_path() -> Path:
    """Return the directory that contains the FastAPI project template.

    The template is expected at `prompta/templates/api` **inside the installed
    package**.  When running from the repository during development, fall back to
    the `../prompta-app` directory.
    """

    # 1. In a regular installed package we bundle templates under
    #    prompta/templates/api/  (this will be included via MANIFEST.in)
    pkg_dir = Path(__file__).resolve().parent.parent  # prompta/
    candidate = pkg_dir / "templates" / "api"
    if candidate.is_dir():
        return candidate

    # 2. Development fallback – take reference implementation directory.
    repo_root = pkg_dir.parent.parent  # one level up from prompta-cli/
    dev_candidate = repo_root / "prompta-app"
    if dev_candidate.is_dir():
        return dev_candidate

    raise FileNotFoundError(
        "Could not locate project template – looked in "
        f"{candidate} and {dev_candidate}"
    )


# ---------------------------------------------------------------------------
# Click command implementation
# ---------------------------------------------------------------------------


@click.command("createproject")
@click.argument("name")
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite destination if it already exists (dangerous).",
)
def create_project_command(name: str, force: bool) -> None:  # pragma: no cover
    """Scaffold a new Prompta backend project in the *NAME* directory."""

    project_dir = Path(name).expanduser().resolve()

    if project_dir.exists() and project_dir.is_dir() and any(project_dir.iterdir()):
        if not force:
            raise click.ClickException(
                f"Directory '{project_dir}' already exists and is not empty."
            )
        # Remove existing directory if force specified
        shutil.rmtree(project_dir)

    template_src = _get_template_path()
    click.echo(f"📦 Creating new Prompta project at {project_dir} …")

    try:
        shutil.copytree(template_src, project_dir)
    except Exception as exc:  # pragma: no cover
        raise click.ClickException(f"Failed to copy template: {exc}") from exc

    # No longer generating .env or .prompta_project files
    # .env.example is included in template for users to copy

    # Initialise git repo (optional)
    try:
        subprocess.run(
            ["git", "init"], cwd=project_dir, check=False, stdout=subprocess.DEVNULL
        )
    except Exception:
        pass  # Git not available – silently ignore

    click.echo("✅ Project created successfully! Next steps:")
    click.echo(f"   cd {project_dir.name}")
    click.echo("   cp .env.example .env   # copy environment config")
    click.echo("   prompta migrate        # create database")
    click.echo("   prompta runserver      # start dev server on http://127.0.0.1:8000")
