"""Publish to PyPI command."""

from pathlib import Path

import click

from workstack.dev_cli.utils import run_pep723_script


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

    args = []
    if dry_run:
        args.append("--dry-run")

    run_pep723_script(script_path, args)
