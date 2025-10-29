import click

from dot_agent_kit import __version__
from dot_agent_kit.commands import check, init


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Manage Claude Code kits."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cli.add_command(init.init)
cli.add_command(check.check)


if __name__ == "__main__":
    cli()
