"""Utilities for parsing markdown front matter and finding .agent directories."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class MarkdownMetadata:
    """Metadata extracted from YAML front matter."""

    description: str | None = None
    url: str | None = None


def parse_markdown_frontmatter(content: str) -> tuple[MarkdownMetadata, str]:
    """Extract YAML front matter from markdown content.

    Returns a tuple of (metadata, remaining_content).
    If no front matter is present, returns empty metadata and full content.
    """
    lines = content.split("\n")

    # Check if content starts with front matter delimiter
    if not lines or lines[0].strip() != "---":
        return MarkdownMetadata(), content

    # Find the closing delimiter
    closing_index = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_index = i
            break

    # If no closing delimiter found, treat as normal content
    if closing_index == -1:
        return MarkdownMetadata(), content

    # Extract YAML content between delimiters
    yaml_content = "\n".join(lines[1:closing_index])

    # Parse YAML
    metadata_dict: dict[str, Any] = {}
    if yaml_content.strip():
        parsed = yaml.safe_load(yaml_content)
        if isinstance(parsed, dict):
            metadata_dict = parsed

    # Extract known fields
    description = metadata_dict.get("description")
    url = metadata_dict.get("url")

    # Validate types
    if not isinstance(description, str):
        description = None
    if not isinstance(url, str):
        url = None

    metadata = MarkdownMetadata(description=description, url=url)

    # Return remaining content after front matter
    remaining_lines = lines[closing_index + 1 :]
    remaining_content = "\n".join(remaining_lines).lstrip()

    return metadata, remaining_content


def find_agent_dir(start: Path | None = None) -> Path | None:
    """Walk upwards from start (default: cwd) to locate a .agent directory."""
    if start is None:
        start = Path.cwd()

    current = start
    while True:
        agent_dir = current / ".agent"
        if agent_dir.exists() and agent_dir.is_dir():
            return agent_dir

        parent = current.parent
        if parent == current:
            return None
        current = parent
