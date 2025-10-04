import json
import subprocess
from pathlib import Path

import click


def add_worktree(
    repo_root: Path,
    path: Path,
    *,
    branch: str | None,
    ref: str | None,
    use_existing_branch: bool = False,
    use_graphite: bool = False,
) -> None:
    """Create a git worktree.

    If `use_existing_branch` is True and `branch` is provided, checks out the existing branch
    in the new worktree: `git worktree add <path> <branch>`.

    If `use_existing_branch` is False and `branch` is provided, creates a new branch:
    - With graphite: `gt create <branch>` followed by `git worktree add <path> <branch>`
    - Without graphite: `git worktree add -b <branch> <path> <ref or HEAD>`

    Otherwise, uses `git worktree add <path> <ref or HEAD>`.
    """

    if branch and use_existing_branch:
        # Check out an existing branch in the new worktree
        cmd = ["git", "worktree", "add", str(path), branch]
        subprocess.run(cmd, cwd=repo_root, check=True)
    elif branch:
        # Create a new branch in the new worktree
        if use_graphite:
            # Use Graphite to create the branch (creates it in a stack)
            base_ref = ref or "HEAD"
            # First, create the branch with Graphite
            subprocess.run(["gt", "create", branch, "--onto", base_ref], cwd=repo_root, check=True)
            # Then add the worktree pointing to that branch
            subprocess.run(["git", "worktree", "add", str(path), branch], cwd=repo_root, check=True)
        else:
            # Use standard git to create the branch
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
            subprocess.run(cmd, cwd=repo_root, check=True)
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


def get_current_branch(cwd: Path) -> str:
    """Get the name of the current branch.

    Raises subprocess.CalledProcessError if HEAD is detached or not in a git repo.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    branch = result.stdout.strip()
    if branch == "HEAD":
        raise ValueError("HEAD is detached (not on a branch)")
    return branch


def checkout_branch(repo_root: Path, branch: str) -> None:
    """Checkout a branch in the current worktree.

    Runs `git checkout <branch>`.
    """
    subprocess.run(["git", "checkout", branch], cwd=repo_root, check=True)


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


def get_pr_status(
    repo_root: Path, branch: str, debug: bool = False
) -> tuple[str | None, int | None, str | None]:
    """Get PR status for a branch using GitHub CLI.

    Returns tuple of (state, pr_number, title) where:
    - state is "MERGED", "CLOSED", "OPEN", or None if no PR found
    - pr_number is the PR number or None
    - title is the PR title or None

    Returns (None, None, None) if gh CLI is not installed or not authenticated.

    Note: Uses try/except as an acceptable error boundary for handling gh CLI
    availability and authentication. We cannot reliably check gh installation
    and authentication status a priori without duplicating gh's logic.
    """

    def debug_print(msg: str) -> None:
        if debug:
            click.echo(click.style(msg, fg="bright_black"))

    try:
        # Check merged PRs first
        for state in ["merged", "closed", "open"]:
            cmd = [
                "gh",
                "pr",
                "list",
                "--state",
                state,
                "--head",
                branch,
                "--json",
                "state,number,title",
            ]

            debug_print(f"  $ {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            prs = json.loads(result.stdout)
            if prs:
                # Take the first PR (should only be one per branch)
                pr = prs[0]
                return pr.get("state"), pr.get("number"), pr.get("title")

        return None, None, None

    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        # gh not installed, not authenticated, or JSON parsing failed
        return None, None, None
