"""Kit command group for managing kits."""

import click

from dot_agent_kit.commands.kit import init, install, list, remove, search, sync, update


@click.group(name="kit")
def kit() -> None:
    """Manage kits - install, update, remove, and search."""


# Add subcommands
kit.add_command(install.install)
kit.add_command(remove.remove)
kit.add_command(update.update)
kit.add_command(sync.sync)
kit.add_command(init.init)
kit.add_command(search.search)
kit.add_command(list.list_kits)
