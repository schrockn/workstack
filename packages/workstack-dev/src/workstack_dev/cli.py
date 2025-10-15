"""Static CLI definition for workstack-dev.

This module uses static imports instead of dynamic command loading to enable
shell completion. Click's completion mechanism requires all commands to be
available at import time for inspection.
"""

import click

from workstack_dev.commands.clean_cache.command import command as clean_cache_cmd
from workstack_dev.commands.codex_review.command import command as codex_review_cmd
from workstack_dev.commands.completion.command import command as completion_cmd
from workstack_dev.commands.create_agents_symlinks.command import (
    command as create_agents_cmd,
)
from workstack_dev.commands.publish_to_pypi.command import command as publish_cmd
from workstack_dev.commands.reserve_pypi_name.command import (
    command as reserve_pypi_name_cmd,
)


@click.group(name="workstack-dev")
def cli() -> None:
    """Development tools for workstack."""
    pass


# Register all commands
cli.add_command(clean_cache_cmd, name="clean-cache")
cli.add_command(codex_review_cmd, name="codex-review")
cli.add_command(completion_cmd, name="completion")
cli.add_command(create_agents_cmd, name="create-agents-symlinks")
cli.add_command(publish_cmd, name="publish-to-pypi")
cli.add_command(reserve_pypi_name_cmd, name="reserve-pypi-name")
