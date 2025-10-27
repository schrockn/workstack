"""Installation operations for dot-agent kits."""

from datetime import datetime
from pathlib import Path

import click

from dot_agent_kit.models.config import ConflictPolicy, InstalledKit, ProjectConfig
from dot_agent_kit.models.kit import KitManifest
from dot_agent_kit.sources.bundled import BundledSource
from dot_agent_kit.sources.standalone import StandaloneSource


def check_conflicts(manifest: KitManifest, config: ProjectConfig, root_dir: Path) -> list[Path]:
    """Check for file conflicts before installation."""
    conflicts = []

    for artifact in manifest.artifacts:
        dest_path = root_dir / artifact.dest_path
        if dest_path.exists():
            conflicts.append(dest_path)

    return conflicts


def install_artifacts(
    source: BundledSource | StandaloneSource,
    manifest: KitManifest,
    root_dir: Path,
    conflict_policy: ConflictPolicy,
) -> list[str]:
    """Install artifacts from a kit."""
    installed_artifacts = []

    for artifact in manifest.artifacts:
        dest_path = root_dir / artifact.dest_path

        # Handle conflicts
        if dest_path.exists():
            if conflict_policy == ConflictPolicy.ERROR:
                raise FileExistsError(f"File already exists: {dest_path}")
            elif conflict_policy == ConflictPolicy.SKIP:
                click.echo(f"  Skipping existing file: {artifact.dest_path}")
                continue
            # ConflictPolicy.OVERWRITE falls through

        # Create parent directory
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy artifact
        content = source.get_artifact_content(artifact.source_path)
        if content is None:
            click.echo(f"  Warning: Source file not found: {artifact.source_path}", err=True)
            continue

        dest_path.write_bytes(content)
        installed_artifacts.append(str(artifact.dest_path))

    return installed_artifacts


def install_from_source(
    source: BundledSource | StandaloneSource,
    kit_name: str,
    config: ProjectConfig,
    force: bool = False,
) -> InstalledKit:
    """Install a kit from any source (bundled or standalone)."""
    if not source.is_available():
        click.echo(f"Kit not available: {kit_name}", err=True)
        raise SystemExit(1)

    manifest = source.get_manifest()
    if not manifest:
        click.echo(f"No kit manifest found: {kit_name}", err=True)
        raise SystemExit(1)

    # Check for conflicts
    root_dir = Path(config.root_dir)
    conflicts = check_conflicts(manifest, config, root_dir)

    if conflicts and not force:
        click.echo("File conflicts detected:", err=True)
        for path in conflicts:
            click.echo(f"  {path}", err=True)
        click.echo("Use --force to overwrite")
        raise SystemExit(1)

    # Install artifacts
    conflict_policy = ConflictPolicy.OVERWRITE if force else config.conflict_policy
    installed_artifacts = install_artifacts(source, manifest, root_dir, conflict_policy)

    # Determine version and source type
    if isinstance(source, BundledSource):
        version = manifest.version
        source_type = "bundled"
        package_name = kit_name
    else:
        from dot_agent_kit.utils.packaging import get_package_version

        version = get_package_version(kit_name) or manifest.version
        source_type = "standalone"
        package_name = kit_name

    # Create installed kit record
    kit = InstalledKit(
        kit_id=manifest.kit_id,
        package_name=package_name,
        version=version,
        artifacts=installed_artifacts,
        install_date=datetime.now().isoformat(),
        source_type=source_type,
    )

    click.echo(
        f"✓ Installed {manifest.kit_id} v{kit.version} ({len(installed_artifacts)} artifacts)"
    )

    return kit


def install_kit(package_name: str, config: ProjectConfig, force: bool = False) -> InstalledKit:
    """Install a kit from a standalone package."""
    source = StandaloneSource(package_name)

    if not source.is_available():
        click.echo(f"Package not installed: {package_name}", err=True)
        click.echo(f"Run: uv pip install {package_name}")
        raise SystemExit(1)

    return install_from_source(source, package_name, config, force)
