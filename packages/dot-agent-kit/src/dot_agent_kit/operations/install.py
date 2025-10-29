"""Kit installation operations."""

from datetime import datetime
from pathlib import Path

from dot_agent_kit.io import add_frontmatter, load_kit_manifest
from dot_agent_kit.models import ArtifactFrontmatter, ConflictPolicy, InstalledKit
from dot_agent_kit.sources import ResolvedKit


def install_kit(
    resolved: ResolvedKit,
    project_dir: Path,
    conflict_policy: ConflictPolicy = ConflictPolicy.ERROR,
) -> InstalledKit:
    """Install a kit to the project."""
    manifest = load_kit_manifest(resolved.manifest_path)
    claude_dir = project_dir / ".claude"

    # Create .claude directory if needed
    if not claude_dir.exists():
        claude_dir.mkdir(parents=True)

    installed_artifacts: list[str] = []

    # Process each artifact type
    for artifact_type, paths in manifest.artifacts.items():
        # Map artifact type to .claude subdirectory
        target_dir = claude_dir / f"{artifact_type}s"  # agents, commands, skills
        if not target_dir.exists():
            target_dir.mkdir(parents=True)

        for artifact_path in paths:
            # Read source artifact
            source = resolved.artifacts_base / artifact_path
            if not source.exists():
                continue

            content = source.read_text(encoding="utf-8")

            # Add frontmatter
            frontmatter = ArtifactFrontmatter(
                kit_id=manifest.name,
                kit_version=manifest.version,
                artifact_type=artifact_type,
                artifact_path=artifact_path,
            )
            content_with_fm = add_frontmatter(content, frontmatter)

            # Determine target path
            target = target_dir / source.name

            # Check for conflicts (ERROR policy only for now)
            if target.exists():
                raise FileExistsError(
                    f"Artifact already exists: {target}\n"
                    f"Use --force to overwrite or change conflict policy"
                )

            # Write artifact
            target.write_text(content_with_fm, encoding="utf-8")

            # Track installation
            installed_artifacts.append(str(target.relative_to(project_dir)))

    return InstalledKit(
        kit_id=manifest.name,
        version=manifest.version,
        source=resolved.source,
        installed_at=datetime.now().isoformat(),
        artifacts=installed_artifacts,
        conflict_policy=conflict_policy.value,
    )
