"""Clean cache directories command."""

import shutil
from pathlib import Path

import click

CACHE_DIRS = [
    Path.home() / ".cache" / "workstack",
    Path(".pytest_cache"),
    Path(".ruff_cache"),
    Path("__pycache__"),
]


def describe_action(prefix: str, cache_dir: Path) -> str:
    """Return a user-facing description for the cache directory path."""
    return f"{prefix}: {cache_dir}"


def clean_cache_directory(cache_dir: Path, dry_run: bool, verbose: bool) -> bool:
    """Remove a single cache directory if it exists."""
    if not cache_dir.exists():
        if verbose:
            click.echo(describe_action("Not found", cache_dir))
        return False

    if dry_run:
        click.echo(describe_action("Would delete", cache_dir))
        return True

    if verbose:
        click.echo(describe_action("Deleting", cache_dir))

    if cache_dir.is_symlink() or cache_dir.is_file():
        cache_dir.unlink()
    else:
        shutil.rmtree(cache_dir)
    return True


@click.command(name="clean-cache")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def command(dry_run: bool, verbose: bool) -> None:
    """Clean all cache directories."""
    click.echo("Cleaning cache directories...")

    deleted_count = 0
    for cache_dir in CACHE_DIRS:
        if clean_cache_directory(cache_dir, dry_run, verbose):
            deleted_count += 1

    if deleted_count > 0:
        action = "Would delete" if dry_run else "Deleted"
        plural = "y" if deleted_count == 1 else "ies"
        click.echo(f"{action} {deleted_count} cache director{plural}")
    else:
        click.echo("No cache directories found")
