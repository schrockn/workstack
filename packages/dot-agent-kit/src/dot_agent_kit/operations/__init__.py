"""Operations for dot-agent-kit."""

from dot_agent_kit.operations.install import install_kit
from dot_agent_kit.operations.validation import (
    ValidationResult,
    validate_artifact,
    validate_project,
)

__all__ = [
    "install_kit",
    "ValidationResult",
    "validate_artifact",
    "validate_project",
]
