"""Reserve PyPI package name command."""

from pathlib import Path

import click

from devclikit import run_pep723_script


@click.command(name="reserve-pypi-name")
@click.option("--name", required=True, help="Package name to reserve")
@click.option(
    "--description",
    default="Reserved package name",
    show_default=True,
    help="Package description",
)
@click.option("--dry-run", is_flag=True, help="Show operations without publishing")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def command(name: str, description: str, dry_run: bool, force: bool) -> None:
    """Reserve a package name on PyPI by publishing a placeholder package."""
    script_path = Path(__file__).parent / "script.py"

    args = [
        "--name",
        name,
        "--description",
        description,
    ]

    if dry_run:
        args.append("--dry-run")

    if force:
        args.append("--force")

    run_pep723_script(script_path, args)
