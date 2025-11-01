import click

from dot_agent_kit import __version__
from dot_agent_kit.commands import status
from dot_agent_kit.commands.artifact import artifact
from dot_agent_kit.commands.hook import hook
from dot_agent_kit.commands.kit import kit

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Manage Claude Code kits."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cli.add_command(kit)
cli.add_command(hook)
cli.add_command(artifact)
cli.add_command(status.status)


if __name__ == "__main__":
    cli()
