"""Link dot-agent-kit resources command."""

from pathlib import Path

import click

from devclikit import run_pep723_script


@click.command(name="link-dot-agent-resources")
@click.option("--create", is_flag=True, help="Create symlinks")
@click.option("--remove", is_flag=True, help="Remove symlinks and restore regular files")
@click.option("--status", is_flag=True, help="Show current status (default)")
@click.option("--verify", is_flag=True, help="Verify symlinks are valid")
@click.option("--dry-run", is_flag=True, help="Preview changes without executing")
@click.option("--verbose", is_flag=True, help="Show detailed output")
@click.option("--force", is_flag=True, help="Skip confirmation prompts")
def command(
    create: bool,
    remove: bool,
    status: bool,
    verify: bool,
    dry_run: bool,
    verbose: bool,
    force: bool,
) -> None:
    """Manage symlinks between .agent/tools/ and dot-agent-kit package resources."""
    script_path = Path(__file__).parent / "script.py"

    args = []
    if create:
        args.append("--create")
    if remove:
        args.append("--remove")
    if status:
        args.append("--status")
    if verify:
        args.append("--verify")
    if dry_run:
        args.append("--dry-run")
    if verbose:
        args.append("--verbose")
    if force:
        args.append("--force")

    run_pep723_script(script_path, args)
