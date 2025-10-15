from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dot_agent_kit import __version__

CONFIG_FILENAME = ".dot-agent-kit.yml"
DEFAULT_MANAGED_FILES: tuple[str, ...] = ("tools/",)


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
    managed_files: tuple[str, ...]
    exclude: tuple[str, ...]
    custom_files: tuple[str, ...]

    @classmethod
    def default(cls) -> "DotAgentConfig":
        """Return the default configuration."""
        return cls(
            version=__version__,
            managed_files=DEFAULT_MANAGED_FILES,
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

        managed_files = _as_tuple(data.get("managed_files", list(DEFAULT_MANAGED_FILES)))
        if not managed_files:
            managed_files = DEFAULT_MANAGED_FILES

        exclude = _as_tuple(data.get("exclude", []))
        custom_files = _as_tuple(data.get("custom_files", []))

        return cls(
            version=version,
            managed_files=managed_files,
            exclude=exclude,
            custom_files=custom_files,
        )

    def save(self, config_path: Path) -> None:
        """Persist the configuration to disk."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": self.version,
            "managed_files": list(self.managed_files),
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
