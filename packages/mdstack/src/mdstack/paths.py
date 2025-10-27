from pathlib import Path


def find_repo_root(start_path: Path) -> Path | None:
    """
    Find repository root by walking up until .git is found.

    Returns None if no repository root is found.
    """
    current = start_path.resolve()

    # Walk up directory tree looking for .git
    while current != current.parent:
        git_dir = current / ".git"
        if git_dir.exists():
            return current
        current = current.parent

    return None


def make_repo_relative(file_path: Path, repo_root: Path | None = None) -> str:
    """
    Convert absolute path to repository-relative path.

    If repo_root is not provided, attempts to find it from file_path.
    Falls back to just the filename if repo root cannot be determined.
    """
    if repo_root is None:
        repo_root = find_repo_root(file_path)

    if repo_root is None:
        # Fall back to filename only
        return file_path.name

    try:
        # Make path relative to repo root
        relative = file_path.resolve().relative_to(repo_root)
        return str(relative)
    except ValueError:
        # Path is not relative to repo_root, fall back to filename
        return file_path.name


def make_scope_relative(file_path: Path, scope_path: Path) -> str:
    """
    Convert absolute path to scope-relative path.

    Makes paths relative to the scope being documented rather than the repository root.
    This creates more intuitive documentation where paths are relative to the context.

    Args:
        file_path: The file path to make relative
        scope_path: The scope directory path to make relative to

    Returns:
        Path relative to scope, or just filename if path is not under scope
    """
    try:
        # Make path relative to scope
        relative = file_path.resolve().relative_to(scope_path.resolve())
        return str(relative)
    except ValueError:
        # Path is not relative to scope_path, fall back to filename
        return file_path.name
