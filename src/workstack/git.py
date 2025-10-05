import subprocess
from pathlib import Path

import click


def get_worktree_branches(repo_root: Path) -> dict[Path, str | None]:
    """Get a mapping of worktree paths to their checked-out branches.

    Returns a dict mapping absolute worktree paths to branch names.
    If a worktree is in a detached HEAD state, the branch value is None.
    """
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    worktrees: dict[Path, str | None] = {}
    current_path: Path | None = None

    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("worktree "):
            current_path = Path(line.split(maxsplit=1)[1])
        elif line.startswith("branch "):
            if current_path is not None:
                # Extract branch name from refs/heads/branch-name
                branch_ref = line.split(maxsplit=1)[1]
                branch_name = branch_ref.replace("refs/heads/", "")
                worktrees[current_path] = branch_name
        elif line == "" and current_path is not None:
            # Empty line separates worktree entries
            # If we haven't set a branch yet, it's detached HEAD
            if current_path not in worktrees:
                worktrees[current_path] = None
            current_path = None

    # Handle the last entry if file doesn't end with blank line
    if current_path is not None and current_path not in worktrees:
        worktrees[current_path] = None

    return worktrees


def detect_default_branch(repo_root: Path) -> str:
    """Detect the default branch (main or master) for the repository.

    Checks for 'main' first, then 'master'. Raises SystemExit if neither exists.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "main"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return "main"

    result = subprocess.run(
        ["git", "rev-parse", "--verify", "master"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return "master"

    click.echo("Error: Could not find 'main' or 'master' branch.", err=True)
    raise SystemExit(1)
