"""Rebase operations interface.

This module provides abstractions for rebase-specific git operations,
separated from general git operations to support complex features like
sandbox rebases.

Architecture:
- RebaseOps: Abstract base class defining the rebase interface
- RealRebaseOps: Production implementation using subprocess
- SandboxRebaseOps: Future decorator for safe sandbox rebasing
"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

# ============================================================================
# Abstract Interface
# ============================================================================


class RebaseOps(ABC):
    """Abstract interface for rebase operations.

    All implementations (real and fake) must implement this interface.
    This interface contains ONLY rebase-related operations.
    """

    @abstractmethod
    def start_rebase(
        self,
        cwd: Path,
        onto: str,
        *,
        interactive: bool = False,
    ) -> tuple[bool, list[str]]:
        """Start a rebase onto the given branch.

        Args:
            cwd: Directory to run rebase in
            onto: Branch/commit to rebase onto
            interactive: Whether to use interactive rebase

        Returns:
            Tuple of (success, list of conflicted files)
            - success: True if rebase completed without conflicts
            - conflicts: List of file paths with conflicts (empty if success=True)
        """
        ...

    @abstractmethod
    def continue_rebase(self, cwd: Path) -> tuple[bool, list[str]]:
        """Continue a rebase after resolving conflicts.

        Args:
            cwd: Directory with rebase in progress

        Returns:
            Tuple of (success, list of conflicted files)
            - success: True if rebase completed
            - conflicts: List of remaining conflicted files (empty if success=True)
        """
        ...

    @abstractmethod
    def abort_rebase(self, cwd: Path) -> None:
        """Abort an ongoing rebase.

        Args:
            cwd: Directory with rebase in progress
        """
        ...

    @abstractmethod
    def get_rebase_status(self, cwd: Path) -> dict[str, Any]:
        """Get detailed rebase status.

        Args:
            cwd: Directory to check

        Returns:
            Dictionary with keys:
            - in_progress: bool - Whether rebase is active
            - onto: str | None - Branch being rebased onto
            - remaining_commits: int - Commits left to apply
            - current_commit: str | None - Currently applying commit
            - conflicts: list[str] - List of conflicted files
        """
        ...

    @abstractmethod
    def get_merge_base(self, cwd: Path, branch1: str, branch2: str) -> str | None:
        """Find the merge base commit between two branches.

        Args:
            cwd: Repository directory
            branch1: First branch name
            branch2: Second branch name

        Returns:
            Commit SHA of merge base, or None if no common ancestor
        """
        ...

    @abstractmethod
    def get_commit_range(
        self,
        cwd: Path,
        from_ref: str,
        to_ref: str,
    ) -> list[dict[str, str]]:
        """Get list of commits between two refs.

        Args:
            cwd: Repository directory
            from_ref: Starting ref (exclusive)
            to_ref: Ending ref (inclusive)

        Returns:
            List of commit dicts with keys:
            - sha: str - Commit SHA
            - message: str - Commit message (first line)
            - author: str - Commit author
        """
        ...

    @abstractmethod
    def get_conflicted_files(self, cwd: Path) -> list[str]:
        """Get list of files with merge conflicts.

        Args:
            cwd: Repository directory

        Returns:
            List of file paths with conflicts
        """
        ...

    @abstractmethod
    def check_clean_worktree(self, cwd: Path) -> bool:
        """Check if worktree has no uncommitted changes.

        Args:
            cwd: Directory to check

        Returns:
            True if worktree is clean (no uncommitted changes)
        """
        ...


# ============================================================================
# Production Implementation
# ============================================================================


class RealRebaseOps(RebaseOps):
    """Production implementation using subprocess.

    All rebase operations execute actual git commands via subprocess.
    """

    def start_rebase(
        self,
        cwd: Path,
        onto: str,
        *,
        interactive: bool = False,
    ) -> tuple[bool, list[str]]:
        """Start a rebase onto the given branch."""
        cmd = ["git", "rebase"]
        if interactive:
            cmd.append("-i")
        cmd.append(onto)

        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return (True, [])

        conflicts = self.get_conflicted_files(cwd)
        return (False, conflicts)

    def continue_rebase(self, cwd: Path) -> tuple[bool, list[str]]:
        """Continue a rebase after resolving conflicts."""
        result = subprocess.run(
            ["git", "rebase", "--continue"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return (True, [])

        conflicts = self.get_conflicted_files(cwd)
        return (False, conflicts)

    def abort_rebase(self, cwd: Path) -> None:
        """Abort an ongoing rebase."""
        subprocess.run(
            ["git", "rebase", "--abort"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )

    def get_rebase_status(self, cwd: Path) -> dict[str, Any]:
        """Get detailed rebase status."""
        git_dir = cwd / ".git"
        rebase_merge = git_dir / "rebase-merge"
        rebase_apply = git_dir / "rebase-apply"

        if rebase_merge.exists():
            msgnum_file = rebase_merge / "msgnum"
            end_file = rebase_merge / "end"
            onto_file = rebase_merge / "onto"

            current_num = (
                int(msgnum_file.read_text(encoding="utf-8").strip()) if msgnum_file.exists() else 0
            )
            total = int(end_file.read_text(encoding="utf-8").strip()) if end_file.exists() else 0
            onto = onto_file.read_text(encoding="utf-8").strip() if onto_file.exists() else None

            return {
                "in_progress": True,
                "onto": onto,
                "remaining_commits": total - current_num,
                "current_commit": str(current_num),
                "conflicts": self.get_conflicted_files(cwd),
            }

        if rebase_apply.exists():
            return {
                "in_progress": True,
                "onto": None,
                "remaining_commits": 0,
                "current_commit": None,
                "conflicts": self.get_conflicted_files(cwd),
            }

        return {
            "in_progress": False,
            "onto": None,
            "remaining_commits": 0,
            "current_commit": None,
            "conflicts": [],
        }

    def get_merge_base(self, cwd: Path, branch1: str, branch2: str) -> str | None:
        """Find the merge base commit between two branches."""
        result = subprocess.run(
            ["git", "merge-base", branch1, branch2],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return None

        return result.stdout.strip()

    def get_commit_range(
        self,
        cwd: Path,
        from_ref: str,
        to_ref: str,
    ) -> list[dict[str, str]]:
        """Get list of commits between two refs."""
        result = subprocess.run(
            [
                "git",
                "log",
                "--format=%H|%s|%an",
                f"{from_ref}..{to_ref}",
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
            sha, message, author = line.split("|", 2)
            commits.append(
                {
                    "sha": sha,
                    "message": message,
                    "author": author,
                }
            )

        return commits

    def get_conflicted_files(self, cwd: Path) -> list[str]:
        """Get list of files with merge conflicts."""
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return []

        return [f.strip() for f in result.stdout.split("\n") if f.strip()]

    def check_clean_worktree(self, cwd: Path) -> bool:
        """Check if worktree has no uncommitted changes."""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )

        return len(result.stdout.strip()) == 0
