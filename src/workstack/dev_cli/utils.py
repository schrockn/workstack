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

    # Use check=False and manually check return code (LBYL pattern)
    result = subprocess.run(cmd, check=False)

    # Check return code and fail if non-zero
    if result.returncode != 0:
        click.echo(f"Command failed with exit code {result.returncode}", err=True)
        raise SystemExit(1)


def run_pep723_script_with_output(script_path: Path, args: list[str] | None = None) -> None:
    """Run a PEP 723 inline script and capture/echo its output.

    Used for commands that generate output to stdout (like completion scripts).

    Args:
        script_path: Path to the script.py file
        args: Optional list of arguments to pass to the script

    Raises:
        SystemExit: If the script execution fails
    """
    cmd = ["uv", "run", str(script_path)]
    if args:
        cmd.extend(args)

    # Use check=False and manually check return code (LBYL pattern)
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    # Echo stdout to make it available in Click test results
    if result.stdout:
        click.echo(result.stdout, nl=False)
    # Echo stderr for warnings/errors
    if result.stderr:
        click.echo(result.stderr, err=True, nl=False)

    # Check return code and fail if non-zero
    if result.returncode != 0:
        click.echo(f"Command failed with exit code {result.returncode}", err=True)
        raise SystemExit(1)
