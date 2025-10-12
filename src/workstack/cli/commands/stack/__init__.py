"""Stack command group and subcommands."""

import click


@click.group("stack")
def stack_group() -> None:
    """Commands for managing stacks of worktrees."""
    pass
