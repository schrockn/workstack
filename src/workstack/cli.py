import click

from workstack.commands.completion import completion_group
from workstack.commands.config import config_group
from workstack.commands.create import create
from workstack.commands.gc import gc_cmd
from workstack.commands.init import init_cmd
from workstack.commands.list import list_cmd, ls_cmd
from workstack.commands.remove import remove_cmd, rm_cmd
from workstack.commands.rename import rename_cmd
from workstack.commands.switch import hidden_switch_cmd, switch_cmd
from workstack.commands.sync import sync_cmd
from workstack.commands.tree import tree_cmd
from workstack.context import create_context

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])  # terse help flags


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(package_name="workstack")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Manage git worktrees in a global worktrees directory."""
    # Only create context if not already provided (e.g., by tests)
    if ctx.obj is None:
        ctx.obj = create_context(dry_run=False)


# Register all commands
cli.add_command(completion_group)
cli.add_command(create)
cli.add_command(switch_cmd)
cli.add_command(hidden_switch_cmd)
cli.add_command(list_cmd)
cli.add_command(ls_cmd)
cli.add_command(init_cmd)
cli.add_command(remove_cmd)
cli.add_command(rm_cmd)
cli.add_command(rename_cmd)
cli.add_command(config_group)
cli.add_command(gc_cmd)
cli.add_command(sync_cmd)
cli.add_command(tree_cmd)
