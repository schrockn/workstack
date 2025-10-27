"""Configuration models for dot-agent projects."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ConflictPolicy(Enum):
    """Policy for handling file conflicts during installation."""

    ERROR = "error"  # Raise error on conflict
    SKIP = "skip"  # Skip conflicting files
    OVERWRITE = "overwrite"  # Overwrite existing files
    MERGE = "merge"  # Attempt to merge (for certain file types)


@dataclass
class InstalledKit:
    """Information about an installed kit."""

    kit_id: str
    package_name: str
    version: str
    artifacts: list[str]  # List of installed artifact paths
    install_date: str
    source_type: str = "standalone"  # "standalone" or "embedded"

    def to_dict(self) -> dict:
        """Convert to dictionary for TOML serialization."""
        return {
            "kit_id": self.kit_id,
            "package_name": self.package_name,
            "version": self.version,
            "artifacts": self.artifacts,
            "install_date": self.install_date,
            "source_type": self.source_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InstalledKit":
        """Create from dictionary (TOML deserialization)."""
        return cls(**data)


@dataclass
class ProjectConfig:
    """Configuration for a project using dot-agent."""

    version: str = "1.0.0"  # Config format version
    root_dir: Path = field(default_factory=lambda: Path(".claude"))
    kits: dict[str, InstalledKit] = field(default_factory=dict)
    conflict_policy: ConflictPolicy = ConflictPolicy.ERROR
    disabled_artifacts: list[str] = field(default_factory=list)

    def add_kit(self, kit: InstalledKit) -> None:
        """Add or update a kit in the configuration."""
        self.kits[kit.kit_id] = kit

    def remove_kit(self, kit_id: str) -> None:
        """Remove a kit from the configuration."""
        self.kits.pop(kit_id, None)

    def get_kit(self, kit_id: str) -> InstalledKit | None:
        """Get a kit by ID."""
        return self.kits.get(kit_id)
