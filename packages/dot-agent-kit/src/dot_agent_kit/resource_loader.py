"""Resource management for bundled documentation and tools."""

from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import PurePosixPath


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

    if candidate.is_file() or candidate.is_dir():
        return candidate

    msg = f"Resource not found: {relative_path}"
    raise FileNotFoundError(msg)


def list_available_files() -> list[str]:
    """Return the list of relative resource file paths shipped with the package.

    Returns paths that match the actual package structure on disk.
    """
    root = get_resource_root()
    relative_paths: list[str] = []

    # Scan agentic_programming_guide package
    apg_dir = root.joinpath("agentic_programming_guide")
    if apg_dir.is_dir():
        for entry in apg_dir.iterdir():
            if entry.is_file() and entry.name.endswith(".md"):
                relative_paths.append(f"agentic_programming_guide/{entry.name}")

    # Scan tools packages
    tools_dir = root.joinpath("tools")
    if tools_dir.is_dir():
        for tool_pkg in tools_dir.iterdir():
            if tool_pkg.is_dir():
                for entry in tool_pkg.iterdir():
                    if entry.is_file() and entry.name.endswith(".md"):
                        relative_paths.append(f"tools/{tool_pkg.name}/{entry.name}")

    return sorted(relative_paths)


def read_resource_file(relative_path: str) -> str:
    """Return the text contents of a bundled resource file."""
    resource = _resolve_resource(relative_path)
    if not resource.is_file():
        msg = f"Resource is not a file: {relative_path}"
        raise IsADirectoryError(msg)

    return resource.read_text(encoding="utf-8")
