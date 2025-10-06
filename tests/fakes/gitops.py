"""Fake git operations for testing.

FakeGitOps is an in-memory implementation that accepts pre-configured state
in its constructor. Construct instances directly with keyword arguments.
"""

from pathlib import Path

import click

from workstack.gitops import GitOps, WorktreeInfo


class FakeGitOps(GitOps):
    """In-memory fake implementation of git operations.

    This class has NO public setup methods. All state is provided via constructor
    using keyword arguments with sensible defaults (empty dicts).
    """

    def __init__(
        self,
        *,
        worktrees: dict[Path, list[WorktreeInfo]] | None = None,
        current_branches: dict[Path, str | None] | None = None,
        default_branches: dict[Path, str] | None = None,
        git_common_dirs: dict[Path, Path] | None = None,
    ) -> None:
        """Create FakeGitOps with pre-configured state.

        Args:
            worktrees: Mapping of repo_root -> list of worktrees
            current_branches: Mapping of cwd -> current branch
            default_branches: Mapping of repo_root -> default branch
            git_common_dirs: Mapping of cwd -> git common directory
        """
        self._worktrees = worktrees or {}
        self._current_branches = current_branches or {}
        self._default_branches = default_branches or {}
        self._git_common_dirs = git_common_dirs or {}
        self._deleted_branches: list[str] = []

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
        """Add a new worktree (mutates internal state)."""
        if repo_root not in self._worktrees:
            self._worktrees[repo_root] = []
        self._worktrees[repo_root].append(WorktreeInfo(path=path, branch=branch))

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

    def checkout_branch(self, cwd: Path, branch: str) -> None:
        """Checkout a branch (mutates internal state)."""
        self._current_branches[cwd] = branch

    def delete_branch_with_graphite(self, repo_root: Path, branch: str, *, force: bool) -> None:
        """Track which branches were deleted (mutates internal state)."""
        self._deleted_branches.append(branch)

    def prune_worktrees(self, repo_root: Path) -> None:
        """Prune stale worktree metadata (no-op for in-memory fake)."""
        pass

    @property
    def deleted_branches(self) -> list[str]:
        """Get the list of branches that have been deleted.

        This property is for test assertions only.
        """
        return self._deleted_branches
