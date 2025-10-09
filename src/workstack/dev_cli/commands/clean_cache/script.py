#!/usr/bin/env python3
# /// script
# dependencies = [
#   "click>=8.1.7",
#   "rich>=13.0.0",
# ]
# requires-python = ">=3.13"
# ///
"""Clean cache implementation."""

# pyright: reportMissingImports=false

import shutil
from pathlib import Path

import click
from rich.console import Console

console = Console()


@click.command()
@click.option("--dry-run", is_flag=True)
@click.option("--verbose", is_flag=True)
def main(dry_run: bool, verbose: bool) -> None:
    """Execute cache cleaning."""
    console.print("[bold]Cleaning cache directories...[/bold]")

    cache_dirs = [
        Path.home() / ".cache" / "workstack",
        Path(".pytest_cache"),
        Path(".ruff_cache"),
        Path("__pycache__"),
    ]

    deleted_count = 0
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            if dry_run:
                console.print(f"[yellow]Would delete:[/yellow] {cache_dir}")
                deleted_count += 1
            else:
                if verbose:
                    console.print(f"[blue]Deleting:[/blue] {cache_dir}")
                shutil.rmtree(cache_dir)
                deleted_count += 1
        elif verbose:
            console.print(f"[dim]Not found:[/dim] {cache_dir}")

    if deleted_count > 0:
        action = "Would delete" if dry_run else "Deleted"
        plural = "y" if deleted_count == 1 else "ies"
        console.print(f"[green]{action} {deleted_count} cache director{plural}[/green]")
    else:
        console.print("[dim]No cache directories found[/dim]")


if __name__ == "__main__":
    main()
