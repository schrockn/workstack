import click

from workstack.commands.completion import completion_group
from workstack.commands.config import config_group
from workstack.commands.create import create
from workstack.commands.gc import gc_cmd
from workstack.commands.init import init_cmd
from workstack.commands.list import list_cmd, ls_cmd
from workstack.commands.remove import remove_cmd, rm_cmd
from workstack.commands.rename import rename_cmd
from workstack.commands.switch import switch_cmd

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])  # terse help flags


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(package_name="workstack")
def cli() -> None:
    """Manage git worktrees in a global worktrees directory."""


# Register all commands
cli.add_command(completion_group)
cli.add_command(create)
cli.add_command(switch_cmd)
cli.add_command(list_cmd)
cli.add_command(ls_cmd)
cli.add_command(init_cmd)
cli.add_command(remove_cmd)
cli.add_command(rm_cmd)
cli.add_command(rename_cmd)
cli.add_command(config_group)
cli.add_command(gc_cmd)
