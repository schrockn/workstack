"""CLI entry point for dot-agent."""

import click

from dot_agent_kit.commands.check import check
from dot_agent_kit.commands.init import init
from dot_agent_kit.commands.list import list_cmd
from dot_agent_kit.commands.search import search
from dot_agent_kit.commands.sync import sync


@click.group()
@click.version_option(version="0.1.0", prog_name="dot-agent")
def cli():
    """dot-agent: Manage Claude Code agent kits."""
    pass


cli.add_command(check)
cli.add_command(init)
cli.add_command(list_cmd, name="list")
cli.add_command(list_cmd, name="ls")
cli.add_command(search)
cli.add_command(sync)


if __name__ == "__main__":
    cli()
