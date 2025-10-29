"""Sync project-local artifacts to bundled kit."""

import shutil
from pathlib import Path

import click
import yaml


def discover_dev_kits(bundle_base: Path) -> list[str]:
    """Discover kits marked as in development.

    Args:
        bundle_base: The base path for bundled kits

    Returns:
        List of kit names that have sync_source: workstack-dev
    """
    if not bundle_base.exists():
        return []

    dev_kits = []
    for kit_dir in bundle_base.iterdir():
        if not kit_dir.is_dir():
            continue

        manifest_path = kit_dir / "kit.yaml"
        if not manifest_path.exists():
            continue

        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = yaml.safe_load(f)
                if manifest.get("sync_source") == "workstack-dev":
                    dev_kits.append(kit_dir.name)
        except Exception:
            # Skip kits with invalid manifests
            continue

    return sorted(dev_kits)


def validate_namespace_pattern(artifact_path: str, kit_name: str) -> tuple[bool, str | None]:
    """Validate that an artifact path follows the namespace pattern.

    Args:
        artifact_path: The artifact path from the manifest (e.g., "agents/devrun/runner.md")
        kit_name: The name of the kit

    Returns:
        Tuple of (is_valid, error_message)
    """
    parts = artifact_path.split("/")

    if len(parts) < 3:
        return False, f"Artifact '{artifact_path}' is not namespaced (too shallow)."

    artifact_type = parts[0]
    namespace = parts[1]

    # Check that the namespace matches the kit name
    if namespace != kit_name:
        expected_pattern = f"{artifact_type}/{kit_name}/..."
        return (
            False,
            f"Artifact '{artifact_path}' is not namespaced correctly.\n"
            f"    Expected pattern: {expected_pattern}",
        )

    return True, None


def sync_artifact(
    source_path: Path,
    dest_path: Path,
    artifact_path: str,
    dry_run: bool,
    verbose: bool,
) -> bool:
    """Sync a single artifact from source to destination.

    Args:
        source_path: The source file path
        dest_path: The destination file path
        artifact_path: The relative artifact path for display
        dry_run: Whether this is a dry run
        verbose: Whether to show verbose output

    Returns:
        True if successful, False otherwise
    """
    if not source_path.exists():
        click.echo(f"  ⚠ {artifact_path} (source not found)", err=True)
        return False

    if verbose:
        click.echo(f"  {source_path}")
        click.echo(f"  → {dest_path}")

    if not dry_run:
        # Create parent directories if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy the file
        try:
            shutil.copy2(source_path, dest_path)
            if verbose:
                size_kb = source_path.stat().st_size / 1024
                click.echo(f"  ✓ Synced ({size_kb:.1f} KB)")
            else:
                click.echo(f"✓ {artifact_path}")
            return True
        except Exception as e:
            click.echo(f"  ✗ {artifact_path} (error: {e})", err=True)
            return False
    else:
        # Dry run - just report what would be done
        return True


def sync_single_kit(
    kit_name: str,
    project_root: Path,
    claude_dir: Path,
    bundle_base: Path,
    dry_run: bool,
    verbose: bool,
) -> bool:
    """Sync a single kit's artifacts.

    Args:
        kit_name: Name of the kit to sync
        project_root: Project root directory
        claude_dir: Path to .claude directory
        bundle_base: Base path for bundled kits
        dry_run: Whether to perform a dry run
        verbose: Whether to show verbose output

    Returns:
        True if sync succeeded, False otherwise
    """
    kit_path = bundle_base / kit_name
    manifest_path = kit_path / "kit.yaml"

    # Check if kit exists
    if not kit_path.exists():
        click.echo(f"Error: Kit '{kit_name}' not found at {kit_path}", err=True)
        return False

    # Check if manifest exists
    if not manifest_path.exists():
        click.echo(f"Error: Manifest not found at {manifest_path}", err=True)
        return False

    # Header output
    if dry_run:
        click.echo(f"Syncing kit: {kit_name} (DRY RUN)")
    else:
        click.echo(f"Syncing kit: {kit_name}")

    if verbose:
        click.echo(f"Bundle path: {kit_path}")
        click.echo("Loading manifest: kit.yaml")

    click.echo()

    # Parse manifest
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
    except yaml.YAMLError as e:
        click.echo(f"Error: Invalid manifest YAML: {e}", err=True)
        return False
    except Exception as e:
        click.echo(f"Error: Failed to read manifest: {e}", err=True)
        return False

    # Check if kit is managed by dot-agent and warn
    existing_sync_source = manifest.get("sync_source")
    if existing_sync_source and existing_sync_source != "workstack-dev":
        click.echo(
            f"Warning: Kit is marked as managed by '{existing_sync_source}'. "
            f"Proceeding will change management to 'workstack-dev'.",
            err=True,
        )
        click.echo()

    # Mark as managed by workstack-dev (will be saved after successful sync)
    manifest["sync_source"] = "workstack-dev"

    # Get artifacts from manifest
    artifacts = manifest.get("artifacts", {})
    all_artifacts = []

    # Collect all artifact paths (using singular forms as per KitManifest model)
    for artifact_type in ["agent", "skill", "command", "hook"]:
        type_artifacts = artifacts.get(artifact_type, [])
        if type_artifacts:
            all_artifacts.extend(type_artifacts)

    if not all_artifacts:
        click.echo("No artifacts found in manifest.", err=True)
        return False

    # Validate namespace patterns
    if verbose:
        click.echo("Validating namespace patterns...")

    validation_errors = []
    for artifact_path in all_artifacts:
        is_valid, error_msg = validate_namespace_pattern(artifact_path, kit_name)
        if not is_valid:
            validation_errors.append((artifact_path, error_msg))
        elif verbose:
            click.echo(f"✓ {artifact_path} (valid)")

    if validation_errors:
        click.echo(
            f"\nError: Kit '{kit_name}' does not follow required namespace pattern:",
            err=True,
        )
        for _, error_msg in validation_errors:
            click.echo(f"  - {error_msg}", err=True)
        click.echo(
            "\nSync aborted. Fix namespace patterns in kit.yaml and try again.",
            err=True,
        )
        return False

    if verbose:
        click.echo()

    # Perform sync operations
    if verbose:
        click.echo("Syncing artifacts...")

    if dry_run:
        click.echo("Would sync:")

    success_count = 0
    failed_count = 0

    for artifact_path in all_artifacts:
        # Determine artifact type from path
        parts = artifact_path.split("/")
        artifact_type = parts[0]

        # Map source and destination paths
        # Source: .claude/{type}/{kit_name}/...
        # But the artifact_path already includes the type and kit_name
        # So source is: .claude/{artifact_path without the s suffix on type}

        # Remove the 's' from the artifact type for the source path
        artifact_type.rstrip("s")
        if artifact_type == "agents":
            pass  # agents stays as agents in .claude/
        elif artifact_type == "skills":
            pass  # skills stays as skills in .claude/
        elif artifact_type == "commands":
            pass  # commands stays as commands in .claude/
        elif artifact_type == "hooks":
            pass  # hooks stays as hooks in .claude/

        source_path = claude_dir / artifact_path
        dest_path = kit_path / artifact_path

        if dry_run:
            click.echo(f"  {artifact_path}")
            success_count += 1
        else:
            if sync_artifact(source_path, dest_path, artifact_path, dry_run, verbose):
                success_count += 1
            else:
                failed_count += 1

    # Summary
    click.echo()
    if dry_run:
        click.echo(f"{success_count} artifacts would be synced (no changes made)")
    else:
        if failed_count > 0:
            click.echo(f"{success_count} artifacts synced successfully, {failed_count} failed")
            return False
        else:
            # Update manifest with sync_source marker on successful sync
            try:
                with open(manifest_path, "w", encoding="utf-8") as f:
                    yaml.dump(manifest, f, sort_keys=False)
                if verbose:
                    click.echo("Updated manifest with sync_source: workstack-dev")
            except Exception as e:
                click.echo(f"Warning: Failed to update manifest with sync_source: {e}", err=True)

            click.echo(f"{success_count} artifacts synced successfully")

    return True


@click.command(name="sync-kit")
@click.argument("kit_name", required=False)
@click.option("--dry-run", is_flag=True, help="Preview changes without writing files")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed sync operations")
def sync_kit_command(kit_name: str | None, dry_run: bool, verbose: bool) -> None:
    """Sync project-local artifacts from .claude/ to bundled kit.

    When KIT_NAME is provided, syncs only that kit.
    When KIT_NAME is omitted, syncs all kits marked with sync_source: workstack-dev.

    Syncs artifacts from .claude/ to packages/dot-agent-kit/src/dot_agent_kit/data/kits/.
    """
    # Path resolution
    project_root = Path.cwd()
    claude_dir = project_root / ".claude"
    bundle_base = project_root / "packages/dot-agent-kit/src/dot_agent_kit/data/kits"

    # Determine which kits to sync
    if kit_name:
        # Single kit mode
        kits_to_sync = [kit_name]
    else:
        # Multi-kit mode - discover all dev kits
        kits_to_sync = discover_dev_kits(bundle_base)
        if not kits_to_sync:
            click.echo("No kits found with sync_source: workstack-dev", err=True)
            raise SystemExit(1)

        if dry_run:
            click.echo(f"Found {len(kits_to_sync)} kit(s) to sync: {', '.join(kits_to_sync)}")
        else:
            click.echo(f"Syncing {len(kits_to_sync)} kit(s): {', '.join(kits_to_sync)}")
        click.echo()

    # Sync each kit
    failed_kits = []
    for current_kit in kits_to_sync:
        success = sync_single_kit(
            current_kit,
            project_root,
            claude_dir,
            bundle_base,
            dry_run,
            verbose,
        )
        if not success:
            failed_kits.append(current_kit)

        # Add separator between kits when syncing multiple
        if len(kits_to_sync) > 1 and current_kit != kits_to_sync[-1]:
            click.echo()
            click.echo("=" * 60)
            click.echo()

    # Final summary for multi-kit sync
    if len(kits_to_sync) > 1:
        click.echo()
        click.echo("=" * 60)
        if failed_kits:
            failed_list = ", ".join(failed_kits)
            click.echo(
                f"Sync completed with errors. {len(failed_kits)} kit(s) failed: {failed_list}",
                err=True,
            )
            raise SystemExit(1)
        else:
            click.echo(f"All {len(kits_to_sync)} kit(s) synced successfully")
    elif failed_kits:
        # Single kit failed
        raise SystemExit(1)
