"""Static CLI definition for mdstack-dev.

This module uses static imports instead of dynamic command loading to enable
shell completion. Click's completion mechanism requires all commands to be
available at import time for inspection.
"""

import click

from mdstack_dev.commands.sync_kit.command import sync_kit_command


@click.group(name="mdstack-dev")
def cli() -> None:
    """Development tools for managing dot-agent kits."""
    pass


# Register all commands
cli.add_command(sync_kit_command)
