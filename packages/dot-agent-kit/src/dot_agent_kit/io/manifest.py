"""Kit manifest I/O operations."""

from pathlib import Path

import yaml

from dot_agent_kit.models.kit import ArtifactMapping, KitManifest


def load_kit_manifest(package_path: Path) -> KitManifest:
    """Load a kit manifest from a package directory."""
    manifest_path = package_path / "kit.yaml"

    if not manifest_path.exists():
        raise FileNotFoundError(f"No kit.yaml found in {package_path}")

    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    artifacts = [
        ArtifactMapping(
            source_path=a["source"],
            dest_path=a.get("dest", a["source"]),
            artifact_type=a.get("type", "unknown"),
        )
        for a in data.get("artifacts", [])
    ]

    return KitManifest(
        kit_id=data["kit_id"],
        version=data["version"],
        description=data.get("description", ""),
        artifacts=artifacts,
        requires_python=data.get("requires_python"),
        dependencies=data.get("dependencies", []),
    )
