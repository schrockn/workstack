"""Registry I/O operations for loading and saving registry data."""

from pathlib import Path

import yaml

from dot_agent_kit.models.registry import Registry, RegistryEntry


def load_bundled_registry() -> Registry:
    """Load the bundled registry from the package data directory."""
    registry_path = Path(__file__).parent.parent / "data" / "registry.yaml"

    with open(registry_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    entries = [
        RegistryEntry(
            name=entry["name"],
            url=entry["url"],
            description=entry.get("description", ""),
            package_name=entry.get("package_name", entry["name"]),
        )
        for entry in data["entries"]
    ]

    return Registry(entries=entries, version=data.get("version", "1.0.0"))


def save_registry(registry: Registry, path: Path) -> None:
    """Save a registry to a YAML file."""
    data = {
        "version": registry.version,
        "entries": [
            {
                "name": entry.name,
                "url": entry.url,
                "description": entry.description,
                "package_name": entry.package_name,
            }
            for entry in registry.entries
        ],
    }

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)
