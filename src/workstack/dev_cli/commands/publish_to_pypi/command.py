"""Publish to PyPI command."""

import subprocess
from pathlib import Path

import click


@click.command(name="publish-to-pypi")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
def command(dry_run: bool) -> None:
    """Publish workstack package to PyPI.

    This command automates the full publishing workflow:
    1. Pull latest changes from remote
    2. Bump version in pyproject.toml
    3. Update lockfile with uv sync
    4. Build and publish to PyPI
    5. Commit and push changes
    """
    script_path = Path(__file__).parent / "script.py"

    cmd = ["uv", "run", str(script_path)]
    if dry_run:
        cmd.append("--dry-run")

    subprocess.run(cmd, check=True)
