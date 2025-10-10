"""File operation utilities."""

import os
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


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
    """
    target_path = Path(target_path)
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
