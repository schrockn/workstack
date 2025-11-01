"""Artifact metadata models."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


@dataclass(frozen=True)
class ArtifactFrontmatter:
    """Frontmatter metadata embedded in artifact files."""

    kit_id: str
    kit_version: str
    artifact_type: str
    artifact_path: str


class ArtifactSource(Enum):
    """Source type of an installed artifact."""

    MANAGED = "managed"  # Tracked in dot-agent.toml
    UNMANAGED = "unmanaged"  # From kit but not in config
    LOCAL = "local"  # Created manually, no kit association


@dataclass(frozen=True)
class InstalledArtifact:
    """Represents an installed artifact with its metadata."""

    artifact_type: str  # skill, command, agent
    artifact_name: str  # Display name
    file_path: Path  # Actual file location relative to .claude/
    source: ArtifactSource
    kit_id: str | None = None
    kit_version: str | None = None
