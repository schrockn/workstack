from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .config import LoadedConfig


@dataclass(frozen=True)
class RepoContext:
    """Represents a git repo root and its managed `.workstack` directory."""

    root: Path
    work_dir: Path


def discover_repo_context(start: Path) -> RepoContext:
    """Walk up from `start` to find a directory containing `.git`.

    Returns a RepoContext pointing to the repo root and the `.workstack` directory.
    Raises FileNotFoundError if not inside a git repo.

    Note: Properly handles git worktrees by finding the main repository root,
    not the worktree's .git file.
    """
    import subprocess

    cur = start.resolve()

    # Use git to find the true repository root (handles worktrees correctly)
    try:
        # Get the common git directory (points to main repo even from worktrees)
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=cur,
            capture_output=True,
            text=True,
            check=True,
        )
        git_common_dir = Path(result.stdout.strip())
        # The parent of .git is the repo root
        root = git_common_dir.parent.resolve()
        work_dir = root / ".workstack"
        return RepoContext(root=root, work_dir=work_dir)
    except subprocess.CalledProcessError:
        # Fallback to walking up the tree
        for parent in [cur, *cur.parents]:
            git_path = parent / ".git"
            if git_path.exists():
                # Only accept if .git is a directory (not a worktree .git file)
                if git_path.is_dir():
                    work_dir = parent / ".workstack"
                    return RepoContext(root=parent, work_dir=work_dir)
        raise FileNotFoundError("Not inside a git repository (no .git found up the tree).")


def ensure_work_dir(repo: RepoContext) -> Path:
    """Ensure `.workstack` exists and return it."""
    repo.work_dir.mkdir(exist_ok=True)
    return repo.work_dir


def worktree_path_for(work_dir: Path, name: str) -> Path:
    """Return the absolute path for a named worktree under `.workstack`."""
    return (work_dir / name).resolve()


def make_env_content(cfg: LoadedConfig, *, worktree_path: Path, repo_root: Path, name: str) -> str:
    """Render .env content using config templates.

    Substitution variables:
      - {worktree_path}
      - {repo_root}
      - {name}
    """

    variables: Mapping[str, str] = {
        "worktree_path": str(worktree_path),
        "repo_root": str(repo_root),
        "name": name,
    }

    lines: list[str] = []
    for key, template in cfg.env.items():
        value = template.format(**variables)
        # Quote value to be safe; dotenv parsers commonly accept quotes.
        lines.append(f"{key}={quote_env_value(value)}")

    # Always include these basics for convenience
    lines.append(f"WORKTREE_PATH={quote_env_value(str(worktree_path))}")
    lines.append(f"REPO_ROOT={quote_env_value(str(repo_root))}")
    lines.append(f"WORKTREE_NAME={quote_env_value(name)}")

    return "\n".join(lines) + "\n"


def quote_env_value(value: str) -> str:
    """Return a quoted value suitable for .env files."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
