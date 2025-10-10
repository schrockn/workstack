"""Shared utilities for dev CLI framework."""

from pathlib import Path


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def is_valid_command_name(name: str) -> bool:
    """Check if a string is a valid command name.

    Args:
        name: Command name to validate

    Returns:
        True if valid command name (lowercase, hyphens, alphanumeric)
    """
    if not name:
        return False

    # Must be lowercase alphanumeric with hyphens
    if not all(c.isalnum() or c == "-" for c in name):
        return False

    # Cannot have uppercase letters
    if name != name.lower():
        return False

    # Cannot start or end with hyphen
    if name.startswith("-") or name.endswith("-"):
        return False

    return True
