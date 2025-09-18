"""work CLI entrypoint.

This package provides a Click-based CLI for managing git worktrees under a
repository-local `.work/` directory. See `work --help` for details.
"""

from .cli import cli


def main() -> None:
    """CLI entry point used by the `work` console script."""
    cli()
