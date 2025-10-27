"""State I/O operations for project configuration (dot-agent.toml)."""

from pathlib import Path

import toml

from dot_agent_kit.models.config import ConflictPolicy, InstalledKit, ProjectConfig


def load_project_config(path: Path | None = None) -> ProjectConfig:
    """Load project configuration from dot-agent.toml."""
    config_path = path or Path("dot-agent.toml")

    if not config_path.exists():
        return ProjectConfig()

    with open(config_path, encoding="utf-8") as f:
        data = toml.load(f)

    config = ProjectConfig(
        version=data.get("version", "1.0.0"),
        root_dir=Path(data.get("root_dir", ".claude")),
        conflict_policy=ConflictPolicy(data.get("conflict_policy", "error")),
        disabled_artifacts=data.get("disabled_artifacts", []),
    )

    # Load installed kits
    for kit_data in data.get("kits", {}).values():
        kit = InstalledKit.from_dict(kit_data)
        config.add_kit(kit)

    return config


def save_project_config(config: ProjectConfig, path: Path | None = None) -> None:
    """Save project configuration to dot-agent.toml."""
    config_path = path or Path("dot-agent.toml")

    data = {
        "version": config.version,
        "root_dir": str(config.root_dir),
        "conflict_policy": config.conflict_policy.value,
        "disabled_artifacts": config.disabled_artifacts,
        "kits": {kit_id: kit.to_dict() for kit_id, kit in config.kits.items()},
    }

    with open(config_path, "w", encoding="utf-8") as f:
        toml.dump(data, f)
