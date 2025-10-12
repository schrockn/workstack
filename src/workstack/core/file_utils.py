"""File operation utilities."""

import os
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def _is_critical_system_file(path: Path) -> bool:
    """Check if path is a critical system file that should not be modified by tests.

    Returns True for shell rc files in the user's real home directory.
    This is a safety check to prevent tests from accidentally modifying real system files.
    """
    if not path.exists():
        return False

    real_home = Path.home()
    critical_files = {
        real_home / ".bashrc",
        real_home / ".zshrc",
        real_home / ".bash_profile",
        real_home / ".profile",
        real_home / ".config" / "fish" / "config.fish",
    }

    try:
        resolved_path = path.resolve()
        return resolved_path in critical_files
    except (OSError, RuntimeError):
        return False


@contextmanager
def atomic_write(target_path: Path, *, mode: str = "w", encoding: str = "utf-8") -> Iterator:
    """Write to a file atomically using a temporary file and rename.

    This context manager ensures that file writes are atomic - either the entire
    write succeeds or the original file is left untouched. It also preserves
    file permissions from the original file if it exists.

    Args:
        target_path: Final destination path for the file
        mode: File open mode (default "w")
        encoding: File encoding (default "utf-8")

    Yields:
        File handle for writing

    Example:
        with atomic_write(Path("config.txt")) as f:
            f.write("new content")

    Note: Exception handling for cleanup is acceptable here per EXCEPTION_HANDLING.md
    as this is encapsulating necessary exception handling at an error boundary.

    Raises:
        RuntimeError: If attempting to write to a critical system file (safety check)
    """
    target_path = Path(target_path)

    # Safety check: prevent accidental writes to critical system files
    if _is_critical_system_file(target_path):
        raise RuntimeError(
            f"Refusing to write to critical system file: {target_path}. "
            "This is a safety check to prevent accidental modification of shell rc files. "
            "If you're writing a test, use a temporary directory instead of Path.home()."
        )

    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory to ensure same filesystem
    temp_fd, temp_path = tempfile.mkstemp(
        dir=target_path.parent, prefix=f".{target_path.name}.", suffix=".tmp"
    )

    try:
        with os.fdopen(temp_fd, mode, encoding=encoding) as f:
            yield f

        # Preserve permissions from original file if it exists
        if target_path.exists():
            shutil.copystat(target_path, temp_path)

        # Atomic rename
        os.rename(temp_path, target_path)

    except OSError:
        # Clean up temp file on error - acceptable use of exception handling
        # per EXCEPTION_HANDLING.md (cleanup during error boundaries)
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass  # File was never created if mkstemp failed
        raise


def extract_plan_title(plan_path: Path) -> str | None:
    """Extract the first heading from a markdown plan file.

    Uses python-frontmatter library to properly parse YAML frontmatter,
    then extracts the first line starting with # from the content.

    Args:
        plan_path: Path to the .PLAN.md file

    Returns:
        The heading text (without the # prefix), or None if not found or file doesn't exist
    """
    if not plan_path.exists():
        return None

    import frontmatter

    # Parse file with frontmatter library (handles YAML frontmatter properly)
    post = frontmatter.load(str(plan_path))

    # Get the content (without frontmatter)
    content = post.content
    lines = content.splitlines()

    # Find first heading
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            # Remove all # symbols and strip whitespace
            title = stripped.lstrip("#").strip()
            if title:
                return title

    return None
