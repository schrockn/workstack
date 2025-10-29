"""List command for showing installed and available kits."""

from pathlib import Path

import click

from dot_agent_kit.io import (
    create_default_config,
    load_kit_manifest,
    load_project_config,
    load_user_config,
)
from dot_agent_kit.models import KitManifest, ProjectConfig
from dot_agent_kit.sources import (
    BundledKitSource,
    KitResolver,
    KitSource,
    StandalonePackageSource,
)


def _get_artifact_name(artifact_path: str) -> str:
    """Extract artifact name from path (strip extension)."""
    return Path(artifact_path).stem


def _show_kit_details(kit_id: str) -> None:
    """Show detailed information about a specific kit.

    Args:
        kit_id: The kit to show details for
    """
    # Try to resolve the kit
    resolver = KitResolver(sources=[BundledKitSource(), StandalonePackageSource()])
    resolved = resolver.resolve(kit_id)

    if resolved is None:
        click.echo(f"Error: Kit '{kit_id}' not found", err=True)
        raise SystemExit(1)

    # Load manifest
    manifest = load_kit_manifest(resolved.manifest_path)

    # Load configs to check installation status
    project_dir = Path.cwd()
    user_config = load_user_config()
    project_config = load_project_config(project_dir)

    # Display kit header
    click.echo(f"Kit: {manifest.name}")
    click.echo(f"Version: {manifest.version}")
    click.echo(f"Description: {manifest.description}")

    if manifest.author:
        click.echo(f"Author: {manifest.author}")

    if manifest.license:
        click.echo(f"License: {manifest.license}")

    if manifest.homepage:
        click.echo(f"Homepage: {manifest.homepage}")

    click.echo()

    # Show installation status
    installed_in_user = kit_id in user_config.kits
    installed_in_project = project_config is not None and kit_id in project_config.kits

    if installed_in_user or installed_in_project:
        click.echo("Installation status:")
        if installed_in_user:
            user_kit = user_config.kits[kit_id]
            click.echo(f"  User (~/.claude): v{user_kit.version}")
        if installed_in_project and project_config is not None:
            project_kit = project_config.kits[kit_id]
            click.echo(f"  Project (./.claude): v{project_kit.version}")
        click.echo()
    else:
        click.echo("Not installed")
        click.echo()

    # Show artifacts
    total_artifacts = sum(len(paths) for paths in manifest.artifacts.values())
    click.echo(f"Artifacts ({total_artifacts} total):")

    for artifact_type, artifact_paths in sorted(manifest.artifacts.items()):
        click.echo(f"  {artifact_type}:")
        for artifact_path in sorted(artifact_paths):
            artifact_name = _get_artifact_name(artifact_path)
            click.echo(f"    - {artifact_name}")

    click.echo()
    click.echo("To install:")
    click.echo(f"  Entire kit:      dot-agent install {kit_id}")
    click.echo(f"  Specific artifact: dot-agent install {kit_id}:artifact-name")


def _list_kits(
    show_artifacts: bool,
    config: ProjectConfig,
    manifests: dict[str, KitManifest],
    sources: list[KitSource],
) -> None:
    """Internal function to list installed and available kits.

    Args:
        show_artifacts: Whether to display individual artifacts for each kit
        config: Project configuration
        manifests: Mapping of kit_id -> manifest for artifact display
        sources: List of kit sources to check for available kits
    """
    # Get available kits from all sources
    available_kit_ids: set[str] = set()
    for source in sources:
        available_kit_ids.update(source.list_available())

    # Get installed kit IDs
    installed_kit_ids: set[str] = set(config.kits.keys())

    # Combine all kits (available + installed)
    all_kit_ids = available_kit_ids | installed_kit_ids

    if len(all_kit_ids) == 0:
        click.echo("No kits available")
        return

    # Display each kit with status
    for kit_id in sorted(all_kit_ids):
        # Determine status
        is_available = kit_id in available_kit_ids
        is_installed = kit_id in installed_kit_ids

        if is_available:
            status = "[BUNDLED]"
        elif is_installed:
            status = "[INSTALLED]"
        else:
            status = ""

        click.echo(f"{kit_id} {status}")

        # Show artifacts if requested
        if show_artifacts:
            # Look up manifest from provided dict
            manifest = manifests.get(kit_id)

            if manifest:
                # Display artifacts grouped by type
                for artifact_type, artifact_paths in manifest.artifacts.items():
                    for artifact_path in artifact_paths:
                        artifact_name = _get_artifact_name(artifact_path)
                        click.echo(f"  {artifact_type}: {artifact_name}")

            click.echo()


@click.command("list")
@click.argument("kit-id", required=False)
@click.option(
    "--artifacts",
    "-a",
    is_flag=True,
    help="Show individual artifacts within each kit",
)
def list_cmd(kit_id: str | None, artifacts: bool, sources: list[KitSource] | None = None) -> None:
    """List installed and available kits, or show details for a specific kit.

    When KIT_ID is provided, shows detailed information about that kit.
    Without arguments, lists all available kits.

    Args:
        kit_id: Optional kit ID to show details for
        artifacts: Whether to show individual artifacts within each kit (list mode only)
        sources: List of kit sources to check (for testing only)
    """
    # If a specific kit is requested, show details
    if kit_id is not None:
        _show_kit_details(kit_id)
        return

    # Otherwise, list all kits
    if sources is None:
        sources = [BundledKitSource()]

    # Load project config
    project_dir = Path.cwd()
    loaded_config = load_project_config(project_dir)
    config = loaded_config if loaded_config is not None else create_default_config()

    # Load manifests for all available kits
    manifests: dict[str, KitManifest] = {}
    for source in sources:
        for kit_id in source.list_available():
            if source.can_resolve(kit_id):
                resolved = source.resolve(kit_id)
                if resolved.manifest_path.exists():
                    manifests[kit_id] = load_kit_manifest(resolved.manifest_path)

    _list_kits(artifacts, config, manifests, sources)


@click.command("ls", hidden=True)
@click.argument("kit-id", required=False)
@click.option(
    "--artifacts",
    "-a",
    is_flag=True,
    help="Show individual artifacts within each kit",
)
def ls_cmd(kit_id: str | None, artifacts: bool, sources: list[KitSource] | None = None) -> None:
    """List installed and available kits, or show details for a specific kit (alias of 'list').

    Args:
        kit_id: Optional kit ID to show details for
        artifacts: Whether to show individual artifacts within each kit (list mode only)
        sources: List of kit sources to check (for testing only)
    """
    # If a specific kit is requested, show details
    if kit_id is not None:
        _show_kit_details(kit_id)
        return

    # Otherwise, list all kits
    if sources is None:
        sources = [BundledKitSource()]

    # Load project config
    project_dir = Path.cwd()
    loaded_config = load_project_config(project_dir)
    config = loaded_config if loaded_config is not None else create_default_config()

    # Load manifests for all available kits
    manifests: dict[str, KitManifest] = {}
    for source in sources:
        for kit_id in source.list_available():
            if source.can_resolve(kit_id):
                resolved = source.resolve(kit_id)
                if resolved.manifest_path.exists():
                    manifests[kit_id] = load_kit_manifest(resolved.manifest_path)

    _list_kits(artifacts, config, manifests, sources)
