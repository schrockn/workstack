from importlib import metadata
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import PurePosixPath

PACKAGE_NAME = "dot-agent-kit"
DEFAULT_VERSION = "0.1.0"

# Exception handling acceptable here: metadata.version() provides no LBYL alternative.
# This catches cases where the package is run from source without being installed.
try:
    __version__ = metadata.version(PACKAGE_NAME)
except metadata.PackageNotFoundError:
    __version__ = DEFAULT_VERSION


def get_resource_root() -> Traversable:
    """Return the traversable root for bundled resources."""
    return files("dot_agent_kit.resources")


def _resolve_resource(relative_path: str) -> Traversable:
    """Resolve a relative path inside the bundled resources."""
    normalized = PurePosixPath(relative_path.strip("/"))
    if normalized.is_absolute() or ".." in normalized.parts or not normalized.parts:
        msg = f"Resource path escapes package resources: {relative_path}"
        raise ValueError(msg)

    root = get_resource_root()
    candidate = root.joinpath(str(normalized))
    if not (candidate.is_file() or candidate.is_dir()):
        msg = f"Resource not found: {relative_path}"
        raise FileNotFoundError(msg)

    return candidate


def list_available_files() -> list[str]:
    """Return the list of relative resource file paths shipped with the package."""
    root = get_resource_root()
    relative_paths: list[str] = []

    # Add root-level markdown files
    for entry in root.iterdir():
        if entry.is_file() and entry.name.endswith(".md"):
            relative_paths.append(entry.name)

    # Add files from tools directory
    tools_dir = root.joinpath("tools")
    if tools_dir.is_dir():
        for entry in tools_dir.iterdir():
            if entry.is_file() and entry.name.endswith(".md"):
                relative_paths.append(f"tools/{entry.name}")

    return sorted(relative_paths)


def read_resource_file(relative_path: str) -> str:
    """Return the text contents of a bundled resource file."""
    resource = _resolve_resource(relative_path)
    if not resource.is_file():
        msg = f"Resource is not a file: {relative_path}"
        raise IsADirectoryError(msg)

    return resource.read_text(encoding="utf-8")
