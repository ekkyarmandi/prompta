"""Prompta CLI core package.

This directory contains the entire implementation of the **Prompta** command-line
interface.
"""

# Keep the semantic version in sync with pyproject.toml
__version__: str = "0.2.10"

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
