"""Sync operations for updating installed kits."""

from pathlib import Path

import click

from dot_agent_kit.models.config import InstalledKit, ProjectConfig
from dot_agent_kit.operations.install import install_artifacts
from dot_agent_kit.sources.standalone import StandaloneSource
from dot_agent_kit.utils.packaging import get_package_version


def check_kit_updates(kit: InstalledKit) -> str | None:
    """Check if a kit has updates available."""
    current_version = get_package_version(kit.package_name)
    if current_version and current_version != kit.version:
        return current_version
    return None


def sync_kit(kit: InstalledKit, config: ProjectConfig) -> InstalledKit | None:
    """Sync a single kit to its current package version."""
    new_version = check_kit_updates(kit)
    if not new_version:
        return None

    source = StandaloneSource(kit.package_name)
    manifest = source.get_manifest()
    if not manifest:
        click.echo(f"  Warning: Cannot load manifest for {kit.kit_id}", err=True)
        return None

    # Reinstall artifacts
    # Use OVERWRITE policy for sync to allow updates to replace existing files
    from dot_agent_kit.models.config import ConflictPolicy

    root_dir = Path(config.root_dir)
    installed_artifacts = install_artifacts(source, manifest, root_dir, ConflictPolicy.OVERWRITE)

    # Update kit record
    kit.version = new_version
    kit.artifacts = installed_artifacts

    return kit


def sync_all_kits(config: ProjectConfig) -> list[tuple[InstalledKit, str]]:
    """Sync all installed kits."""
    updated_kits = []

    for kit in config.kits.values():
        old_version = kit.version
        updated_kit = sync_kit(kit, config)

        if updated_kit:
            config.add_kit(updated_kit)
            updated_kits.append((updated_kit, old_version))
            click.echo(f"✓ Updated {kit.kit_id} {old_version} → {updated_kit.version}")
        else:
            click.echo(f"✓ {kit.kit_id} v{kit.version} - up to date")

    return updated_kits
