"""Utilities for Python package introspection and management."""

import importlib.metadata
import importlib.util
from pathlib import Path


def is_package_installed(package_name: str) -> bool:
    """Check if a Python package is installed."""
    try:
        importlib.metadata.version(package_name)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


def get_package_version(package_name: str) -> str | None:
    """Get the installed version of a package."""
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def get_package_path(package_name: str) -> Path | None:
    """Get the installation path of a package."""
    try:
        spec = importlib.util.find_spec(package_name.replace("-", "_"))
        if spec and spec.origin:
            return Path(spec.origin).parent
    except (ImportError, ValueError):
        pass

    # Fallback: check distribution files for traditional packages or data-only packages
    try:
        dist = importlib.metadata.distribution(package_name)
        if dist.files:
            # First, try to find __init__.py (traditional packages)
            for file in dist.files:
                if file.name == "__init__.py":
                    return Path(file.locate()).parent

            # Second, try to find kit.yaml (data-only packages like dev-runners-da-kit)
            for file in dist.files:
                if file.name == "kit.yaml" or file.name.endswith("/kit.yaml"):
                    located = Path(file.locate())
                    if located.exists():
                        return located.parent
    except importlib.metadata.PackageNotFoundError:
        pass

    return None


def get_package_metadata(package_name: str) -> dict | None:
    """Get metadata for an installed package."""
    try:
        dist = importlib.metadata.distribution(package_name)
        return {
            "name": dist.name,
            "version": dist.version,
            "summary": dist.metadata.get("Summary"),
            "home_page": dist.metadata.get("Home-Page"),
        }
    except importlib.metadata.PackageNotFoundError:
        return None
