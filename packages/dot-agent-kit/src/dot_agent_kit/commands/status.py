"""Status command for showing installed kits."""

from pathlib import Path

import click

from dot_agent_kit.io import load_project_config, load_user_config


@click.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed installation information",
)
def status(verbose: bool) -> None:
    """Show installed kits in user and project directories.

    Displays which kits are installed globally (user directory) and
    locally (project directory), along with version information.
    """
    project_dir = Path.cwd()

    # Load both configs
    user_config = load_user_config()
    loaded_project_config = load_project_config(project_dir)

    # Check if any kits installed
    has_user_kits = len(user_config.kits) > 0
    has_project_kits = loaded_project_config is not None and len(loaded_project_config.kits) > 0

    if not has_user_kits and not has_project_kits:
        click.echo("No kits installed")
        return

    # Display user-installed kits
    if has_user_kits:
        click.echo("User kits (~/.claude):")
        for kit_id, kit in sorted(user_config.kits.items()):
            click.echo(f"  {kit_id} v{kit.version}")
            if verbose:
                click.echo(f"    Source: {kit.source}")
                click.echo(f"    Artifacts: {len(kit.artifacts)}")
                click.echo(f"    Installed: {kit.installed_at}")
        click.echo()

    # Display project-installed kits
    if has_project_kits and loaded_project_config is not None:
        click.echo("Project kits (./.claude):")
        for kit_id, kit in sorted(loaded_project_config.kits.items()):
            click.echo(f"  {kit_id} v{kit.version}")
            if verbose:
                click.echo(f"    Source: {kit.source}")
                click.echo(f"    Artifacts: {len(kit.artifacts)}")
                click.echo(f"    Installed: {kit.installed_at}")
        click.echo()

    # Summary
    project_kits_count = len(loaded_project_config.kits) if loaded_project_config is not None else 0
    total_kits = len(user_config.kits) + project_kits_count
    click.echo(f"Total: {total_kits} kit(s) installed")
