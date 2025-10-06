from dataclasses import dataclass
from pathlib import Path

from workstack.context import WorkstackContext


@dataclass(frozen=True)
class RepoContext:
    """Represents a git repo root and its managed worktrees directory."""

    root: Path
    repo_name: str
    work_dir: Path


def discover_repo_context(ctx: WorkstackContext, start: Path) -> RepoContext:
    """Walk up from `start` to find a directory containing `.git`.

    Returns a RepoContext pointing to the repo root and the global worktrees directory
    for this repository.
    Raises FileNotFoundError if not inside a git repo or if global config is missing.

    Note: Properly handles git worktrees by finding the main repository root,
    not the worktree's .git file.
    """
    cur = start.resolve()

    root: Path | None = None
    git_common_dir = ctx.git_ops.get_git_common_dir(cur)
    if git_common_dir is not None:
        root = git_common_dir.parent.resolve()
    else:
        for parent in [cur, *cur.parents]:
            git_path = parent / ".git"
            if git_path.exists():
                if git_path.is_dir():
                    root = parent
                    break

    if root is None:
        raise FileNotFoundError("Not inside a git repository (no .git found up the tree).")

    repo_name = root.name
    work_dir = ctx.global_config_ops.get_workstacks_root() / repo_name

    return RepoContext(root=root, repo_name=repo_name, work_dir=work_dir)


def ensure_work_dir(repo: RepoContext) -> Path:
    """Ensure the worktrees directory exists and return it."""
    repo.work_dir.mkdir(parents=True, exist_ok=True)
    return repo.work_dir


def worktree_path_for(work_dir: Path, name: str) -> Path:
    """Return the absolute path for a named worktree."""
    return (work_dir / name).resolve()
