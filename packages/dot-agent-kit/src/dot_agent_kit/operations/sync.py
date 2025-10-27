"""Sync operations for updating installed kits."""

from dot_agent_kit.models.config import InstalledKit
from dot_agent_kit.utils.packaging import get_package_version


def check_kit_updates(kit: InstalledKit) -> str | None:
    """Check if a kit has updates available."""
    current_version = get_package_version(kit.package_name)
    if current_version and current_version != kit.version:
        return current_version
    return None
