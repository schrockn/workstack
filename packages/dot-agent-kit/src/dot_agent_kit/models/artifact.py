"""Artifact metadata models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactFrontmatter:
    """Frontmatter metadata embedded in artifact files."""

    kit_id: str
    kit_version: str
    artifact_type: str
    artifact_path: str
