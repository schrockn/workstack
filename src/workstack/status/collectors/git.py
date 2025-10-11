"""Git status collector."""

import subprocess
from pathlib import Path

from workstack.core.context import WorkstackContext
from workstack.status.collectors.base import StatusCollector
from workstack.status.models.status_data import CommitInfo, GitStatus


class GitStatusCollector(StatusCollector):
    """Collects git repository status information."""

    @property
    def name(self) -> str:
        """Name identifier for this collector."""
        return "git"

    def is_available(self, ctx: WorkstackContext, worktree_path: Path) -> bool:
        """Check if git operations are available.

        Args:
            ctx: Workstack context
            worktree_path: Path to worktree

        Returns:
            True if worktree exists and has git
        """
        if not worktree_path.exists():
            return False

        return True

    def collect(
        self, ctx: WorkstackContext, worktree_path: Path, repo_root: Path
    ) -> GitStatus | None:
        """Collect git status information.

        Args:
            ctx: Workstack context
            worktree_path: Path to worktree
            repo_root: Repository root path

        Returns:
            GitStatus with repository information or None if collection fails
        """
        branch = ctx.git_ops.get_current_branch(worktree_path)
        if branch is None:
            return None

        # Get git status
        staged, modified, untracked = self._get_file_status(worktree_path)
        clean = len(staged) == 0 and len(modified) == 0 and len(untracked) == 0

        # Get ahead/behind counts
        ahead, behind = self._get_ahead_behind(worktree_path, branch)

        # Get recent commits
        recent_commits = self._get_recent_commits(worktree_path, limit=5)

        return GitStatus(
            branch=branch,
            clean=clean,
            ahead=ahead,
            behind=behind,
            staged_files=staged,
            modified_files=modified,
            untracked_files=untracked,
            recent_commits=recent_commits,
        )

    def _get_file_status(self, cwd: Path) -> tuple[list[str], list[str], list[str]]:
        """Get lists of staged, modified, and untracked files.

        Args:
            cwd: Working directory

        Returns:
            Tuple of (staged, modified, untracked) file lists
        """
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )

        staged = []
        modified = []
        untracked = []

        for line in result.stdout.splitlines():
            if not line:
                continue

            status_code = line[:2]
            filename = line[3:]

            # Check if file is staged (first character is not space)
            if status_code[0] != " " and status_code[0] != "?":
                staged.append(filename)

            # Check if file is modified (second character is not space)
            if status_code[1] != " " and status_code[1] != "?":
                modified.append(filename)

            # Check if file is untracked
            if status_code == "??":
                untracked.append(filename)

        return staged, modified, untracked

    def _get_ahead_behind(self, cwd: Path, branch: str) -> tuple[int, int]:
        """Get number of commits ahead and behind tracking branch.

        Args:
            cwd: Working directory
            branch: Current branch name

        Returns:
            Tuple of (ahead, behind) counts
        """
        # Check if branch has upstream
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            # No upstream branch
            return 0, 0

        upstream = result.stdout.strip()

        # Get ahead/behind counts
        result = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", f"{upstream}...HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )

        parts = result.stdout.strip().split()
        if len(parts) == 2:
            behind = int(parts[0])
            ahead = int(parts[1])
            return ahead, behind

        return 0, 0

    def _get_recent_commits(self, cwd: Path, *, limit: int = 5) -> list[CommitInfo]:
        """Get recent commit information.

        Args:
            cwd: Working directory
            limit: Maximum number of commits to retrieve

        Returns:
            List of recent commits
        """
        result = subprocess.run(
            [
                "git",
                "log",
                f"-{limit}",
                "--format=%H%x00%s%x00%an%x00%ar",
            ],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("\x00")
            if len(parts) == 4:
                commits.append(
                    CommitInfo(
                        sha=parts[0][:7],  # Short SHA
                        message=parts[1],
                        author=parts[2],
                        date=parts[3],
                    )
                )

        return commits
