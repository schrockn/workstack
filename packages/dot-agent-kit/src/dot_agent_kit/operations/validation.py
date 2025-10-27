"""Artifact validation operations."""

from dataclasses import dataclass
from pathlib import Path

from dot_agent_kit.io import parse_frontmatter, validate_frontmatter


@dataclass(frozen=True)
class ValidationResult:
    """Result of artifact validation."""

    artifact_path: Path
    is_valid: bool
    errors: list[str]


def validate_artifact(artifact_path: Path) -> ValidationResult:
    """Validate a single artifact file."""
    if not artifact_path.exists():
        return ValidationResult(
            artifact_path=artifact_path,
            is_valid=False,
            errors=["File does not exist"],
        )

    content = artifact_path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(content)

    if frontmatter is None:
        return ValidationResult(
            artifact_path=artifact_path,
            is_valid=False,
            errors=["No frontmatter found"],
        )

    errors = validate_frontmatter(frontmatter)

    return ValidationResult(
        artifact_path=artifact_path,
        is_valid=len(errors) == 0,
        errors=errors,
    )


def validate_project(project_dir: Path) -> list[ValidationResult]:
    """Validate all artifacts in project."""
    results: list[ValidationResult] = []

    claude_dir = project_dir / ".claude"
    if not claude_dir.exists():
        return results

    # Check all artifact directories
    for artifact_type in ["agents", "commands", "skills"]:
        artifact_dir = claude_dir / artifact_type
        if not artifact_dir.exists():
            continue

        for artifact_file in artifact_dir.glob("*.md"):
            result = validate_artifact(artifact_file)
            results.append(result)

    return results
