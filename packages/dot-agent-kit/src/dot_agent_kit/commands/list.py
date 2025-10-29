"""List command for showing installed and available kits."""

from pathlib import Path

import click

from dot_agent_kit.io import load_project_config, load_registry


def _list_kits() -> None:
    """Internal function to list installed and available kits."""
    project_dir = Path.cwd()
    config = load_project_config(project_dir)
    registry = load_registry()

    # Get set of installed kit IDs for quick lookup
    installed_kit_ids: set[str] = set(config.kits.keys()) if config else set()

    # Display installed kits first
    if config and len(config.kits) > 0:
        click.echo(f"Installed kits ({len(config.kits)}):\n")
        for kit_id, kit in config.kits.items():
            click.echo(f"  {kit_id} (v{kit.version})")
            click.echo(f"  └─ Source: {kit.source}")
            click.echo(f"     Artifacts: {len(kit.artifacts)}")
            click.echo()
    else:
        click.echo("No kits installed\n")

    # Display available kits from registry
    available_kits = [entry for entry in registry if entry.kit_id not in installed_kit_ids]

    if len(available_kits) > 0:
        click.echo(f"Available kits ({len(available_kits)}):\n")
        for entry in available_kits:
            click.echo(f"  {entry.name} [AVAILABLE]")
            click.echo(f"  └─ {entry.description}")
            click.echo(f"     Source: {entry.source}")
            if entry.author:
                click.echo(f"     Author: {entry.author}")
            if entry.tags:
                click.echo(f"     Tags: {', '.join(entry.tags)}")
            click.echo()


@click.command("list")
def list_cmd() -> None:
    """List installed and available kits (alias: ls)."""
    _list_kits()


@click.command("ls", hidden=True)
def ls_cmd() -> None:
    """List installed and available kits (alias of 'list')."""
    _list_kits()
