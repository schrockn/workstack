"""Package synchronization operations."""

import shutil
from dataclasses import dataclass
from datetime import datetime
from importlib.resources.abc import Traversable
from pathlib import Path

from dot_agent_kit import get_resource_root
from dot_agent_kit.packages.manager import PackageManager, _parse_package_name
from dot_agent_kit.packages.manifest import PackageManifest, get_manifest_path
from dot_agent_kit.packages.models import SyncResult, compute_file_hash


@dataclass(frozen=True, slots=True)
class ConflictInfo:
    """Information about a file conflict."""

    file_path: str
    expected_hash: str
    actual_hash: str


class PackageSyncer:
    """Handles package synchronization operations."""

    def __init__(self, agent_dir: Path):
        """Initialize the package syncer.

        Args:
            agent_dir: Path to the .agent directory
        """
        self.agent_dir = agent_dir
        self.packages_dir = agent_dir / "packages"
        self.manager = PackageManager(agent_dir)

    def check_sync_conflicts(self, package_name: str) -> list[ConflictInfo]:
        """Check if a package has local modifications.

        Args:
            package_name: Full package name (e.g., "tools/gt")

        Returns:
            List of ConflictInfo for files with conflicts.
        """
        manifest_path = get_manifest_path(self.agent_dir)
        manifest = PackageManifest.load(manifest_path)

        if package_name not in manifest.packages:
            return []

        source_info = manifest.packages[package_name]
        if not source_info.file_hashes:
            return []

        namespace, pkg_name = _parse_package_name(package_name)
        if namespace:
            pkg_dir = self.packages_dir / namespace / pkg_name
        else:
            pkg_dir = self.packages_dir / pkg_name

        if not pkg_dir.exists():
            return []

        conflicts: list[ConflictInfo] = []
        for file_path, expected_hash in source_info.file_hashes.items():
            local_path = pkg_dir / file_path
            if not local_path.exists():
                conflicts.append(
                    ConflictInfo(
                        file_path=file_path,
                        expected_hash=expected_hash,
                        actual_hash="",
                    )
                )
                continue

            actual_hash = compute_file_hash(local_path)
            if actual_hash != expected_hash:
                conflicts.append(
                    ConflictInfo(
                        file_path=file_path,
                        expected_hash=expected_hash,
                        actual_hash=actual_hash,
                    )
                )

        return conflicts

    def sync_package(self, package_name: str, *, force: bool = False) -> SyncResult:
        """Sync a specific package from bundled resources.

        Args:
            package_name: Full package name (e.g., "tools/gt")
            force: If True, overwrite local modifications

        Returns:
            SyncResult indicating the outcome.
        """
        manifest_path = get_manifest_path(self.agent_dir)
        manifest = PackageManifest.load(manifest_path)

        if package_name not in manifest.packages:
            return SyncResult(
                package_name=package_name,
                status="error",
                message=f"Package not found in manifest: {package_name}",
            )

        source_info = manifest.packages[package_name]
        if source_info.source != "bundled":
            return SyncResult(
                package_name=package_name,
                status="skipped",
                message=f"Package is not bundled: {source_info.source}",
            )

        # Check for conflicts
        conflicts = self.check_sync_conflicts(package_name)
        if conflicts and not force:
            return SyncResult(
                package_name=package_name,
                status="conflict",
                message="Local modifications detected. Use --force to overwrite.",
                files_conflicted=[c.file_path for c in conflicts],
            )

        # Create backup if forcing over conflicts
        if conflicts and force:
            self._create_backup(package_name)

        # Perform sync
        files_updated = self._sync_bundled_package(package_name)

        return SyncResult(
            package_name=package_name,
            status="success",
            message=f"Synced {files_updated} files",
            files_updated=files_updated,
        )

    def _create_backup(self, package_name: str) -> None:
        """Create a backup of a package before overwriting.

        Args:
            package_name: Full package name
        """
        namespace, pkg_name = _parse_package_name(package_name)
        if namespace:
            pkg_dir = self.packages_dir / namespace / pkg_name
        else:
            pkg_dir = self.packages_dir / pkg_name

        if not pkg_dir.exists():
            return

        # Create backup directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_name = f"{package_name.replace('/', '-')}-{timestamp}"
        backup_dir = self.agent_dir / ".backups" / backup_name

        backup_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(pkg_dir, backup_dir)

    def _sync_bundled_package(self, package_name: str) -> int:
        """Sync a bundled package from resources.

        Args:
            package_name: Full package name

        Returns:
            Number of files updated.
        """
        namespace, pkg_name = _parse_package_name(package_name)
        if namespace:
            pkg_dir = self.packages_dir / namespace / pkg_name
        else:
            pkg_dir = self.packages_dir / pkg_name

        pkg_dir.mkdir(parents=True, exist_ok=True)

        # Get bundled resources
        resource_root = get_resource_root()
        if namespace:
            resource_pkg_dir = resource_root.joinpath(namespace).joinpath(pkg_name)
        else:
            resource_pkg_dir = resource_root.joinpath(pkg_name)

        if not resource_pkg_dir.is_dir():
            return 0

        files_updated = 0

        # Copy all files from resource package using iterdir (since Traversable doesn't have rglob)
        def _copy_dir(src_dir: Traversable, dest_dir: Path) -> None:
            nonlocal files_updated
            for item in src_dir.iterdir():
                if item.is_file():
                    dest_path = dest_dir / item.name
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    content = item.read_text(encoding="utf-8")
                    dest_path.write_text(content, encoding="utf-8")
                    files_updated += 1
                elif item.is_dir():
                    _copy_dir(item, dest_dir / item.name)

        _copy_dir(resource_pkg_dir, pkg_dir)

        # Update manifest with file hashes
        self._update_manifest_hashes(package_name, pkg_dir)

        return files_updated

    def _update_manifest_hashes(self, package_name: str, pkg_dir: Path) -> None:
        """Update manifest with current file hashes.

        Args:
            package_name: Full package name
            pkg_dir: Path to package directory
        """
        manifest_path = get_manifest_path(self.agent_dir)
        manifest = PackageManifest.load(manifest_path)

        if package_name not in manifest.packages:
            return

        source_info = manifest.packages[package_name]

        # Compute hashes for all files
        file_hashes: dict[str, str] = {}
        for item in pkg_dir.rglob("*"):
            if not item.is_file():
                continue
            if item.name == "package.yaml":
                continue

            relative_path = str(item.relative_to(pkg_dir))
            file_hash = compute_file_hash(item)
            file_hashes[relative_path] = file_hash

        # Create updated source info
        from dot_agent_kit.packages.models import PackageSource

        updated_source = PackageSource(
            source=source_info.source,
            version=source_info.version,
            path=source_info.path,
            url=source_info.url,
            ref=source_info.ref,
            file_hashes=file_hashes,
        )

        # Update manifest
        updated_packages = dict(manifest.packages)
        updated_packages[package_name] = updated_source

        updated_manifest = PackageManifest(
            version=manifest.version,
            packages=updated_packages,
        )

        updated_manifest.save(manifest_path)
