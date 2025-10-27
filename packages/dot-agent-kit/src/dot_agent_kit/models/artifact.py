"""Artifact models for validation and frontmatter."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactFrontmatter:
    """Frontmatter from a dot-agent kit artifact."""

    kit_id: str | None = None
    version: str | None = None
    description: str | None = None
    artifact_type: str | None = None
    tags: list[str] | None = None

    def validate(self) -> list[str]:
        """Validate frontmatter and return any errors."""
        errors = []

        if not self.kit_id:
            errors.append("Missing required field: kit_id")

        if self.kit_id and not self._is_valid_kit_id(self.kit_id):
            errors.append(f"Invalid kit_id format: {self.kit_id}")

        return errors

    @staticmethod
    def _is_valid_kit_id(kit_id: str) -> bool:
        """Check if kit_id follows naming conventions."""
        import re

        # PEP 503 normalized names: lowercase, hyphens only
        pattern = r"^[a-z0-9]+(-[a-z0-9]+)*-dot-agent-kit$"
        return bool(re.match(pattern, kit_id))


@dataclass(frozen=True)
class Artifact:
    """A validated artifact from a kit."""

    path: Path
    content: str
    frontmatter: ArtifactFrontmatter | None
    validation_errors: list[str]

    @property
    def is_valid(self) -> bool:
        """Check if the artifact is valid."""
        return len(self.validation_errors) == 0
