"""Repository interface for artifact discovery."""

from abc import ABC, abstractmethod
from pathlib import Path

from dot_agent_kit.models.artifact import InstalledArtifact
from dot_agent_kit.models.config import ProjectConfig


class ArtifactRepository(ABC):
    """Abstract interface for artifact discovery operations."""

    @abstractmethod
    def discover_all_artifacts(
        self, project_dir: Path, config: ProjectConfig
    ) -> list[InstalledArtifact]:
        """Discover all installed artifacts with their metadata.

        Args:
            project_dir: Project root directory
            config: Project configuration from dot-agent.toml

        Returns:
            List of all installed artifacts with metadata
        """
        pass
