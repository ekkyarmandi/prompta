"""Allows `python -m prompta ...` execution.

When a package is executed with `-m`, Python looks for `<package>.__main__`.  We simply
delegate to the Click `cli` defined in *prompta.main*.
"""

from __future__ import annotations

from .main import cli


def main() -> None:  # pragma: no cover
    cli()


if __name__ == "__main__":  # pragma: no cover
    main()
