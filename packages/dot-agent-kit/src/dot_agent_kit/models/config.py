"""Configuration models for dot-agent-kit."""

from dataclasses import dataclass
from enum import Enum


class ConflictPolicy(Enum):
    """How to handle file conflicts during installation."""

    ERROR = "error"  # Fail on conflicts (default)
    SKIP = "skip"  # Skip conflicting files
    OVERWRITE = "overwrite"  # Replace existing files
    MERGE = "merge"  # Intelligent merging (future)


@dataclass(frozen=True)
class InstalledKit:
    """Represents an installed kit in dot-agent.toml."""

    kit_id: str
    version: str
    source: str
    installed_at: str
    artifacts: list[str]
    conflict_policy: str = "error"


@dataclass(frozen=True)
class ProjectConfig:
    """Project configuration from dot-agent.toml."""

    version: str
    default_conflict_policy: ConflictPolicy
    kits: dict[str, InstalledKit]
