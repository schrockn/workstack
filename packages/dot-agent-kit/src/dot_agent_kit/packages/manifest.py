"""Package manifest handling (.dot-agent-kit.yml)."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from dot_agent_kit import __version__
from dot_agent_kit.packages.models import PackageSource

MANIFEST_FILENAME = ".dot-agent-kit.yml"


@dataclass(frozen=True, slots=True)
class PackageManifest:
    """Manifest describing installed packages."""

    version: str
    packages: dict[str, PackageSource]

    @classmethod
    def default(cls) -> "PackageManifest":
        """Return a default manifest with bundled packages."""
        return cls(
            version=__version__,
            packages={
                "agentic_programming_guide": PackageSource(
                    source="bundled",
                    version=__version__,
                ),
                "tools/gt": PackageSource(
                    source="bundled",
                    version=__version__,
                ),
                "tools/gh": PackageSource(
                    source="bundled",
                    version=__version__,
                ),
                "tools/workstack": PackageSource(
                    source="bundled",
                    version=__version__,
                ),
            },
        )

    @classmethod
    def load(cls, manifest_path: Path) -> "PackageManifest":
        """Load manifest from disk, falling back to defaults."""
        if not manifest_path.exists():
            return cls.default()

        raw_text = manifest_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw_text) or {}
        if not isinstance(data, dict):
            return cls.default()

        version = data.get("version")
        if not isinstance(version, str):
            version = __version__

        packages_data = data.get("packages", {})
        if not isinstance(packages_data, dict):
            packages_data = {}

        packages: dict[str, PackageSource] = {}
        for pkg_name, pkg_info in packages_data.items():
            if not isinstance(pkg_info, dict):
                continue

            source = pkg_info.get("source", "bundled")
            if source not in {"bundled", "local", "git"}:
                source = "bundled"

            version_str = pkg_info.get("version")
            if not isinstance(version_str, str):
                version_str = None

            path_str = pkg_info.get("path")
            if not isinstance(path_str, str):
                path_str = None

            url_str = pkg_info.get("url")
            if not isinstance(url_str, str):
                url_str = None

            ref_str = pkg_info.get("ref")
            if not isinstance(ref_str, str):
                ref_str = None

            file_hashes = pkg_info.get("file_hashes", {})
            if not isinstance(file_hashes, dict):
                file_hashes = {}

            packages[pkg_name] = PackageSource(
                source=source,
                version=version_str,
                path=path_str,
                url=url_str,
                ref=ref_str,
                file_hashes=file_hashes,
            )

        return cls(version=version, packages=packages)

    def save(self, manifest_path: Path) -> None:
        """Persist the manifest to disk."""
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        packages_dict: dict[str, dict[str, Any]] = {}
        for pkg_name, pkg_source in self.packages.items():
            pkg_dict: dict[str, Any] = {"source": pkg_source.source}

            if pkg_source.version is not None:
                pkg_dict["version"] = pkg_source.version

            if pkg_source.path is not None:
                pkg_dict["path"] = pkg_source.path

            if pkg_source.url is not None:
                pkg_dict["url"] = pkg_source.url

            if pkg_source.ref is not None:
                pkg_dict["ref"] = pkg_source.ref

            if pkg_source.file_hashes:
                pkg_dict["file_hashes"] = dict(pkg_source.file_hashes)

            packages_dict[pkg_name] = pkg_dict

        data = {
            "version": self.version,
            "packages": packages_dict,
        }

        serialized = yaml.safe_dump(
            data,
            sort_keys=False,
            default_flow_style=False,
        )
        manifest_path.write_text(serialized, encoding="utf-8")


def get_manifest_path(agent_dir: Path) -> Path:
    """Return the canonical manifest path inside a .agent directory."""
    return agent_dir / MANIFEST_FILENAME
