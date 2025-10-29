"""List command for showing installed and available kits."""

from pathlib import Path

import click

from dot_agent_kit.io import load_kit_manifest, load_project_config
from dot_agent_kit.models import KitManifest, ProjectConfig
from dot_agent_kit.sources import BundledKitSource, KitSource


def _get_artifact_name(artifact_path: str) -> str:
    """Extract artifact name from path (strip extension)."""
    return Path(artifact_path).stem


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
@click.option(
    "--artifacts",
    "-a",
    is_flag=True,
    help="Show individual artifacts within each kit",
)
def list_cmd(artifacts: bool, sources: list[KitSource] | None = None) -> None:
    """List installed and available kits (alias: ls).

    Args:
        artifacts: Whether to show individual artifacts within each kit
        sources: List of kit sources to check (for testing only)
    """
    if sources is None:
        sources = [BundledKitSource()]

    # Load project config
    project_dir = Path.cwd()
    config = load_project_config(project_dir)

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
@click.option(
    "--artifacts",
    "-a",
    is_flag=True,
    help="Show individual artifacts within each kit",
)
def ls_cmd(artifacts: bool, sources: list[KitSource] | None = None) -> None:
    """List installed and available kits (alias of 'list').

    Args:
        artifacts: Whether to show individual artifacts within each kit
        sources: List of kit sources to check (for testing only)
    """
    if sources is None:
        sources = [BundledKitSource()]

    # Load project config
    project_dir = Path.cwd()
    config = load_project_config(project_dir)

    # Load manifests for all available kits
    manifests: dict[str, KitManifest] = {}
    for source in sources:
        for kit_id in source.list_available():
            if source.can_resolve(kit_id):
                resolved = source.resolve(kit_id)
                if resolved.manifest_path.exists():
                    manifests[kit_id] = load_kit_manifest(resolved.manifest_path)

    _list_kits(artifacts, config, manifests, sources)
