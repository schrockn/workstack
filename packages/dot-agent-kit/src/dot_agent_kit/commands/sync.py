"""Sync command for updating installed kits."""

import click

from dot_agent_kit.io.state import load_project_config, save_project_config
from dot_agent_kit.operations.sync import sync_all_kits


@click.command()
@click.option("--dry-run", is_flag=True, help="Show what would be updated")
def sync(dry_run: bool) -> None:
    """Sync all installed kits to their latest versions."""
    config = load_project_config()

    if not config.kits:
        click.echo("No kits installed")
        return

    if dry_run:
        click.echo("Would update:")
        for kit in config.kits.values():
            from dot_agent_kit.operations.sync import check_kit_updates

            new_version = check_kit_updates(kit)
            if new_version:
                click.echo(f"  - {kit.kit_id} {kit.version} → {new_version}")
        return

    updated_kits = sync_all_kits(config)

    if updated_kits:
        save_project_config(config)
        click.echo(f"\n{len(updated_kits)} kits updated")
    else:
        click.echo("All kits up to date")
