"""Source for standalone dot-agent kit packages."""

from dot_agent_kit.io.manifest import load_kit_manifest
from dot_agent_kit.models.kit import KitManifest
from dot_agent_kit.utils.packaging import get_package_path, is_package_installed


class StandaloneSource:
    """Source for standalone dot-agent kit packages."""

    def __init__(self, package_name: str):
        self.package_name = package_name

    def is_available(self) -> bool:
        """Check if the package is installed and available."""
        return is_package_installed(self.package_name)

    def get_manifest(self) -> KitManifest | None:
        """Load the kit manifest from the package."""
        package_path = get_package_path(self.package_name)
        if not package_path:
            return None

        try:
            return load_kit_manifest(package_path)
        except FileNotFoundError:
            return None

    def get_artifact_content(self, source_path: str) -> bytes | None:
        """Read artifact content from the package."""
        package_path = get_package_path(self.package_name)
        if not package_path:
            return None

        artifact_path = package_path / source_path
        if not artifact_path.exists():
            return None

        return artifact_path.read_bytes()
