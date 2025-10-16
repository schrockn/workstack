"""Package manager for discovering and managing packages."""

from pathlib import Path

from dot_agent_kit.packages.models import (
    FileInfo,
    Package,
    create_file_info,
)


def _parse_package_name(full_name: str) -> tuple[str | None, str]:
    """Parse a package name into namespace and package_name parts.

    Args:
        full_name: Full package name like "tools/gt" or "agentic_programming_guide"

    Returns:
        Tuple of (namespace, package_name) where namespace is None if not present.
    """
    if "/" in full_name:
        parts = full_name.split("/", 1)
        return (parts[0], parts[1])
    return (None, full_name)


class PackageManager:
    """Manager for package discovery and operations."""

    def __init__(self, agent_dir: Path):
        """Initialize the package manager.

        Args:
            agent_dir: Path to the .agent directory
        """
        self.agent_dir = agent_dir
        self.packages_dir = agent_dir / "packages"

    def discover_packages(self) -> dict[str, Package]:
        """Discover all packages in the packages directory.

        Returns:
            Dictionary mapping package names to Package objects.
        """
        if not self.packages_dir.exists():
            return {}

        packages: dict[str, Package] = {}

        # Scan for packages at packages/ root level
        for item in self.packages_dir.iterdir():
            if not item.is_dir():
                continue

            # Check if this is a namespace directory
            if self._is_namespace_dir(item):
                # Scan for packages within namespace
                for pkg_dir in item.iterdir():
                    if not pkg_dir.is_dir():
                        continue
                    namespace = item.name
                    pkg_name = pkg_dir.name
                    full_name = f"{namespace}/{pkg_name}"
                    package = self._load_package(pkg_dir, namespace, pkg_name, full_name)
                    if package is not None:
                        packages[full_name] = package
            else:
                # Regular package at root level
                pkg_name = item.name
                package = self._load_package(item, None, pkg_name, pkg_name)
                if package is not None:
                    packages[pkg_name] = package

        return packages

    def _is_namespace_dir(self, path: Path) -> bool:
        """Check if a directory is a namespace directory.

        A namespace directory contains subdirectories (packages) but no files.
        """
        has_subdirs = False
        has_files = False

        for item in path.iterdir():
            if item.is_dir():
                has_subdirs = True
            elif item.is_file() and item.name != ".gitkeep":
                has_files = True

        return has_subdirs and not has_files

    def _load_package(
        self,
        pkg_dir: Path,
        namespace: str | None,
        pkg_name: str,
        full_name: str,
    ) -> Package | None:
        """Load a package from a directory.

        Args:
            pkg_dir: Path to package directory
            namespace: Package namespace or None
            pkg_name: Package name without namespace
            full_name: Full package name including namespace

        Returns:
            Package object or None if loading fails.
        """
        files: dict[str, FileInfo] = {}

        # Collect all files in the package
        for item in pkg_dir.rglob("*"):
            if not item.is_file():
                continue

            file_info = create_file_info(item, pkg_dir)
            files[file_info.relative_path] = file_info

        return Package(
            name=full_name,
            namespace=namespace,
            package_name=pkg_name,
            path=pkg_dir,
            files=files,
        )

    def load_tool_package(self, cli_name: str) -> Package | None:
        """Load a package for a specific CLI tool.

        Args:
            cli_name: CLI command name (e.g., "gt", "gh")

        Returns:
            Package object or None if not found.
        """
        tool_package_name = f"tools/{cli_name}"
        packages = self.discover_packages()
        return packages.get(tool_package_name)
