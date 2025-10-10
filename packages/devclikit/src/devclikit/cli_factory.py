"""High-level API for creating development CLIs."""

from pathlib import Path
from typing import Any

import click

from devclikit.completion import add_completion_commands
from devclikit.loader import load_commands


def create_cli(
    name: str,
    description: str,
    commands_dir: str | Path = "./commands",
    *,
    version: str | None = None,
    add_completion: bool = True,
    context_settings: dict[str, Any] | None = None,
) -> click.Group:
    """Create a development CLI with automatic command discovery.

    Args:
        name: CLI name (used for executable and completion)
        description: Help text for the CLI
        commands_dir: Directory containing command subdirectories
        version: Optional version string (enables --version flag)
        add_completion: Whether to add completion commands (default: True)
        context_settings: Optional Click context settings

    Returns:
        Click group with all discovered commands registered

    Example:
        >>> cli = create_cli(
        ...     name="myproject-dev",
        ...     description="Development tools for myproject",
        ...     version="1.0.0"
        ... )
    """

    @click.group(name=name, context_settings=context_settings)
    def cli() -> None:
        pass

    cli.help = description

    if version:

        @cli.command()
        def version_cmd() -> None:
            """Show version."""
            click.echo(version)

        version_cmd.name = "version"

    # Auto-discover and register commands
    commands = load_commands(Path(commands_dir))
    for cmd_name, cmd in commands.items():
        cli.add_command(cmd, name=cmd_name)

    # Add completion commands
    if add_completion:
        add_completion_commands(cli, name)

    return cli
