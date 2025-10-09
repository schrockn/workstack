"""Clean cache directories command."""

from pathlib import Path

import click

from workstack.dev_cli.utils import run_pep723_script


@click.command(name="clean-cache")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def command(dry_run: bool, verbose: bool) -> None:
    """Clean all cache directories."""
    script_path = Path(__file__).parent / "script.py"

    args = []
    if dry_run:
        args.append("--dry-run")
    if verbose:
        args.append("--verbose")

    run_pep723_script(script_path, args)
