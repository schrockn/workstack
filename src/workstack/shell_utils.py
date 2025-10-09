"""Utilities for generating shell integration scripts."""

from pathlib import Path


def render_cd_script(path: Path, *, comment: str, success_message: str) -> str:
    """Generate shell script to change directory with feedback.

    Args:
        path: Target directory path to cd into.
        comment: Shell comment describing the operation.
        success_message: Message to echo after successful cd.

    Returns:
        Shell script that changes directory and shows success message.
    """
    path_str = str(path)
    quoted_path = "'" + path_str.replace("'", "'\\''") + "'"
    lines = [
        f"# {comment}",
        f"cd {quoted_path}",
        f'echo "{success_message}"',
    ]
    return "\n".join(lines) + "\n"
