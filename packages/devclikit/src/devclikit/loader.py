"""Command discovery and dynamic loading."""

import importlib.util
import inspect
import types
from pathlib import Path

import click

from devclikit.exceptions import CommandLoadError


def load_commands(
    commands_dir: Path,
    *,
    verbose: bool = False,
    strict: bool = False,
) -> dict[str, click.Command]:
    """Discover and load all commands from a directory.

    Scans for subdirectories containing command.py files, dynamically
    imports them, and extracts Click command objects.

    Args:
        commands_dir: Directory containing command subdirectories
        verbose: Print loading progress to stderr
        strict: Raise exceptions on load failures (default: warn and skip)

    Returns:
        Mapping of command name to Click command object

    Raises:
        CommandLoadError: If strict=True and loading fails
    """
    commands: dict[str, click.Command] = {}

    if not commands_dir.exists():
        if strict:
            raise CommandLoadError(f"Commands directory not found: {commands_dir}")
        return commands

    if not commands_dir.is_dir():
        if strict:
            raise CommandLoadError(f"Not a directory: {commands_dir}")
        return commands

    # Iterate through subdirectories
    for cmd_dir in sorted(commands_dir.iterdir()):
        if not cmd_dir.is_dir():
            continue
        if cmd_dir.name.startswith("_") or cmd_dir.name.startswith("."):
            continue

        command_file = cmd_dir / "command.py"
        if not command_file.exists():
            if verbose:
                click.echo(f"Skipping {cmd_dir.name}: no command.py", err=True)
            continue

        # Load command module
        # Error boundary: catch module loading errors
        try:
            module = _load_module(command_file, cmd_dir.name)
            cmd = _extract_command(module)

            if cmd:
                # Prefer directory name over command.name
                cmd_name = cmd_dir.name.replace("_", "-")
                commands[cmd_name] = cmd
                if verbose:
                    click.echo(f"Loaded command: {cmd_name}", err=True)
            else:
                if strict:
                    raise CommandLoadError(f"No Click command found in {command_file}")
                if verbose:
                    click.echo(f"Warning: No command in {cmd_dir.name}", err=True)

        except (ImportError, AttributeError, CommandLoadError) as e:
            if strict:
                raise CommandLoadError(f"Failed to load {cmd_dir.name}: {e}") from e
            click.echo(f"Warning: Failed to load '{cmd_dir.name}': {e}", err=True)

    return commands


def _load_module(command_file: Path, module_name: str) -> types.ModuleType:
    """Dynamically import a command module."""
    spec = importlib.util.spec_from_file_location(
        f"_dev_cli_commands.{module_name}",
        command_file,
    )

    if not spec or not spec.loader:
        raise CommandLoadError(f"Failed to create module spec for {command_file}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extract_command(module: types.ModuleType) -> click.Command | None:
    """Extract Click command from module.

    Looks for:
    1. Attribute named 'command'
    2. First Click.Command or Click.Group instance
    """
    # Check for explicit 'command' attribute
    if hasattr(module, "command") and isinstance(module.command, click.Command):
        return module.command

    # Find first Click command
    for _name, obj in inspect.getmembers(module):
        if isinstance(obj, (click.Command, click.Group)):
            return obj

    return None
