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
    """Resolve a relative path inside the bundled resources.

    Handles both old flat paths (e.g., "AGENTIC_PROGRAMMING.md", "tools/gt.md")
    and new package paths (e.g., "agentic_programming_guide/AGENTIC_PROGRAMMING.md").
    """
    normalized = PurePosixPath(relative_path.strip("/"))
    if normalized.is_absolute() or ".." in normalized.parts or not normalized.parts:
        msg = f"Resource path escapes package resources: {relative_path}"
        raise ValueError(msg)

    root = get_resource_root()

    # Try direct path first (new package structure)
    candidate = root.joinpath(str(normalized))
    if candidate.is_file() or candidate.is_dir():
        return candidate

    # Handle old flat paths for backwards compatibility
    if relative_path.startswith("tools/"):
        # Convert "tools/gt.md" to "tools/gt/gt.md"
        tool_file = relative_path[6:]  # Remove "tools/"
        tool_name = tool_file.replace(".md", "")
        package_path = f"tools/{tool_name}/{tool_file}"
        candidate = root.joinpath(package_path)
        if candidate.is_file():
            return candidate
    elif "/" not in relative_path and relative_path.endswith(".md"):
        # Convert "AGENTIC_PROGRAMMING.md" to "agentic_programming_guide/AGENTIC_PROGRAMMING.md"
        candidate = root.joinpath(f"agentic_programming_guide/{relative_path}")
        if candidate.is_file():
            return candidate

    msg = f"Resource not found: {relative_path}"
    raise FileNotFoundError(msg)


def list_available_files() -> list[str]:
    """Return the list of relative resource file paths shipped with the package.

    This function returns paths in the old flat format for backwards compatibility,
    but reads from the new package structure.
    """
    root = get_resource_root()
    relative_paths: list[str] = []

    # Scan agentic_programming_guide package
    apg_dir = root.joinpath("agentic_programming_guide")
    if apg_dir.is_dir():
        for entry in apg_dir.iterdir():
            if entry.is_file() and entry.name.endswith(".md"):
                relative_paths.append(entry.name)

    # Scan tools packages
    tools_dir = root.joinpath("tools")
    if tools_dir.is_dir():
        for tool_pkg in tools_dir.iterdir():
            if tool_pkg.is_dir():
                for entry in tool_pkg.iterdir():
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
