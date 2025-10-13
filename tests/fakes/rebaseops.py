"""Fake rebase operations for testing.

FakeRebaseOps is an in-memory implementation that accepts pre-configured state
in its constructor. Construct instances directly with keyword arguments.
"""

from pathlib import Path
from typing import Any

from workstack.core.rebaseops import RebaseOps


class FakeRebaseOps(RebaseOps):
    """In-memory fake implementation of rebase operations.

    This class has NO public setup methods. All state is provided via constructor
    using keyword arguments with sensible defaults (empty dicts).
    """

    def __init__(
        self,
        *,
        merge_bases: dict[tuple[str, str], str | None] | None = None,
        commit_ranges: dict[tuple[str, str], list[dict[str, str]]] | None = None,
        conflicted_files: dict[Path, list[str]] | None = None,
        rebase_in_progress: dict[Path, bool] | None = None,
        clean_worktrees: dict[Path, bool] | None = None,
    ) -> None:
        """Create FakeRebaseOps with pre-configured state.

        Args:
            merge_bases: Mapping of (branch1, branch2) -> merge base SHA
            commit_ranges: Mapping of (from_ref, to_ref) -> list of commits
            conflicted_files: Mapping of cwd -> list of conflicted file paths
            rebase_in_progress: Mapping of cwd -> whether rebase is in progress
            clean_worktrees: Mapping of cwd -> whether worktree is clean
        """
        self._merge_bases = merge_bases or {}
        self._commit_ranges = commit_ranges or {}
        self._conflicted_files = conflicted_files or {}
        self._rebase_in_progress = rebase_in_progress or {}
        self._clean_worktrees = clean_worktrees or {}

    def start_rebase(
        self,
        cwd: Path,
        onto: str,
        *,
        interactive: bool = False,
    ) -> tuple[bool, list[str]]:
        """Start a rebase (returns pre-configured conflicts if any)."""
        conflicts = self._conflicted_files.get(cwd, [])
        if conflicts:
            self._rebase_in_progress[cwd] = True
            return (False, conflicts)
        return (True, [])

    def continue_rebase(self, cwd: Path) -> tuple[bool, list[str]]:
        """Continue a rebase (returns pre-configured conflicts if any)."""
        conflicts = self._conflicted_files.get(cwd, [])
        if not conflicts:
            self._rebase_in_progress[cwd] = False
            return (True, [])
        return (False, conflicts)

    def abort_rebase(self, cwd: Path) -> None:
        """Abort a rebase (clears in-progress state)."""
        self._rebase_in_progress[cwd] = False

    def get_rebase_status(self, cwd: Path) -> dict[str, Any]:
        """Get rebase status (returns pre-configured state)."""
        in_progress = self._rebase_in_progress.get(cwd, False)
        conflicts = self._conflicted_files.get(cwd, []) if in_progress else []

        return {
            "in_progress": in_progress,
            "onto": "main" if in_progress else None,
            "remaining_commits": 1 if in_progress else 0,
            "current_commit": "1" if in_progress else None,
            "conflicts": conflicts,
        }

    def get_merge_base(self, cwd: Path, branch1: str, branch2: str) -> str | None:
        """Get merge base (returns pre-configured value)."""
        return self._merge_bases.get((branch1, branch2))

    def get_commit_range(
        self,
        cwd: Path,
        from_ref: str,
        to_ref: str,
    ) -> list[dict[str, str]]:
        """Get commit range (returns pre-configured commits)."""
        return self._commit_ranges.get((from_ref, to_ref), [])

    def get_conflicted_files(self, cwd: Path) -> list[str]:
        """Get conflicted files (returns pre-configured list)."""
        return self._conflicted_files.get(cwd, [])

    def check_clean_worktree(self, cwd: Path) -> bool:
        """Check if worktree is clean (returns pre-configured value)."""
        return self._clean_worktrees.get(cwd, True)
