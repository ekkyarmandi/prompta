"""Project commands: runserver, migrate, createsuperuser."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

import click

PROJECT_MARKER = "alembic.ini"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_project_root(start: Path | None = None) -> Path:
    """Ascend directories until we find `alembic.ini` marker."""

    current = start or Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / PROJECT_MARKER).is_file():
            return parent
    raise click.ClickException(
        "This command must be run inside a Prompta project directory."
    )


def _ensure_on_sys_path(path: Path) -> None:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


# ---------------------------------------------------------------------------
# runserver
# ---------------------------------------------------------------------------


@click.command("runserver")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.option("--reload/--no-reload", default=True, show_default=True)
def runserver_command(host: str, port: int, reload: bool) -> None:  # pragma: no cover
    """Start the FastAPI development server (uvicorn)."""

    project_root = _find_project_root()

    # Check if app.main module exists
    app_main_file = project_root / "app" / "main.py"
    if not app_main_file.exists():
        raise click.ClickException("Could not find app/main.py in project root")

    try:
        click.echo(f"🚀 Starting server at http://{host}:{port}")

        # Build uvicorn command
        cmd = ["uvicorn", "app.main:app", "--host", host, "--port", str(port)]

        if reload:
            cmd.append("--reload")

        # Run uvicorn in the project directory
        result = subprocess.run(cmd, cwd=project_root, check=False)

        # If uvicorn exits, show the exit code
        if result.returncode != 0:
            raise click.ClickException(f"Server exited with code {result.returncode}")

    except FileNotFoundError:
        raise click.ClickException(
            "Uvicorn is not installed or not found in PATH. "
            "Install it in your project environment: pip install uvicorn"
        )


# ---------------------------------------------------------------------------
# migrate
# ---------------------------------------------------------------------------


@click.command("migrate")
@click.option(
    "--autogenerate",
    is_flag=True,
    help="Autogenerate migration (alembic revision --autogenerate).",
)
@click.option("-m", "--message", default="auto", help="Migration message.")
def migrate_command(autogenerate: bool, message: str) -> None:  # pragma: no cover
    """Run database migrations (Alembic)."""

    project_root = _find_project_root()

    alembic_ini = project_root / "alembic.ini"
    if not alembic_ini.exists():
        raise click.ClickException("Could not find alembic.ini in project root")

    try:
        if autogenerate:
            click.echo("🔄 Generating new migration …")
            cmd = ["alembic", "revision", "--autogenerate", "-m", message]
        else:
            click.echo("📜 Applying migrations …")
            cmd = ["alembic", "upgrade", "head"]

        # Run alembic in the project directory
        result = subprocess.run(
            cmd, cwd=project_root, capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            error_msg = (
                result.stderr.strip() if result.stderr else "Unknown error occurred"
            )
            raise click.ClickException(f"Alembic command failed: {error_msg}")

        # Print alembic output
        if result.stdout:
            click.echo(result.stdout.strip())

    except FileNotFoundError:
        raise click.ClickException(
            "Alembic is not installed or not found in PATH. "
            "Install it in your project environment: pip install alembic"
        )


# ---------------------------------------------------------------------------
# createsuperuser
# ---------------------------------------------------------------------------


@click.command("createsuperuser")
def createsuperuser_command() -> None:  # pragma: no cover
    """Interactive creation of an admin user."""

    project_root = _find_project_root()
    _ensure_on_sys_path(project_root)

    import getpass

    # Lazy imports (inside project environment)
    from sqlalchemy.exc import IntegrityError

    try:
        from app.database import SessionLocal, create_tables  # type: ignore

        # Import models to satisfy SQLAlchemy relationship resolution before using
        # the User class (it references Prompt via relationship()).
        import prompts.models  # type: ignore  # noqa: F401
        from auth.models import User  # type: ignore
        from auth.security import get_password_hash  # type: ignore
    except ModuleNotFoundError as exc:
        raise click.ClickException(
            "Failed to import project modules – are you in a Prompta project directory?"
        ) from exc

    # Ensure tables exist
    create_tables()

    username = click.prompt("Username")
    email = click.prompt("Email")

    while True:
        pwd1 = getpass.getpass("Password: ")
        pwd2 = getpass.getpass("Password (again): ")
        if pwd1 != pwd2:
            click.echo("Passwords don't match. Try again.")
            continue
        if len(pwd1) < 6:
            click.echo("Password must be at least 6 characters long.")
            continue
        break

    db = SessionLocal()
    import hashlib

    try:
        # get_password_hash uses Passlib (bcrypt). Fallback to sha256 if bcrypt backend
        # is unavailable in the current environment so the command still works for
        # quick local testing.
        try:
            hashed = get_password_hash(pwd1)
        except Exception:  # pragma: no cover
            click.echo("⚠️  bcrypt backend not available – using SHA256 hash.")
            hashed = hashlib.sha256(pwd1.encode()).hexdigest()

        user = User(
            username=username, email=email, password_hash=hashed, is_active=True
        )
        db.add(user)
        db.commit()
        click.echo("✅ Superuser created successfully")
    except IntegrityError:
        db.rollback()
        raise click.ClickException("User with that username or email already exists")
    finally:
        db.close()


# Convenience accessor for adding all commands from other modules
commands = [runserver_command, migrate_command, createsuperuser_command]
