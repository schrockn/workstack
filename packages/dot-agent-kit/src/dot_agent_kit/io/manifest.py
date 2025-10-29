"""Kit manifest I/O."""

from pathlib import Path

import yaml

from dot_agent_kit.models import KitManifest


def load_kit_manifest(manifest_path: Path) -> KitManifest:
    """Load kit.yaml manifest file."""
    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return KitManifest(
        name=data["name"],
        version=data["version"],
        description=data["description"],
        artifacts=data.get("artifacts", {}),
        license=data.get("license"),
        homepage=data.get("homepage"),
    )
