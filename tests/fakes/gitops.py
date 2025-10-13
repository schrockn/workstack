"""Fake git operations for testing.

FakeGitOps is an in-memory implementation that accepts pre-configured state
in its constructor. Construct instances directly with keyword arguments.
"""

from pathlib import Path
from typing import Any

import click

from tests.fakes.rebaseops import FakeRebaseOps
from workstack.core.gitops import GitOps, WorktreeInfo
from workstack.core.rebaseops import RebaseOps


class FakeGitOps(GitOps):
    """In-memory fake implementation of git operations.

    State Management:
    -----------------
    This fake maintains mutable state to simulate git's stateful behavior.
    Operations like add_worktree, checkout_branch modify internal state.
    State changes are visible to subsequent method calls within the same test.

    When to Use Mutation:
    --------------------
    - Operations that simulate stateful external systems (git, databases)
    - When tests need to verify sequences of operations
    - When simulating side effects visible to production code

    Constructor Injection:
    ---------------------
    All INITIAL state is provided via constructor (immutable after construction).
    Runtime mutations occur through operation methods.
    Tests should construct fakes with complete initial state.

    Mutation Tracking:
    -----------------
    This fake tracks mutations for test assertions via read-only properties:
    - deleted_branches: Branches deleted via delete_branch_with_graphite()
    - added_worktrees: Worktrees added via add_worktree()
    - removed_worktrees: Worktrees removed via remove_worktree()
    - checked_out_branches: Branches checked out via checkout_branch()

    Examples:
    ---------
        # Initial state via constructor
        git_ops = FakeGitOps(
            worktrees={repo: [WorktreeInfo(path=wt1, branch="main")]},
            current_branches={wt1: "main"},
            git_common_dirs={repo: repo / ".git"},
        )

        # Mutation through operation
        git_ops.add_worktree(repo, wt2, branch="feature")

        # Verify mutation
        assert len(git_ops.list_worktrees(repo)) == 2
        assert (wt2, "feature") in git_ops.added_worktrees

        # Verify sequence of operations
        git_ops.checkout_branch(repo, "feature")
        git_ops.delete_branch_with_graphite(repo, "old-feature", force=True)
        assert (repo, "feature") in git_ops.checked_out_branches
        assert "old-feature" in git_ops.deleted_branches
    """

    def __init__(
        self,
        *,
        worktrees: dict[Path, list[WorktreeInfo]] | None = None,
        current_branches: dict[Path, str | None] | None = None,
        default_branches: dict[Path, str] | None = None,
        git_common_dirs: dict[Path, Path] | None = None,
        merge_bases: dict[tuple[str, str], str | None] | None = None,
        commit_ranges: dict[tuple[str, str], list[dict[str, str]]] | None = None,
        conflicted_files: dict[Path, list[str]] | None = None,
        rebase_in_progress: dict[Path, bool] | None = None,
        clean_worktrees: dict[Path, bool] | None = None,
    ) -> None:
        """Create FakeGitOps with pre-configured state.

        Args:
            worktrees: Mapping of repo_root -> list of worktrees
            current_branches: Mapping of cwd -> current branch
            default_branches: Mapping of repo_root -> default branch
            git_common_dirs: Mapping of cwd -> git common directory
            merge_bases: Mapping of (branch1, branch2) -> merge base SHA
            commit_ranges: Mapping of (from_ref, to_ref) -> list of commits
            conflicted_files: Mapping of cwd -> list of conflicted file paths
            rebase_in_progress: Mapping of cwd -> whether rebase is in progress
            clean_worktrees: Mapping of cwd -> whether worktree is clean
        """
        self._worktrees = worktrees or {}
        self._current_branches = current_branches or {}
        self._default_branches = default_branches or {}
        self._git_common_dirs = git_common_dirs or {}

        # Mutation tracking
        self._deleted_branches: list[str] = []
        self._added_worktrees: list[tuple[Path, str | None]] = []
        self._removed_worktrees: list[Path] = []
        self._checked_out_branches: list[tuple[Path, str]] = []

        # Create FakeRebaseOps with rebase-related state
        self._rebase_ops_instance = FakeRebaseOps(
            merge_bases=merge_bases,
            commit_ranges=commit_ranges,
            conflicted_files=conflicted_files,
            rebase_in_progress=rebase_in_progress,
            clean_worktrees=clean_worktrees,
        )

    @property
    def rebase_ops(self) -> RebaseOps:
        """Get the RebaseOps instance for rebase operations."""
        return self._rebase_ops_instance

    def list_worktrees(self, repo_root: Path) -> list[WorktreeInfo]:
        """List all worktrees in the repository."""
        return self._worktrees.get(repo_root, [])

    def get_current_branch(self, cwd: Path) -> str | None:
        """Get the currently checked-out branch."""
        return self._current_branches.get(cwd)

    def detect_default_branch(self, repo_root: Path) -> str:
        """Detect the default branch."""
        if repo_root in self._default_branches:
            return self._default_branches[repo_root]
        click.echo("Error: Could not find 'main' or 'master' branch.", err=True)
        raise SystemExit(1)

    def get_git_common_dir(self, cwd: Path) -> Path | None:
        """Get the common git directory."""
        return self._git_common_dirs.get(cwd)

    def add_worktree(
        self,
        repo_root: Path,
        path: Path,
        *,
        branch: str | None = None,
        ref: str | None = None,
        create_branch: bool = False,
    ) -> None:
        """Add a new worktree (mutates internal state and creates directory)."""
        if repo_root not in self._worktrees:
            self._worktrees[repo_root] = []
        self._worktrees[repo_root].append(WorktreeInfo(path=path, branch=branch))
        # Create the worktree directory to simulate git worktree add behavior
        path.mkdir(parents=True, exist_ok=True)
        # Track the addition
        self._added_worktrees.append((path, branch))

    def move_worktree(self, repo_root: Path, old_path: Path, new_path: Path) -> None:
        """Move a worktree (mutates internal state and simulates filesystem move)."""
        if repo_root in self._worktrees:
            for i, wt in enumerate(self._worktrees[repo_root]):
                if wt.path == old_path:
                    self._worktrees[repo_root][i] = WorktreeInfo(path=new_path, branch=wt.branch)
                    break
        # Simulate the filesystem move if the paths exist
        if old_path.exists():
            old_path.rename(new_path)

    def remove_worktree(self, repo_root: Path, path: Path, *, force: bool = False) -> None:
        """Remove a worktree (mutates internal state)."""
        if repo_root in self._worktrees:
            self._worktrees[repo_root] = [
                wt for wt in self._worktrees[repo_root] if wt.path != path
            ]
        # Track the removal
        self._removed_worktrees.append(path)

    def checkout_branch(self, cwd: Path, branch: str) -> None:
        """Checkout a branch (mutates internal state)."""
        self._current_branches[cwd] = branch
        # Update worktree branch in the worktrees list
        for repo_root, worktrees in self._worktrees.items():
            for i, wt in enumerate(worktrees):
                if wt.path.resolve() == cwd.resolve():
                    self._worktrees[repo_root][i] = WorktreeInfo(path=wt.path, branch=branch)
                    break
        # Track the checkout
        self._checked_out_branches.append((cwd, branch))

    def delete_branch_with_graphite(self, repo_root: Path, branch: str, *, force: bool) -> None:
        """Track which branches were deleted (mutates internal state)."""
        self._deleted_branches.append(branch)

    def prune_worktrees(self, repo_root: Path) -> None:
        """Prune stale worktree metadata (no-op for in-memory fake)."""
        pass

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
        """Start a rebase (delegates to RebaseOps)."""
        return self._rebase_ops_instance.start_rebase(cwd, onto, interactive=interactive)

    def continue_rebase(self, cwd: Path) -> tuple[bool, list[str]]:
        """Continue a rebase (delegates to RebaseOps)."""
        return self._rebase_ops_instance.continue_rebase(cwd)

    def abort_rebase(self, cwd: Path) -> None:
        """Abort a rebase (delegates to RebaseOps)."""
        self._rebase_ops_instance.abort_rebase(cwd)

    def get_rebase_status(self, cwd: Path) -> dict[str, Any]:
        """Get rebase status (delegates to RebaseOps)."""
        return self._rebase_ops_instance.get_rebase_status(cwd)

    def get_merge_base(self, cwd: Path, branch1: str, branch2: str) -> str | None:
        """Get merge base (delegates to RebaseOps)."""
        return self._rebase_ops_instance.get_merge_base(cwd, branch1, branch2)

    def get_commit_range(
        self,
        cwd: Path,
        from_ref: str,
        to_ref: str,
    ) -> list[dict[str, str]]:
        """Get commit range (delegates to RebaseOps)."""
        return self._rebase_ops_instance.get_commit_range(cwd, from_ref, to_ref)

    def get_conflicted_files(self, cwd: Path) -> list[str]:
        """Get conflicted files (delegates to RebaseOps)."""
        return self._rebase_ops_instance.get_conflicted_files(cwd)

    def check_clean_worktree(self, cwd: Path) -> bool:
        """Check if worktree is clean (delegates to RebaseOps)."""
        return self._rebase_ops_instance.check_clean_worktree(cwd)

    @property
    def deleted_branches(self) -> list[str]:
        """Get the list of branches that have been deleted.

        This property is for test assertions only.
        """
        return self._deleted_branches.copy()

    @property
    def added_worktrees(self) -> list[tuple[Path, str | None]]:
        """Get list of worktrees added during test.

        Returns list of (path, branch) tuples.
        This property is for test assertions only.
        """
        return self._added_worktrees.copy()

    @property
    def removed_worktrees(self) -> list[Path]:
        """Get list of worktrees removed during test.

        This property is for test assertions only.
        """
        return self._removed_worktrees.copy()

    @property
    def checked_out_branches(self) -> list[tuple[Path, str]]:
        """Get list of branches checked out during test.

        Returns list of (cwd, branch) tuples.
        This property is for test assertions only.
        """
        return self._checked_out_branches.copy()
