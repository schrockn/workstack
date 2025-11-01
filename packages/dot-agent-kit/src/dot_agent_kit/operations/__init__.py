"""Operations for dot-agent-kit."""

from dot_agent_kit.operations.artifact_selection import ArtifactSpec
from dot_agent_kit.operations.install import install_kit
from dot_agent_kit.operations.sync import (
    SyncResult,
    check_for_updates,
    sync_all_kits,
    sync_kit,
)
from dot_agent_kit.operations.user_install import (
    get_installation_context,
    install_kit_to_target,
)
from dot_agent_kit.operations.validation import (
    SyncCheckResult,
    ValidationResult,
    check_artifact_sync,
    check_bundled_kits_sync,
    validate_artifact,
    validate_project,
)

__all__ = [
    "ArtifactSpec",
    "get_installation_context",
    "install_kit",
    "install_kit_to_target",
    "SyncResult",
    "check_for_updates",
    "sync_all_kits",
    "sync_kit",
    "SyncCheckResult",
    "ValidationResult",
    "check_artifact_sync",
    "check_bundled_kits_sync",
    "validate_artifact",
    "validate_project",
]
