"""Codex code review command."""

from pathlib import Path

import click

from devclikit import run_pep723_script


@click.command(name="codex-review")
@click.argument("base-branch", required=False)
@click.option("--output", "-o", help="Output file path (default: auto-generated)")
def command(base_branch: str | None, output: str | None) -> None:
    """Perform code review using Codex against repository standards.

    Automatically detects base branch using Graphite parent or falls back to main.
    Generates timestamped review file unless --output is specified.

    Examples:

        # Auto-detect base branch
        workstack-dev codex-review

        # Specify base branch
        workstack-dev codex-review main

        # Custom output file
        workstack-dev codex-review --output my-review.md
    """
    script_path = Path(__file__).parent / "script.py"

    args = []
    if base_branch:
        args.extend(["--base", base_branch])
    if output:
        args.extend(["--output", output])

    run_pep723_script(script_path, args)
