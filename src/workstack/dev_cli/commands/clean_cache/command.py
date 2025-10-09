"""Clean cache directories command."""

import subprocess
from pathlib import Path

import click


@click.command(name="clean-cache")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def command(dry_run: bool, verbose: bool) -> None:
    """Clean all cache directories."""
    script_path = Path(__file__).parent / "script.py"

    cmd = ["uv", "run", str(script_path)]
    if dry_run:
        cmd.append("--dry-run")
    if verbose:
        cmd.append("--verbose")

    subprocess.run(cmd, check=True)
