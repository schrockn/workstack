"""Utility functions for hook commands."""

from pathlib import Path

import click


def parse_hook_path(hook_path: str, hooks_dir: Path) -> Path:
    """Parse and validate hook path, returning path to hooks.toml.

    Args:
        hook_path: Hook path in format "kit-name/hook-name"
        hooks_dir: Path to hooks directory

    Returns:
        Path to the kit's hooks.toml file

    Raises:
        SystemExit: If path format is invalid or kit not found
    """
    parts = hook_path.split("/")
    if len(parts) != 2:
        click.echo(
            "Error: Invalid hook path format. Use: kit-name/hook-name",
            err=True,
        )
        raise SystemExit(1)

    kit_name, _hook_name = parts
    hooks_toml = hooks_dir / kit_name / "hooks.toml"

    if not hooks_toml.exists():
        click.echo(f"Error: Kit '{kit_name}' not found or has no hooks", err=True)
        raise SystemExit(1)

    return hooks_toml
