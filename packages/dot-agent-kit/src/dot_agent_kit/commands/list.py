"""List command for showing installed and available kits."""

from pathlib import Path

import click

from dot_agent_kit.io import load_kit_manifest, load_project_config


def _get_bundled_kits() -> list[str]:
    """Get list of bundled kit IDs."""
    data_dir = Path(__file__).parent.parent / "data" / "kits"
    if not data_dir.exists():
        return []

    bundled_kits = []
    for kit_dir in data_dir.iterdir():
        if kit_dir.is_dir() and (kit_dir / "kit.yaml").exists():
            bundled_kits.append(kit_dir.name)

    return bundled_kits


def _get_artifact_name(artifact_path: str) -> str:
    """Extract artifact name from path (strip extension)."""
    return Path(artifact_path).stem


def _get_bundled_manifest_path(kit_id: str) -> Path | None:
    """Get path to bundled kit manifest if it exists."""
    data_dir = Path(__file__).parent.parent / "data" / "kits" / kit_id
    manifest_path = data_dir / "kit.yaml"
    if manifest_path.exists():
        return manifest_path
    return None


def _list_kits(show_artifacts: bool) -> None:
    """Internal function to list installed and available kits."""
    project_dir = Path.cwd()
    config = load_project_config(project_dir)

    # Get bundled kits
    bundled_kit_ids = _get_bundled_kits()

    # Get installed kit IDs
    installed_kit_ids: set[str] = set(config.kits.keys()) if config else set()

    # Combine all kits (bundled + installed)
    all_kit_ids = set(bundled_kit_ids) | installed_kit_ids

    if len(all_kit_ids) == 0:
        click.echo("No kits available")
        return

    # Display each kit with status
    for kit_id in sorted(all_kit_ids):
        # Determine status
        is_bundled = kit_id in bundled_kit_ids
        is_installed = kit_id in installed_kit_ids

        if is_bundled:
            status = "[BUNDLED]"
        elif is_installed:
            status = "[INSTALLED]"
        else:
            status = ""

        click.echo(f"{kit_id} {status}")

        # Show artifacts if requested
        if show_artifacts:
            # Load manifest to get artifacts
            manifest_path = None

            if is_bundled:
                manifest_path = _get_bundled_manifest_path(kit_id)
            elif is_installed and config:
                # For installed kits, we need to resolve the manifest
                # For now, skip showing artifacts for non-bundled installed kits
                pass

            if manifest_path:
                manifest = load_kit_manifest(manifest_path)

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
def list_cmd(artifacts: bool) -> None:
    """List installed and available kits (alias: ls)."""
    _list_kits(artifacts)


@click.command("ls", hidden=True)
@click.option(
    "--artifacts",
    "-a",
    is_flag=True,
    help="Show individual artifacts within each kit",
)
def ls_cmd(artifacts: bool) -> None:
    """List installed and available kits (alias of 'list')."""
    _list_kits(artifacts)
