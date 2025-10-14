from dataclasses import dataclass
from pathlib import Path

import click

from workstack.core.context import WorkstackContext


@dataclass(frozen=True)
class RepoContext:
    """Represents a git repo root and its managed worktrees directory."""

    root: Path
    repo_name: str
    workstacks_dir: Path


def discover_repo_context(ctx: WorkstackContext, start: Path) -> RepoContext:
    """Walk up from `start` to find a directory containing `.git`.

    Returns a RepoContext pointing to the repo root and the global worktrees directory
    for this repository.
    Raises FileNotFoundError if not inside a git repo or if global config is missing.

    Note: Properly handles git worktrees by finding the main repository root,
    not the worktree's .git file.
    """
    if not start.exists():
        raise FileNotFoundError(f"Start path '{start}' does not exist.")

    cur = start.resolve()

    root: Path | None = None
    git_common_dir = ctx.git_ops.get_git_common_dir(cur)
    if git_common_dir is not None:
        root = git_common_dir.parent.resolve()
    else:
        for parent in [cur, *cur.parents]:
            git_path = parent / ".git"
            if not git_path.exists():
                continue

            if git_path.is_dir():
                root = parent
                break

    if root is None:
        raise FileNotFoundError("Not inside a git repository (no .git found up the tree).")

    repo_name = root.name
    workstacks_dir = ctx.global_config_ops.get_workstacks_root() / repo_name

    return RepoContext(root=root, repo_name=repo_name, workstacks_dir=workstacks_dir)


def ensure_workstacks_dir(repo: RepoContext) -> Path:
    """Ensure the workstacks directory exists and return it."""
    repo.workstacks_dir.mkdir(parents=True, exist_ok=True)
    return repo.workstacks_dir


def worktree_path_for(workstacks_dir: Path, name: str) -> Path:
    """Return the absolute path for a named worktree within workstacks_dir.

    Note: Does not handle 'root' as a special case. Commands that support
    'root' must check for it explicitly and use repo.root directly.

    Args:
        workstacks_dir: The directory containing all workstacks for this repo
        name: The worktree name (e.g., 'feature-a')

    Returns:
        Absolute path to the worktree (e.g., ~/worktrees/myrepo/feature-a/)
    """
    return (workstacks_dir / name).resolve()


def validate_worktree_name_for_removal(name: str) -> None:
    """Validate that a worktree name is safe for removal.

    Rejects:
    - Empty strings
    - `.` or `..` (current/parent directory references)
    - `root` (explicit root worktree name)
    - Names starting with `/` (absolute paths)
    - Names containing `/` (path separators)

    Raises SystemExit(1) with error message if validation fails.
    """
    if not name or not name.strip():
        click.echo("Error: Worktree name cannot be empty", err=True)
        raise SystemExit(1)

    if name in (".", ".."):
        click.echo(f"Error: Cannot remove '{name}' - directory references not allowed", err=True)
        raise SystemExit(1)

    if name == "root":
        click.echo("Error: Cannot remove 'root' - root worktree name not allowed", err=True)
        raise SystemExit(1)

    if name.startswith("/"):
        click.echo(f"Error: Cannot remove '{name}' - absolute paths not allowed", err=True)
        raise SystemExit(1)

    if "/" in name:
        click.echo(f"Error: Cannot remove '{name}' - path separators not allowed", err=True)
        raise SystemExit(1)
