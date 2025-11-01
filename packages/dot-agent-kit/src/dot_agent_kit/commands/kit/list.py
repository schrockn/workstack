"""List command for showing installed kits."""

from pathlib import Path

import click

from dot_agent_kit.io import create_default_config, load_project_config
from dot_agent_kit.models.config import ProjectConfig


def _list_kits(config: ProjectConfig) -> None:
    """List all installed kits.

    Args:
        config: Project configuration
    """
    if not config.kits:
        click.echo("No kits installed")
        return

    click.echo("Installed kits:")
    for kit_id, kit in sorted(config.kits.items()):
        artifact_count = len(kit.artifacts)
        click.echo(f"  {kit_id} v{kit.version} ({artifact_count} artifacts)")


@click.command("list")
def list_kits() -> None:
    """List all installed kits."""
    project_dir = Path.cwd()
    loaded_config = load_project_config(project_dir)
    config = loaded_config if loaded_config is not None else create_default_config()
    _list_kits(config)
