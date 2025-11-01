"""Artifact validation operations."""

from dataclasses import dataclass
from pathlib import Path

from dot_agent_kit.io import load_project_config, parse_frontmatter, validate_frontmatter
from dot_agent_kit.sources import BundledKitSource


@dataclass(frozen=True)
class ValidationResult:
    """Result of artifact validation."""

    artifact_path: Path
    is_valid: bool
    errors: list[str]


@dataclass(frozen=True)
class SyncCheckResult:
    """Result of checking sync status for one artifact."""

    artifact_path: Path
    is_in_sync: bool
    reason: str | None = None


def validate_artifact(artifact_path: Path) -> ValidationResult:
    """Validate a single artifact file."""
    if not artifact_path.exists():
        return ValidationResult(
            artifact_path=artifact_path,
            is_valid=False,
            errors=["File does not exist"],
        )

    content = artifact_path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(content)

    if frontmatter is None:
        return ValidationResult(
            artifact_path=artifact_path,
            is_valid=False,
            errors=["No frontmatter found"],
        )

    errors = validate_frontmatter(frontmatter)

    return ValidationResult(
        artifact_path=artifact_path,
        is_valid=len(errors) == 0,
        errors=errors,
    )


def validate_project(project_dir: Path) -> list[ValidationResult]:
    """Validate all artifacts in project."""
    results: list[ValidationResult] = []

    claude_dir = project_dir / ".claude"
    if not claude_dir.exists():
        return results

    # Check all artifact directories
    for artifact_type in ["agents", "commands", "skills"]:
        artifact_dir = claude_dir / artifact_type
        if not artifact_dir.exists():
            continue

        for artifact_file in artifact_dir.glob("*.md"):
            result = validate_artifact(artifact_file)
            results.append(result)

    return results


def check_artifact_sync(
    project_dir: Path,
    artifact_rel_path: str,
    bundled_base: Path,
) -> SyncCheckResult:
    """Check if an artifact is in sync with bundled source."""
    # Artifact path in .claude/
    local_path = project_dir / artifact_rel_path

    # Corresponding bundled path (remove .claude/ prefix if present)
    artifact_rel = Path(artifact_rel_path)
    if artifact_rel.parts[0] == ".claude":
        artifact_rel = Path(*artifact_rel.parts[1:])

    bundled_path = bundled_base / artifact_rel

    # Check if both exist
    if not local_path.exists():
        return SyncCheckResult(
            artifact_path=local_path,
            is_in_sync=False,
            reason="Local artifact missing",
        )

    if not bundled_path.exists():
        return SyncCheckResult(
            artifact_path=local_path,
            is_in_sync=False,
            reason="Bundled artifact missing",
        )

    # Compare content
    try:
        local_content = local_path.read_bytes()
        bundled_content = bundled_path.read_bytes()

        if local_content != bundled_content:
            return SyncCheckResult(
                artifact_path=local_path,
                is_in_sync=False,
                reason="Content differs",
            )
    except Exception as e:
        return SyncCheckResult(
            artifact_path=local_path,
            is_in_sync=False,
            reason=f"Read error: {e}",
        )

    return SyncCheckResult(
        artifact_path=local_path,
        is_in_sync=True,
    )


def check_bundled_kits_sync(project_dir: Path) -> list[tuple[str, list[SyncCheckResult]]]:
    """Check sync status for all bundled kit artifacts in project.

    Returns a list of tuples containing (kit_id, list of sync check results).
    Only checks artifacts from bundled kits (not standalone/custom kits).
    """
    config = load_project_config(project_dir)
    if config is None:
        return []

    if len(config.kits) == 0:
        return []

    bundled_source = BundledKitSource()
    all_results: list[tuple[str, list[SyncCheckResult]]] = []

    for kit_id, installed in config.kits.items():
        # Only check kits from bundled source
        if not bundled_source.can_resolve(installed.source):
            continue

        # Get bundled kit base path
        bundled_path = bundled_source._get_bundled_kit_path(installed.source)
        if bundled_path is None:
            continue

        # Check each artifact
        kit_results: list[SyncCheckResult] = []
        for artifact_path in installed.artifacts:
            result = check_artifact_sync(project_dir, artifact_path, bundled_path)
            kit_results.append(result)

        all_results.append((kit_id, kit_results))

    return all_results
