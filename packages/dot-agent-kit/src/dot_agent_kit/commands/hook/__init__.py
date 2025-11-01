"""Hook command group for managing hooks."""

import click

from dot_agent_kit.commands.hook import disable, enable, list


@click.group(name="hook")
def hook() -> None:
    """Manage hooks - list, enable, and disable."""


# Add subcommands
hook.add_command(list.list_hooks)
hook.add_command(enable.enable_hook)
hook.add_command(disable.disable_hook)
