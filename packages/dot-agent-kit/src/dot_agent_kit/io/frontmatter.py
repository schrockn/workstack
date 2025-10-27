"""Frontmatter parsing for dot-agent kit artifacts."""

import re
from pathlib import Path

import yaml

from dot_agent_kit.models.artifact import Artifact, ArtifactFrontmatter


def parse_frontmatter(content: str) -> tuple[ArtifactFrontmatter | None, str]:
    """Parse YAML frontmatter from markdown content."""
    # Look for dot-agent-kit frontmatter
    pattern = r"<!--\s*dot-agent-kit:\s*\n(.*?)\n-->"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return None, content

    try:
        frontmatter_yaml = match.group(1)
        data = yaml.safe_load(frontmatter_yaml)

        frontmatter = ArtifactFrontmatter(
            kit_id=data.get("kit_id"),
            version=data.get("version"),
            description=data.get("description"),
            artifact_type=data.get("type"),
            tags=data.get("tags", []),
        )

        # Remove frontmatter from content
        content_without_fm = content[: match.start()] + content[match.end() :]

        return frontmatter, content_without_fm
    except yaml.YAMLError:
        # Invalid YAML in frontmatter
        return None, content


def load_artifact(path: Path) -> Artifact:
    """Load and validate an artifact file."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        return Artifact(
            path=path, content="", frontmatter=None, validation_errors=[f"Failed to read file: {e}"]
        )

    frontmatter, content_body = parse_frontmatter(content)

    validation_errors = []
    if frontmatter:
        validation_errors.extend(frontmatter.validate())

    return Artifact(
        path=path,
        content=content_body,
        frontmatter=frontmatter,
        validation_errors=validation_errors,
    )
