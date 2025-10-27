import logging
import tomllib
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PackageLayout:
    """Describes the layout of a Python package with separate src and test directories."""

    source_dirs: list[Path]
    test_dirs: list[Path]


def detect_package_root(path: Path) -> PackageLayout | None:
    """
    Detect if path is a Python package root by checking for pyproject.toml.

    Parses pyproject.toml to find source and test directories from:
    - tool.setuptools.packages.find.where (source directories)
    - tool.pytest.ini_options.testpaths (test directories)

    Falls back to ["src"] and ["tests"] if not specified.

    Returns None if no pyproject.toml exists or if neither src nor tests dirs exist.
    """
    pyproject_path = path / "pyproject.toml"

    if not pyproject_path.exists():
        return None

    try:
        content = pyproject_path.read_text(encoding="utf-8")
        config = tomllib.loads(content)
    except Exception as e:
        logger.debug(f"Failed to parse pyproject.toml at {pyproject_path}: {e}")
        return None

    # Extract source directories
    source_dir_names = _extract_source_dirs(config)
    test_dir_names = _extract_test_dirs(config)

    # Resolve to absolute paths and filter to existing directories
    source_dirs = _resolve_dirs(path, source_dir_names)
    test_dirs = _resolve_dirs(path, test_dir_names)

    # Only return PackageLayout if at least one directory exists
    if not source_dirs and not test_dirs:
        return None

    return PackageLayout(source_dirs=source_dirs, test_dirs=test_dirs)


def _extract_source_dirs(config: dict) -> list[str]:
    """
    Extract source directories from pyproject.toml config.

    Checks tool.setuptools.packages.find.where, defaults to ["src"].
    """
    try:
        where = (
            config.get("tool", {})
            .get("setuptools", {})
            .get("packages", {})
            .get("find", {})
            .get("where")
        )
        if where and isinstance(where, list):
            return where
    except (KeyError, TypeError):
        pass

    # Default to src/
    return ["src"]


def _extract_test_dirs(config: dict) -> list[str]:
    """
    Extract test directories from pyproject.toml config.

    Checks tool.pytest.ini_options.testpaths, defaults to ["tests"].
    """
    try:
        testpaths = config.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("testpaths")
        if testpaths and isinstance(testpaths, list):
            return testpaths
    except (KeyError, TypeError):
        pass

    # Default to tests/
    return ["tests"]


def _resolve_dirs(base_path: Path, dir_names: list[str]) -> list[Path]:
    """
    Resolve directory names relative to base path.

    Returns only directories that exist.
    """
    resolved = []
    for dir_name in dir_names:
        dir_path = base_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            resolved.append(dir_path)
    return resolved


def discover_python_packages(root: Path) -> list[Path]:
    """
    Recursively discover all Python packages (directories with __init__.py) under root.

    Returns paths in depth-first order (deepest packages first).
    """
    packages = []

    if not root.exists() or not root.is_dir():
        return packages

    # Find all __init__.py files recursively
    init_files = sorted(root.rglob("__init__.py"))

    for init_file in init_files:
        package_dir = init_file.parent

        # Skip __pycache__ and other special directories
        if "__pycache__" in package_dir.parts:
            continue

        # Skip .egg-info directories
        if any(part.endswith(".egg-info") for part in package_dir.parts):
            continue

        packages.append(package_dir)

    # Sort by depth (deepest first)
    packages.sort(key=lambda p: len(p.parts), reverse=True)

    return packages
