from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


def add_worktree(repo_root: Path, path: Path, *, branch: Optional[str], ref: Optional[str]) -> None:
    """Create a git worktree.

    If `branch` is provided, uses `git worktree add -b <branch> <path> <ref or HEAD>`.
    Otherwise, uses `git worktree add <path> <ref or HEAD>`.
    """

    if branch:
        base_ref = ref or "HEAD"
        cmd = [
            "git",
            "worktree",
            "add",
            "-b",
            branch,
            str(path),
            base_ref,
        ]
    else:
        base_ref = ref or "HEAD"
        cmd = ["git", "worktree", "add", str(path), base_ref]

    subprocess.run(cmd, cwd=repo_root, check=True)


def remove_worktree(repo_root: Path, path: Path, *, force: bool) -> None:
    """Remove a git worktree from the repository metadata.

    Runs `git worktree remove [--force] <path>`. This may fail if the worktree has
    uncommitted changes unless `force=True`.
    """

    cmd = ["git", "worktree", "remove"]
    if force:
        cmd.append("--force")
    cmd.append(str(path))
    subprocess.run(cmd, cwd=repo_root, check=True)
