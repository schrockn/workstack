"""Sync command for updating installed kits."""

import click


@click.command()
@click.option("--dry-run", is_flag=True, help="Show what would be updated")
def sync(dry_run: bool) -> None:
    """Sync all installed kits to their latest versions."""
    raise NotImplementedError("Coming in commit 6")
