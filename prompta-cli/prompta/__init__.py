"""Prompta CLI core package.

This directory contains the entire implementation of the Prompta command-line
interface.
"""

import os
from pathlib import Path

# Keep the semantic version in sync with pyproject.toml
__version__: str = "0.3.1"


def _ensure_prompta_config_on_import():
    """Create ~/.prompta config file when package is first imported after installation."""
    prompta_path = Path.home() / ".prompta"

    # Only create if it doesn't exist (don't overwrite)
    if not prompta_path.exists():
        default_config = 'PROMPTA_API_URL="http://localhost:8000"\nPROMPTA_API_KEY=""\n'

        try:
            # Create parent directory if it doesn't exist
            prompta_path.parent.mkdir(parents=True, exist_ok=True)

            with open(prompta_path, "w") as f:
                f.write(default_config)
        except Exception:
            # Silently ignore errors - user can create manually if needed
            pass


# Create config on package import (happens on first use after installation)
_ensure_prompta_config_on_import()

# Metadata
__author__: str = "Ekky Armandi"
__email__: str = "me@ekky.dev"
__license__: str = "MIT"

# Re-export the Click entry-point so that `python -m prompta` works as expected.
from .main import cli  # noqa: E402, isort: skip

__all__ = [
    "cli",
    "__version__",
]
