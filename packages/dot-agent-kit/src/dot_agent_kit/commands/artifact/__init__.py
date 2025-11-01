"""Artifact command group for managing artifacts."""

import click

from dot_agent_kit.commands.artifact import check, check_sync, list


@click.group(name="artifact")
def artifact() -> None:
    """Manage artifacts - list, check, and validate."""


# Add subcommands
artifact.add_command(list.list_artifacts)
artifact.add_command(check.check)
artifact.add_command(check_sync.check_sync)
