"""Create AGENTS.md symlinks command."""

from pathlib import Path

import click

from workstack.dev_cli.utils import run_pep723_script


@click.command(name="create-agents-symlinks")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def command(dry_run: bool, verbose: bool) -> None:
    """Create AGENTS.md symlinks for all CLAUDE.md files in the repository."""
    script_path = Path(__file__).parent / "script.py"

    args = []
    if dry_run:
        args.append("--dry-run")
    if verbose:
        args.append("--verbose")

    run_pep723_script(script_path, args)
