from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .config import LoadedConfig


@dataclass(frozen=True)
class RepoContext:
    """Represents a git repo root and its managed `.work` directory."""

    root: Path
    work_dir: Path


def discover_repo_context(start: Path) -> RepoContext:
    """Walk up from `start` to find a directory containing `.git`.

    Returns a RepoContext pointing to the repo root and the `.work` directory.
    Raises FileNotFoundError if not inside a git repo.
    """

    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / ".git").exists():
            work_dir = parent / ".work"
            return RepoContext(root=parent, work_dir=work_dir)
    raise FileNotFoundError("Not inside a git repository (no .git found up the tree).")


def ensure_work_dir(repo: RepoContext) -> Path:
    """Ensure `.work` exists and return it."""
    repo.work_dir.mkdir(exist_ok=True)
    return repo.work_dir


def worktree_path_for(work_dir: Path, name: str) -> Path:
    """Return the absolute path for a named worktree under `.work`."""
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
