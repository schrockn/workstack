"""Kit models for dot-agent kit manifests."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ArtifactMapping:
    """Mapping of a single artifact to its destination."""

    source_path: str  # Path within the kit package
    dest_path: str  # Destination path relative to .claude/
    artifact_type: str  # "command", "skill", "script", etc.


@dataclass(frozen=True)
class KitManifest:
    """Manifest for a dot-agent kit."""

    kit_id: str  # Unique identifier
    version: str  # Kit version
    description: str  # Brief description
    artifacts: list[ArtifactMapping]  # Files to install
    requires_python: str | None = None  # Python version requirement
    dependencies: list[str] = field(default_factory=list)  # Required packages

    def get_artifacts_by_type(self, artifact_type: str) -> list[ArtifactMapping]:
        """Get all artifacts of a specific type."""
        return [a for a in self.artifacts if a.artifact_type == artifact_type]
