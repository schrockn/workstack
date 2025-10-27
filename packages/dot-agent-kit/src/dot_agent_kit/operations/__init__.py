"""Operations for dot-agent-kit."""

from dot_agent_kit.operations.install import install_kit
from dot_agent_kit.operations.sync import (
    SyncResult,
    check_for_updates,
    sync_all_kits,
    sync_kit,
)
from dot_agent_kit.operations.validation import (
    ValidationResult,
    validate_artifact,
    validate_project,
)

__all__ = [
    "install_kit",
    "SyncResult",
    "check_for_updates",
    "sync_all_kits",
    "sync_kit",
    "ValidationResult",
    "validate_artifact",
    "validate_project",
]
