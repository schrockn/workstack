"""Static CLI definition for workstack-dev.

This module uses static imports instead of dynamic command loading to enable
shell completion. Click's completion mechanism requires all commands to be
available at import time for inspection.
"""

import click

from devclikit.exceptions import DevCliFrameworkError
from workstack_dev.commands.clean_cache.command import command as clean_cache_cmd
from workstack_dev.commands.codex_review.command import command as codex_review_cmd
from workstack_dev.commands.completion.command import command as completion_cmd
from workstack_dev.commands.create_agents_symlinks.command import (
    command as create_agents_cmd,
)
from workstack_dev.commands.link_dot_agent_resources.command import (
    command as link_resources_cmd,
)
from workstack_dev.commands.publish_to_pypi.command import command as publish_cmd
from workstack_dev.commands.reserve_pypi_name.command import (
    command as reserve_pypi_name_cmd,
)


class WorkstackDevGroup(click.Group):
    """Customize CLI error handling for framework exceptions."""

    def invoke(self, ctx: click.Context) -> object:
        try:
            return super().invoke(ctx)
        except DevCliFrameworkError as error:
            message = str(error) or "Command failed"
            raise click.ClickException(message) from None


@click.group(name="workstack-dev", cls=WorkstackDevGroup)
def cli() -> None:
    """Development tools for workstack."""
    pass


# Register all commands
cli.add_command(clean_cache_cmd, name="clean-cache")
cli.add_command(codex_review_cmd, name="codex-review")
cli.add_command(completion_cmd, name="completion")
cli.add_command(create_agents_cmd, name="create-agents-symlinks")
cli.add_command(link_resources_cmd, name="link-dot-agent-resources")
cli.add_command(publish_cmd, name="publish-to-pypi")
cli.add_command(reserve_pypi_name_cmd, name="reserve-pypi-name")
