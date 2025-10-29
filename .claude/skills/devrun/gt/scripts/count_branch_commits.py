#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Count commits in current branch that aren't in parent branch.

This script uses Graphite (gt) to find the parent branch, then counts
commits between parent and HEAD using git rev-list.

Usage:
    uv run count_branch_commits.py [directory]

Arguments:
    directory: Optional path to git repository (defaults to current directory)

Output:
    Single integer representing the number of commits in current branch
    that don't exist in the parent branch.

Exit Codes:
    0: Success
    1: Error (git/gt command failed)

Examples:
    $ uv run count_branch_commits.py
    3

    $ uv run count_branch_commits.py /path/to/repo
    1
"""
import subprocess
import sys
from pathlib import Path


def count_branch_commits(cwd: Path) -> int:
    """Count commits between parent branch and HEAD.

    Args:
        cwd: Directory containing git repository

    Returns:
        Number of commits in current branch not in parent

    Raises:
        subprocess.CalledProcessError: If git or gt command fails
    """
    # Get parent branch using Graphite
    result = subprocess.run(
        ["gt", "parent"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    parent = result.stdout.strip()

    # Count commits: current branch not in parent
    # Format: parent..HEAD means "commits reachable from HEAD but not from parent"
    result = subprocess.run(
        ["git", "rev-list", "--count", f"{parent}..HEAD"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return int(result.stdout.strip())


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse arguments
    cwd = Path.cwd() if len(sys.argv) < 2 else Path(sys.argv[1])

    try:
        count = count_branch_commits(cwd)
        print(count)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
