"""Sync command for updating kits."""

from pathlib import Path

import click

from dot_agent_kit.io import load_project_config
from dot_agent_kit.operations import check_for_updates, sync_all_kits, sync_kit
from dot_agent_kit.sources import KitResolver, StandalonePackageSource


@click.command()
@click.argument("kit-id", required=False)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed sync information",
)
def sync(kit_id: str | None, verbose: bool) -> None:
    """Sync installed kits with their sources."""
    project_dir = Path.cwd()

    config = load_project_config(project_dir)
    if config is None:
        click.echo("Error: No dot-agent.toml found", err=True)
        raise SystemExit(1)

    if len(config.kits) == 0:
        click.echo("No kits installed")
        return

    resolver = KitResolver(sources=[StandalonePackageSource()])

    # Sync specific kit or all kits
    if kit_id is not None:
        if kit_id not in config.kits:
            click.echo(f"Error: Kit '{kit_id}' not installed", err=True)
            raise SystemExit(1)

        installed = config.kits[kit_id]
        has_update, resolved = check_for_updates(installed, resolver)

        if not has_update or resolved is None:
            click.echo(f"Kit '{kit_id}' is up to date")
            return

        result = sync_kit(kit_id, installed, resolved, project_dir)

        if result.was_updated:
            click.echo(f"✓ Updated {kit_id}: {result.old_version} → {result.new_version}")
            if verbose:
                click.echo(f"  Artifacts: {result.artifacts_updated}")

    else:
        # Sync all kits
        results = sync_all_kits(config, project_dir, resolver)

        updated_count = sum(1 for r in results if r.was_updated)

        if verbose or updated_count > 0:
            for result in results:
                if result.was_updated:
                    click.echo(f"✓ {result.kit_id}: {result.old_version} → {result.new_version}")
                elif verbose:
                    click.echo(f"  {result.kit_id}: up to date")

        if updated_count == 0:
            click.echo("All kits are up to date")
        else:
            click.echo(f"\nUpdated {updated_count} kit(s)")
