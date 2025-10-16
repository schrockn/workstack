"""Data models for the package system."""

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileInfo:
    """Information about a file within a package."""

    relative_path: str
    hash: str
    modified_time: float
    size: int


@dataclass(frozen=True, slots=True)
class Package:
    """A package containing related documentation files."""

    name: str
    namespace: str | None
    package_name: str
    path: Path
    files: dict[str, FileInfo]

    @property
    def install_path(self) -> Path:
        """Return the installation path relative to .agent/ directory."""
        if self.namespace:
            return Path("packages") / self.namespace / self.package_name
        return Path("packages") / self.package_name

    @property
    def full_name(self) -> str:
        """Return the full package name including namespace."""
        if self.namespace:
            return f"{self.namespace}/{self.package_name}"
        return self.package_name


def compute_file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not path.exists():
        return ""

    hasher = hashlib.sha256()
    content = path.read_bytes()
    hasher.update(content)
    return f"sha256:{hasher.hexdigest()}"


def create_file_info(path: Path, relative_to: Path) -> FileInfo:
    """Create FileInfo for a file."""
    if not path.exists():
        msg = f"File does not exist: {path}"
        raise FileNotFoundError(msg)

    relative_path = str(path.relative_to(relative_to))
    stat = path.stat()

    return FileInfo(
        relative_path=relative_path,
        hash=compute_file_hash(path),
        modified_time=stat.st_mtime,
        size=stat.st_size,
    )
