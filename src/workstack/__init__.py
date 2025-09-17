"""workstack CLI entry point.

This package provides a Click-based CLI for managing git worktrees under a
repository-local `.work/` directory. See `workstack --help` for details.
"""

from .cli import cli


def main() -> None:
    """CLI entry point used by the `workstack` console script."""
    cli()
