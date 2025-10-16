from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dot_agent_kit import __version__, list_available_files

CONFIG_FILENAME = ".dot-agent-kit.yml"


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


def _as_tuple(value: Any) -> tuple[str, ...]:
    """Convert a YAML list into a tuple of strings."""
    if not isinstance(value, list):
        return ()

    items: list[str] = []
    for item in value:
        if isinstance(item, str):
            items.append(item)

    return tuple(items)


@dataclass(frozen=True, slots=True)
class DotAgentConfig:
    version: str
    installed_files: tuple[str, ...]
    exclude: tuple[str, ...]
    custom_files: tuple[str, ...]

    @classmethod
    def default(cls) -> "DotAgentConfig":
        """Return the default configuration with all available files."""
        available_files = tuple(list_available_files())
        return cls(
            version=__version__,
            installed_files=available_files,
            exclude=(),
            custom_files=(),
        )

    @classmethod
    def load(cls, config_path: Path) -> "DotAgentConfig":
        """Load configuration from disk, falling back to defaults."""
        if not config_path.exists():
            return cls.default()

        raw_text = config_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw_text) or {}
        if not isinstance(data, dict):
            return cls.default()

        version = data.get("version")
        if not isinstance(version, str):
            version = __version__

        # Support both old "managed_files" and new "installed_files" keys for backward compatibility
        installed_files = _as_tuple(
            data.get("installed_files", data.get("managed_files", []))
        )
        if not installed_files:
            # Default to all available files if not specified
            installed_files = tuple(list_available_files())

        exclude = _as_tuple(data.get("exclude", []))
        custom_files = _as_tuple(data.get("custom_files", []))

        return cls(
            version=version,
            installed_files=installed_files,
            exclude=exclude,
            custom_files=custom_files,
        )

    def save(self, config_path: Path) -> None:
        """Persist the configuration to disk."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": self.version,
            "installed_files": list(self.installed_files),
            "exclude": list(self.exclude),
            "custom_files": list(self.custom_files),
        }
        serialized = yaml.safe_dump(
            data,
            sort_keys=False,
            default_flow_style=False,
        )
        config_path.write_text(serialized, encoding="utf-8")


def get_config_path(agent_dir: Path) -> Path:
    """Return the canonical config path inside a .agent directory."""
    return agent_dir / CONFIG_FILENAME


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
