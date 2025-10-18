"""Metadata management for .agent/ folders in repositories."""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class RepoMetadata:
    """Metadata for repository .agent/ folder."""

    path: Path
    managed: bool
    installed_at: datetime | None = None
    original_hash: str | None = None
    current_hash: str | None = None
    source_url: str | None = None


def calculate_folder_hash(folder_path: Path) -> str:
    """Calculate SHA-256 hash of folder contents recursively.

    Returns a hex string hash of all file contents in sorted order.
    Excludes README.md to avoid circular dependency with metadata.
    """
    if not folder_path.exists():
        return ""

    if not folder_path.is_dir():
        return ""

    hasher = hashlib.sha256()

    # Collect all files recursively, excluding README.md
    files: list[Path] = []
    for item in sorted(folder_path.rglob("*")):
        if item.is_file() and item.name != "README.md":
            files.append(item)

    # Hash each file's content in sorted order
    for file_path in sorted(files):
        # Add relative path to hash for structure awareness
        relative = file_path.relative_to(folder_path)
        hasher.update(str(relative).encode("utf-8"))

        # Add file content
        content = file_path.read_bytes()
        hasher.update(content)

    return f"sha256:{hasher.hexdigest()}"


def parse_agent_frontmatter(content: str) -> dict[str, Any]:
    """Extract YAML frontmatter from .agent/README.md content.

    Returns the dot_agent section of frontmatter or empty dict if not present.
    """
    lines = content.split("\n")

    # Check if content starts with front matter delimiter
    if not lines or lines[0].strip() != "---":
        return {}

    # Find the closing delimiter
    closing_index = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_index = i
            break

    # If no closing delimiter found, return empty
    if closing_index == -1:
        return {}

    # Extract YAML content between delimiters
    yaml_content = "\n".join(lines[1:closing_index])

    # Parse YAML
    if not yaml_content.strip():
        return {}

    parsed = yaml.safe_load(yaml_content)
    if not isinstance(parsed, dict):
        return {}

    # Extract dot_agent section
    dot_agent = parsed.get("dot_agent", {})
    if not isinstance(dot_agent, dict):
        return {}

    return dot_agent


def update_agent_frontmatter(content: str, metadata: dict[str, Any]) -> str:
    """Add or update dot_agent frontmatter in .agent/README.md content.

    Preserves existing frontmatter structure but replaces dot_agent section.
    """
    lines = content.split("\n")

    # Check if content has existing frontmatter
    has_frontmatter = False
    closing_index = -1

    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                closing_index = i
                has_frontmatter = True
                break

    # Extract body content (after frontmatter if present)
    if has_frontmatter and closing_index != -1:
        body_content = "\n".join(lines[closing_index + 1 :]).lstrip()

        # Parse existing frontmatter
        yaml_content = "\n".join(lines[1:closing_index])
        existing_frontmatter: dict[str, Any] = {}
        if yaml_content.strip():
            parsed = yaml.safe_load(yaml_content)
            if isinstance(parsed, dict):
                existing_frontmatter = parsed
    else:
        body_content = content.lstrip()
        existing_frontmatter = {}

    # Update dot_agent section
    existing_frontmatter["dot_agent"] = metadata

    # Generate new frontmatter
    frontmatter_yaml = yaml.dump(existing_frontmatter, sort_keys=False, default_flow_style=False)

    return f"---\n{frontmatter_yaml}---\n\n{body_content}"


def get_repo_metadata(repo_path: Path) -> RepoMetadata | None:
    """Get metadata for .agent/ folder if it exists in the repository.

    Returns None if no .agent/ folder or README.md exists.
    """
    agent_dir = repo_path / ".agent"
    if not agent_dir.exists():
        return None

    if not agent_dir.is_dir():
        return None

    readme_path = agent_dir / "README.md"
    if not readme_path.exists():
        return None

    # Read and parse frontmatter
    content = readme_path.read_text(encoding="utf-8")
    frontmatter = parse_agent_frontmatter(content)

    # Extract metadata fields
    managed = frontmatter.get("managed", False)
    if not isinstance(managed, bool):
        managed = False

    installed_at_str = frontmatter.get("installed_at")
    installed_at: datetime | None = None
    if isinstance(installed_at_str, str):
        # Parse ISO 8601 timestamp
        installed_at = datetime.fromisoformat(installed_at_str.replace("Z", "+00:00"))

    original_hash = frontmatter.get("original_hash")
    if not isinstance(original_hash, str):
        original_hash = None

    current_hash_stored = frontmatter.get("current_hash")
    if not isinstance(current_hash_stored, str):
        current_hash_stored = None

    source_url = frontmatter.get("source_url")
    if not isinstance(source_url, str):
        source_url = None

    # Calculate current hash
    current_hash = calculate_folder_hash(agent_dir)

    return RepoMetadata(
        path=repo_path,
        managed=managed,
        installed_at=installed_at,
        original_hash=original_hash,
        current_hash=current_hash,
        source_url=source_url,
    )


def write_repo_metadata(repo_path: Path, metadata: dict[str, Any]) -> None:
    """Write metadata to .agent/README.md frontmatter.

    Creates README.md if it doesn't exist.
    Updates frontmatter if it does exist.
    """
    agent_dir = repo_path / ".agent"
    if not agent_dir.exists():
        return

    if not agent_dir.is_dir():
        return

    readme_path = agent_dir / "README.md"

    if readme_path.exists():
        # Update existing file
        content = readme_path.read_text(encoding="utf-8")
        updated_content = update_agent_frontmatter(content, metadata)
    else:
        # Create new file with frontmatter
        frontmatter_yaml = yaml.dump(
            {"dot_agent": metadata}, sort_keys=False, default_flow_style=False
        )
        updated_content = (
            f"---\n{frontmatter_yaml}---\n\n# .agent/ Directory\n\n"
            "This directory contains automated documentation and tooling configuration.\n"
        )

    readme_path.write_text(updated_content, encoding="utf-8")
