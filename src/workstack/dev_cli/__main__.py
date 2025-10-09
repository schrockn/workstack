"""Development CLI entry point."""

import click

from workstack.dev_cli.loader import load_commands


@click.group()
def cli() -> None:
    """Development tools for workstack."""
    pass


# Auto-register all discovered commands
for _cmd_name, cmd in load_commands().items():
    cli.add_command(cmd)


if __name__ == "__main__":
    cli()
