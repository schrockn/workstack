"""Discover and manage local files in the .agent directory.

This module handles files that exist in the .agent directory root and
subdirectories (excluding packages/), which are user-created files that
are never touched by the sync system.
"""

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LocalFile:
    """Metadata for a local file in the .agent directory.

    Args:
        relative_path: Path relative to .agent/ root (e.g., "ARCHITECTURE.md", "docs/guide.md")
        full_path: Absolute path to the file
        size: File size in bytes
        modified_time: Last modification timestamp (seconds since epoch)
        file_type: File extension without dot (e.g., "md", "txt") or "directory"
    """

    relative_path: str
    full_path: Path
    size: int
    modified_time: float
    file_type: str

    @property
    def is_directory(self) -> bool:
        """Return True if this represents a directory."""
        return self.file_type == "directory"


class LocalFileDiscovery:
    """Discover local files in the .agent directory."""

    def __init__(self, agent_dir: Path) -> None:
        """Initialize discovery for the given .agent directory.

        Args:
            agent_dir: Path to the .agent directory
        """
        self.agent_dir = agent_dir

    def discover_local_files(
        self,
        pattern: str | None = None,
        include_directories: bool = False,
    ) -> list[LocalFile]:
        """Discover all local files in the .agent directory.

        This scans the .agent directory root and all subdirectories, excluding
        the packages/ directory which contains installed package files.

        Args:
            pattern: Optional glob pattern to filter files (e.g., "*.md", "docs/*")
            include_directories: If True, include directories in the results

        Returns:
            List of LocalFile objects sorted by relative path
        """
        if not self.agent_dir.exists():
            return []

        local_files: list[LocalFile] = []

        # Walk the .agent directory
        for path in self.agent_dir.rglob("*"):
            # Skip packages/ directory entirely
            if self._is_in_packages(path):
                continue

            # Skip hidden files and directories (except .agent itself)
            if self._is_hidden(path):
                continue

            # Handle directories
            if path.is_dir():
                if include_directories:
                    local_file = self._create_local_file(path, is_directory=True)
                    if pattern is None or fnmatch(local_file.relative_path, pattern):
                        local_files.append(local_file)
                continue

            # Handle regular files
            if path.is_file():
                local_file = self._create_local_file(path, is_directory=False)
                if pattern is None or fnmatch(local_file.relative_path, pattern):
                    local_files.append(local_file)

        return sorted(local_files, key=lambda f: f.relative_path)

    def _is_in_packages(self, path: Path) -> bool:
        """Check if a path is inside the packages/ directory."""
        packages_dir = self.agent_dir / "packages"
        if not packages_dir.exists():
            return False

        # Check if path is packages dir itself or is relative to it
        if path == packages_dir:
            return True

        # Check if packages_dir is in the path's parents
        return packages_dir in path.parents

    def _is_hidden(self, path: Path) -> bool:
        """Check if a path or any of its components (relative to agent_dir) are hidden.

        Hidden means starting with a dot, excluding the .agent directory itself.
        """
        relative = path.relative_to(self.agent_dir)
        for part in relative.parts:
            if part.startswith("."):
                return True
        return False

    def _create_local_file(self, path: Path, is_directory: bool) -> LocalFile:
        """Create a LocalFile object from a Path."""
        relative = path.relative_to(self.agent_dir)
        stat = path.stat()

        if is_directory:
            file_type = "directory"
            size = 0
        else:
            suffix = path.suffix.lstrip(".")
            file_type = suffix if suffix else "no-extension"
            size = stat.st_size

        return LocalFile(
            relative_path=str(relative),
            full_path=path,
            size=size,
            modified_time=stat.st_mtime,
            file_type=file_type,
        )

    def get_file(self, relative_path: str) -> LocalFile | None:
        """Get a specific local file by relative path.

        Args:
            relative_path: Path relative to .agent/ root

        Returns:
            LocalFile if found, None otherwise
        """
        full_path = self.agent_dir / relative_path

        if not full_path.exists():
            return None

        # Check if it's in packages/
        if self._is_in_packages(full_path):
            return None

        if full_path.is_dir():
            return self._create_local_file(full_path, is_directory=True)

        if full_path.is_file():
            return self._create_local_file(full_path, is_directory=False)

        return None

    def read_file(self, relative_path: str) -> str:
        """Read the contents of a local file.

        Args:
            relative_path: Path relative to .agent/ root

        Returns:
            File contents as a string

        Raises:
            FileNotFoundError: If file doesn't exist
            IsADirectoryError: If path points to a directory
            ValueError: If path is in packages/ directory
        """
        full_path = self.agent_dir / relative_path

        if not full_path.exists():
            msg = f"File not found: {relative_path}"
            raise FileNotFoundError(msg)

        if self._is_in_packages(full_path):
            msg = f"Cannot read installed package file: {relative_path}"
            raise ValueError(msg)

        if full_path.is_dir():
            msg = f"Path is a directory: {relative_path}"
            raise IsADirectoryError(msg)

        return full_path.read_text(encoding="utf-8")

    def categorize_files(self, files: list[LocalFile]) -> dict[str, list[LocalFile]]:
        """Categorize files by their top-level directory.

        Args:
            files: List of LocalFile objects to categorize

        Returns:
            Dictionary mapping category names to lists of files.
            Files in the root have category "root".
        """
        categories: dict[str, list[LocalFile]] = {}

        for file in files:
            parts = Path(file.relative_path).parts
            if len(parts) == 1:
                category = "root"
            else:
                category = parts[0]

            if category not in categories:
                categories[category] = []
            categories[category].append(file)

        return categories
