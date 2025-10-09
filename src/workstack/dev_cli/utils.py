"""Shared utilities for dev CLI commands."""

import subprocess
from pathlib import Path

import click


def run_pep723_script(script_path: Path, args: list[str] | None = None) -> None:
    """Run a PEP 723 inline script using uv run.

    Args:
        script_path: Path to the script.py file
        args: Optional list of arguments to pass to the script

    Raises:
        SystemExit: If the script execution fails
    """
    cmd = ["uv", "run", str(script_path)]
    if args:
        cmd.extend(args)

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Command failed with exit code {e.returncode}", err=True)
        raise SystemExit(1) from e
