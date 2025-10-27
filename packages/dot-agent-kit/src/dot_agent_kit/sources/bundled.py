"""Source for bundled dot-agent kit packages."""

from pathlib import Path

from dot_agent_kit.io.manifest import load_kit_manifest
from dot_agent_kit.models.kit import KitManifest


def get_bundled_kits_path() -> Path:
    """Get the path to the bundled-kits directory."""
    # Get the path to this module's directory
    this_file = Path(__file__)
    # Navigate to the data/bundled-kits directory
    # sources/bundled.py -> dot_agent_kit/ -> data/bundled-kits/
    return this_file.parent.parent / "data" / "bundled-kits"


class BundledSource:
    """Source for bundled dot-agent kit packages."""

    def __init__(self, kit_name: str):
        self.kit_name = kit_name
        self.kit_path = get_bundled_kits_path() / kit_name

    def is_available(self) -> bool:
        """Check if the bundled kit is available."""
        return self.kit_path.exists() and (self.kit_path / "kit.yaml").exists()

    def get_manifest(self) -> KitManifest | None:
        """Load the kit manifest from the bundled kit."""
        if not self.is_available():
            return None

        try:
            return load_kit_manifest(self.kit_path)
        except FileNotFoundError:
            return None

    def get_artifact_content(self, source_path: str) -> bytes | None:
        """Read artifact content from the bundled kit."""
        if not self.is_available():
            return None

        artifact_path = self.kit_path / source_path
        if not artifact_path.exists():
            return None

        return artifact_path.read_bytes()
