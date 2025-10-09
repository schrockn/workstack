"""Discover and load all commands from the commands directory."""

import importlib.util
import inspect
from pathlib import Path

import click


def load_commands() -> dict[str, click.Command]:
    """Discover and load all commands from the commands directory.

    Returns:
        Mapping of command name to click command function
    """
    discovered_commands: dict[str, click.Command] = {}
    commands_dir = Path(__file__).parent / "commands"

    if not commands_dir.exists():
        return discovered_commands

    # Iterate through all directories in commands/
    for cmd_dir in commands_dir.iterdir():
        if not cmd_dir.is_dir() or cmd_dir.name.startswith("_"):
            continue

        command_file = cmd_dir / "command.py"
        if not command_file.exists():
            continue

        # Import command.py dynamically
        spec = importlib.util.spec_from_file_location(
            f"workstack.dev_cli.commands.{cmd_dir.name}.command",
            command_file,
        )

        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)

            # Error boundary: catch broken command modules
            try:
                spec.loader.exec_module(module)
            except (ImportError, SyntaxError) as e:
                click.echo(f"Warning: Failed to load command '{cmd_dir.name}': {e}", err=True)
                continue

            # Look for click.Command objects
            for _name, obj in inspect.getmembers(module):
                if isinstance(obj, click.Command):
                    cmd_name = obj.name or cmd_dir.name.replace("_", "-")
                    discovered_commands[cmd_name] = obj
                    break  # Only take first command from each module

    return discovered_commands
