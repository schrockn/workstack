"""Installation target and context models."""

from enum import Enum
from pathlib import Path


class InstallationTarget(Enum):
    """Where to install a kit."""

    USER = "user"
    PROJECT = "project"


class InstallationContext:
    """Context for installation operations."""

    def __init__(self, target: InstallationTarget, base_path: Path):
        """Initialize installation context.

        Args:
            target: Where to install (user or project)
            base_path: Base path for the installation (home dir for user, project dir for project)
        """
        self.target = target
        self.base_path = base_path

    def get_claude_dir(self) -> Path:
        """Get the .claude directory path for this installation."""
        return self.base_path / ".claude"

    def get_config_path(self) -> Path:
        """Get the dot-agent.toml path for this installation."""
        return self.base_path / "dot-agent.toml"
