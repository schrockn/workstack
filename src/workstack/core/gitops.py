"""High-level git operations interface.

This module provides a clean abstraction over git subprocess calls, making the
codebase more testable and maintainable.

Architecture:
- GitOps: Abstract base class defining the interface
- RealGitOps: Production implementation using subprocess
- Standalone functions: Convenience wrappers delegating to module singleton
"""

import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click

from workstack.core.rebaseops import RealRebaseOps, RebaseOps


@dataclass(frozen=True)
class WorktreeInfo:
    """Information about a single git worktree."""

    path: Path
    branch: str | None


# ============================================================================
# Abstract Interface
# ============================================================================


class GitOps(ABC):
    """Abstract interface for git operations.

    All implementations (real and fake) must implement this interface.
    This interface contains ONLY runtime operations - no test setup methods.
    """

    @property
    @abstractmethod
    def rebase_ops(self) -> RebaseOps:
        """Get the RebaseOps instance for rebase operations."""
        ...

    @abstractmethod
    def list_worktrees(self, repo_root: Path) -> list[WorktreeInfo]:
        """List all worktrees in the repository."""
        ...

    @abstractmethod
    def get_current_branch(self, cwd: Path) -> str | None:
        """Get the currently checked-out branch."""
        ...

    @abstractmethod
    def detect_default_branch(self, repo_root: Path) -> str:
        """Detect the default branch (main or master)."""
        ...

    @abstractmethod
    def get_git_common_dir(self, cwd: Path) -> Path | None:
        """Get the common git directory."""
        ...

    @abstractmethod
    def add_worktree(
        self,
        repo_root: Path,
        path: Path,
        *,
        branch: str | None,
        ref: str | None,
        create_branch: bool,
    ) -> None:
        """Add a new git worktree.

        Args:
            repo_root: Path to the git repository root
            path: Path where the worktree should be created
            branch: Branch name (None creates detached HEAD or uses ref)
            ref: Git ref to base worktree on (None defaults to HEAD when creating branches)
            create_branch: True to create new branch, False to checkout existing
        """
        ...

    @abstractmethod
    def move_worktree(self, repo_root: Path, old_path: Path, new_path: Path) -> None:
        """Move a worktree to a new location."""
        ...

    @abstractmethod
    def remove_worktree(self, repo_root: Path, path: Path, *, force: bool) -> None:
        """Remove a worktree.

        Args:
            repo_root: Path to the git repository root
            path: Path to the worktree to remove
            force: True to force removal even if worktree has uncommitted changes
        """
        ...

    @abstractmethod
    def checkout_branch(self, cwd: Path, branch: str) -> None:
        """Checkout a branch in the given directory."""
        ...

    @abstractmethod
    def delete_branch_with_graphite(self, repo_root: Path, branch: str, *, force: bool) -> None:
        """Delete a branch using Graphite's gt delete command."""
        ...

    @abstractmethod
    def prune_worktrees(self, repo_root: Path) -> None:
        """Prune stale worktree metadata."""
        ...

    @abstractmethod
    def is_branch_checked_out(self, repo_root: Path, branch: str) -> Path | None:
        """Check if a branch is already checked out in any worktree.

        Args:
            repo_root: Path to the git repository root
            branch: Branch name to check

        Returns:
            Path to the worktree where branch is checked out, or None if not checked out.
        """
        ...

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


class RealGitOps(GitOps):
    """Production implementation using subprocess.

    All git operations execute actual git commands via subprocess.
    """

    def __init__(self) -> None:
        """Initialize RealGitOps with a RealRebaseOps instance."""
        self._rebase_ops = RealRebaseOps()

    @property
    def rebase_ops(self) -> RebaseOps:
        """Get the RebaseOps instance for rebase operations."""
        return self._rebase_ops

    def list_worktrees(self, repo_root: Path) -> list[WorktreeInfo]:
        """List all worktrees in the repository."""
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )

        worktrees: list[WorktreeInfo] = []
        current_path: Path | None = None
        current_branch: str | None = None

        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("worktree "):
                current_path = Path(line.split(maxsplit=1)[1])
                current_branch = None
            elif line.startswith("branch "):
                if current_path is None:
                    continue
                branch_ref = line.split(maxsplit=1)[1]
                current_branch = branch_ref.replace("refs/heads/", "")
            elif line == "" and current_path is not None:
                worktrees.append(WorktreeInfo(path=current_path, branch=current_branch))
                current_path = None
                current_branch = None

        if current_path is not None:
            worktrees.append(WorktreeInfo(path=current_path, branch=current_branch))

        return worktrees

    def get_current_branch(self, cwd: Path) -> str | None:
        """Get the currently checked-out branch."""
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None

        branch = result.stdout.strip()
        if branch == "HEAD":
            return None

        return branch

    def detect_default_branch(self, repo_root: Path) -> str:
        """Detect the default branch (main or master)."""
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            remote_head = result.stdout.strip()
            if remote_head.startswith("refs/remotes/origin/"):
                branch = remote_head.replace("refs/remotes/origin/", "")
                return branch

        for candidate in ["main", "master"]:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", candidate],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return candidate

        click.echo("Error: Could not find 'main' or 'master' branch.", err=True)
        raise SystemExit(1)

    def get_git_common_dir(self, cwd: Path) -> Path | None:
        """Get the common git directory."""
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None

        git_dir = Path(result.stdout.strip())
        if not git_dir.is_absolute():
            git_dir = cwd / git_dir

        return git_dir.resolve()

    def add_worktree(
        self,
        repo_root: Path,
        path: Path,
        *,
        branch: str | None,
        ref: str | None,
        create_branch: bool,
    ) -> None:
        """Add a new git worktree."""
        if branch and not create_branch:
            cmd = ["git", "worktree", "add", str(path), branch]
        elif branch and create_branch:
            base_ref = ref or "HEAD"
            cmd = ["git", "worktree", "add", "-b", branch, str(path), base_ref]
        else:
            base_ref = ref or "HEAD"
            cmd = ["git", "worktree", "add", str(path), base_ref]

        subprocess.run(cmd, cwd=repo_root, check=True, capture_output=True, text=True)

    def move_worktree(self, repo_root: Path, old_path: Path, new_path: Path) -> None:
        """Move a worktree to a new location."""
        cmd = ["git", "worktree", "move", str(old_path), str(new_path)]
        subprocess.run(cmd, cwd=repo_root, check=True)

    def remove_worktree(self, repo_root: Path, path: Path, *, force: bool) -> None:
        """Remove a worktree."""
        cmd = ["git", "worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(str(path))
        subprocess.run(cmd, cwd=repo_root, check=True)

    def checkout_branch(self, cwd: Path, branch: str) -> None:
        """Checkout a branch in the given directory."""
        subprocess.run(
            ["git", "checkout", branch],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )

    def delete_branch_with_graphite(self, repo_root: Path, branch: str, *, force: bool) -> None:
        """Delete a branch using Graphite's gt delete command."""
        cmd = ["gt", "delete", branch]
        if force:
            cmd.insert(2, "-f")
        subprocess.run(cmd, cwd=repo_root, check=True)

    def prune_worktrees(self, repo_root: Path) -> None:
        """Prune stale worktree metadata."""
        subprocess.run(["git", "worktree", "prune"], cwd=repo_root, check=True)

    def is_branch_checked_out(self, repo_root: Path, branch: str) -> Path | None:
        """Check if a branch is already checked out in any worktree."""
        worktrees = self.list_worktrees(repo_root)
        for wt in worktrees:
            if wt.branch == branch:
                return wt.path
        return None

    def start_rebase(
        self,
        cwd: Path,
        onto: str,
        *,
        interactive: bool = False,
    ) -> tuple[bool, list[str]]:
        """Start a rebase onto the given branch."""
        return self._rebase_ops.start_rebase(cwd, onto, interactive=interactive)

    def continue_rebase(self, cwd: Path) -> tuple[bool, list[str]]:
        """Continue a rebase after resolving conflicts."""
        return self._rebase_ops.continue_rebase(cwd)

    def abort_rebase(self, cwd: Path) -> None:
        """Abort an ongoing rebase."""
        self._rebase_ops.abort_rebase(cwd)

    def get_rebase_status(self, cwd: Path) -> dict[str, Any]:
        """Get detailed rebase status."""
        return self._rebase_ops.get_rebase_status(cwd)

    def get_merge_base(self, cwd: Path, branch1: str, branch2: str) -> str | None:
        """Find the merge base commit between two branches."""
        return self._rebase_ops.get_merge_base(cwd, branch1, branch2)

    def get_commit_range(
        self,
        cwd: Path,
        from_ref: str,
        to_ref: str,
    ) -> list[dict[str, str]]:
        """Get list of commits between two refs."""
        return self._rebase_ops.get_commit_range(cwd, from_ref, to_ref)

    def get_conflicted_files(self, cwd: Path) -> list[str]:
        """Get list of files with merge conflicts."""
        return self._rebase_ops.get_conflicted_files(cwd)

    def check_clean_worktree(self, cwd: Path) -> bool:
        """Check if worktree has no uncommitted changes."""
        return self._rebase_ops.check_clean_worktree(cwd)


# ============================================================================
# Dry-Run Wrapper
# ============================================================================


class DryRunGitOps(GitOps):
    """Wrapper that prints dry-run messages instead of executing destructive operations.

    This wrapper intercepts destructive git operations and prints what would happen
    instead of executing. Read-only operations are delegated to the wrapped implementation.

    Usage:
        real_ops = RealGitOps()
        dry_run_ops = DryRunGitOps(real_ops)

        # Prints message instead of deleting
        dry_run_ops.remove_worktree(repo_root, path, force=False)
    """

    def __init__(self, wrapped: GitOps) -> None:
        """Create a dry-run wrapper around a GitOps implementation.

        Args:
            wrapped: The GitOps implementation to wrap (usually RealGitOps or FakeGitOps)
        """
        self._wrapped = wrapped

    @property
    def rebase_ops(self) -> RebaseOps:
        """Get the RebaseOps instance (delegates to wrapped)."""
        return self._wrapped.rebase_ops

    # Read-only operations: delegate to wrapped implementation

    def list_worktrees(self, repo_root: Path) -> list[WorktreeInfo]:
        """List all worktrees (read-only, delegates to wrapped)."""
        return self._wrapped.list_worktrees(repo_root)

    def get_current_branch(self, cwd: Path) -> str | None:
        """Get current branch (read-only, delegates to wrapped)."""
        return self._wrapped.get_current_branch(cwd)

    def detect_default_branch(self, repo_root: Path) -> str:
        """Detect default branch (read-only, delegates to wrapped)."""
        return self._wrapped.detect_default_branch(repo_root)

    def get_git_common_dir(self, cwd: Path) -> Path | None:
        """Get git common directory (read-only, delegates to wrapped)."""
        return self._wrapped.get_git_common_dir(cwd)

    def checkout_branch(self, cwd: Path, branch: str) -> None:
        """Checkout branch (delegates to wrapped - considered read-only for dry-run)."""
        return self._wrapped.checkout_branch(cwd, branch)

    # Destructive operations: print dry-run message instead of executing

    def add_worktree(
        self,
        repo_root: Path,
        path: Path,
        *,
        branch: str | None,
        ref: str | None,
        create_branch: bool,
    ) -> None:
        """Print dry-run message instead of adding worktree."""
        if branch and create_branch:
            base_ref = ref or "HEAD"
            click.echo(
                f"[DRY RUN] Would run: git worktree add -b {branch} {path} {base_ref}",
                err=True,
            )
        elif branch:
            click.echo(f"[DRY RUN] Would run: git worktree add {path} {branch}", err=True)
        else:
            base_ref = ref or "HEAD"
            click.echo(f"[DRY RUN] Would run: git worktree add {path} {base_ref}", err=True)

    def move_worktree(self, repo_root: Path, old_path: Path, new_path: Path) -> None:
        """Print dry-run message instead of moving worktree."""
        click.echo(f"[DRY RUN] Would run: git worktree move {old_path} {new_path}", err=True)

    def remove_worktree(self, repo_root: Path, path: Path, *, force: bool) -> None:
        """Print dry-run message instead of removing worktree."""
        force_flag = "--force " if force else ""
        click.echo(f"[DRY RUN] Would run: git worktree remove {force_flag}{path}", err=True)

    def delete_branch_with_graphite(self, repo_root: Path, branch: str, *, force: bool) -> None:
        """Print dry-run message instead of deleting branch."""
        force_flag = "-f " if force else ""
        click.echo(f"[DRY RUN] Would run: gt delete {force_flag}{branch}", err=True)

    def prune_worktrees(self, repo_root: Path) -> None:
        """Print dry-run message instead of pruning worktrees."""
        click.echo("[DRY RUN] Would run: git worktree prune", err=True)

    def is_branch_checked_out(self, repo_root: Path, branch: str) -> Path | None:
        """Check if branch is checked out (read-only, delegates to wrapped)."""
        return self._wrapped.is_branch_checked_out(repo_root, branch)

    def start_rebase(
        self,
        cwd: Path,
        onto: str,
        *,
        interactive: bool = False,
    ) -> tuple[bool, list[str]]:
        """Print dry-run message for rebase."""
        interactive_flag = "-i " if interactive else ""
        click.echo(f"[DRY RUN] Would run: git rebase {interactive_flag}{onto}", err=True)
        return self._wrapped.start_rebase(cwd, onto, interactive=interactive)

    def continue_rebase(self, cwd: Path) -> tuple[bool, list[str]]:
        """Print dry-run message for continue."""
        click.echo("[DRY RUN] Would run: git rebase --continue", err=True)
        return (True, [])

    def abort_rebase(self, cwd: Path) -> None:
        """Print dry-run message for abort."""
        click.echo("[DRY RUN] Would run: git rebase --abort", err=True)

    def get_rebase_status(self, cwd: Path) -> dict[str, Any]:
        """Get rebase status (read-only, delegates to wrapped)."""
        return self._wrapped.get_rebase_status(cwd)

    def get_merge_base(self, cwd: Path, branch1: str, branch2: str) -> str | None:
        """Get merge base (read-only, delegates to wrapped)."""
        return self._wrapped.get_merge_base(cwd, branch1, branch2)

    def get_commit_range(
        self,
        cwd: Path,
        from_ref: str,
        to_ref: str,
    ) -> list[dict[str, str]]:
        """Get commit range (read-only, delegates to wrapped)."""
        return self._wrapped.get_commit_range(cwd, from_ref, to_ref)

    def get_conflicted_files(self, cwd: Path) -> list[str]:
        """Get conflicted files (read-only, delegates to wrapped)."""
        return self._wrapped.get_conflicted_files(cwd)

    def check_clean_worktree(self, cwd: Path) -> bool:
        """Check clean worktree (read-only, delegates to wrapped)."""
        return self._wrapped.check_clean_worktree(cwd)
