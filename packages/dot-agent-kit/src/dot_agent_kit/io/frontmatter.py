"""Frontmatter parsing and injection."""

import re

import yaml

from dot_agent_kit.models import ArtifactFrontmatter

FRONTMATTER_PATTERN = re.compile(
    r"<!--\s*dot-agent-kit:\s*\n(.*?)\n\s*-->", re.DOTALL | re.MULTILINE
)


def validate_frontmatter(frontmatter: ArtifactFrontmatter) -> list[str]:
    """Validate frontmatter structure and return errors."""
    errors: list[str] = []

    # Validate kit_id format (kebab-case)
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", frontmatter.kit_id):
        errors.append(f"Invalid kit_id format: {frontmatter.kit_id}")

    # Validate version format (semver-ish)
    if not re.match(r"^\d+\.\d+\.\d+", frontmatter.kit_version):
        errors.append(f"Invalid version format: {frontmatter.kit_version}")

    # Validate artifact_type
    valid_types = {"agent", "command", "skill"}
    if frontmatter.artifact_type not in valid_types:
        errors.append(
            f"Invalid artifact_type: {frontmatter.artifact_type} (must be one of {valid_types})"
        )

    return errors


def parse_frontmatter(content: str) -> ArtifactFrontmatter | None:
    """Extract frontmatter from markdown content."""
    match = FRONTMATTER_PATTERN.search(content)
    if not match:
        return None

    yaml_content = match.group(1)
    data = yaml.safe_load(yaml_content)

    return ArtifactFrontmatter(
        kit_id=data["kit_id"],
        kit_version=data["kit_version"],
        artifact_type=data["artifact_type"],
        artifact_path=data["artifact_path"],
    )


def add_frontmatter(content: str, frontmatter: ArtifactFrontmatter) -> str:
    """Add frontmatter to markdown content."""
    fm_yaml = yaml.dump(
        {
            "kit_id": frontmatter.kit_id,
            "kit_version": frontmatter.kit_version,
            "artifact_type": frontmatter.artifact_type,
            "artifact_path": frontmatter.artifact_path,
        },
        default_flow_style=False,
    )

    fm_block = f"<!-- dot-agent-kit:\n{fm_yaml}-->\n\n"
    return fm_block + content
