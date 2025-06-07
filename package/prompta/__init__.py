"""Prompta CLI Package

A comprehensive command-line interface and Python library for Prompta.

This package provides:
1. CLI commands for prompt and project management
2. Interface objects for external use without API complexity
3. Auto-tracking functionality with context detection
4. File-based prompt management with auto-sync
5. Version-specific prompt loading and comparison

Interface Objects (for external use):
- Project: Create, read, update, delete projects
- Prompt: Create, read, update, delete prompts
- PromptVersion: Work with prompt versions

Tracking Objects (auto-detection + explicit naming):
- TrackedPrompt: Enhanced prompts with context detection, file support, and version loading
- tracked_prompt(): Convenience function for tracking prompts

Version Loading Examples:
```python
# Load specific version
prompt = TrackedPrompt(name="assistant", version="v1")
prompt = TrackedPrompt(name="assistant", version=2)
prompt = TrackedPrompt(name="assistant", version="latest")

# Load from file
prompt = TrackedPrompt(name="assistant", location="prompt.txt")

# Regular tracking (creates versions automatically)
prompt = TrackedPrompt(name="assistant", content="You are helpful")
```

Classes and functions imported from this package can be used independently
of the CLI commands, making them suitable for integration into other Python projects.
"""

import os
from pathlib import Path

# Keep the semantic version in sync with pyproject.toml
__version__: str = "0.4.1"


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

# Export interface objects for external use
from .models import Project, Prompt, PromptVersion  # noqa: E402, isort: skip

# Export tracking functionality
from .tracking import TrackedPrompt, tracked_prompt  # noqa: E402, isort: skip

# Configuration and client (for advanced users)
from .config import Config, ConfigManager
from .client import PromptaClient

__all__ = [
    "cli",
    "Project",
    "Prompt",
    "PromptVersion",
    "TrackedPrompt",
    "tracked_prompt",
    "Config",
    "ConfigManager",
    "PromptaClient",
    "__version__",
]
