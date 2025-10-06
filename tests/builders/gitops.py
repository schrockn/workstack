"""Builder for creating configured FakeGitOps instances in tests."""

from pathlib import Path

from tests.fakes.gitops import FakeGitOps
from workstack.gitops import WorktreeInfo


class GitOpsBuilder:
    """Fluent builder for configuring FakeGitOps in tests.

    Provides a clear, readable API for test setup that separates test
    configuration from production code.

    Example:
        >>> git = (
        ...     GitOpsBuilder()
        ...     .with_default_branch(Path("/repo"), "main")
        ...     .with_worktrees(Path("/repo"), [
        ...         WorktreeInfo(Path("/repo"), "main"),
        ...         WorktreeInfo(Path("/wt/feature"), "feature/auth"),
        ...     ])
        ...     .build()
        ... )
    """

    def __init__(self) -> None:
        self._worktrees: dict[Path, list[WorktreeInfo]] = {}
        self._current_branches: dict[Path, str | None] = {}
        self._default_branches: dict[Path, str] = {}
        self._git_common_dirs: dict[Path, Path] = {}

    def with_worktrees(self, repo_root: Path, worktrees: list[WorktreeInfo]) -> "GitOpsBuilder":
        """Configure worktrees for a repository.

        Args:
            repo_root: Repository root path
            worktrees: List of worktree information

        Returns:
            Self for method chaining
        """
        self._worktrees[repo_root] = worktrees
        return self

    def with_current_branch(self, cwd: Path, branch: str | None) -> "GitOpsBuilder":
        """Configure current branch for a directory.

        Args:
            cwd: Directory path
            branch: Current branch name (None for detached HEAD)

        Returns:
            Self for method chaining
        """
        self._current_branches[cwd] = branch
        return self

    def with_default_branch(self, repo_root: Path, branch: str) -> "GitOpsBuilder":
        """Configure default branch for a repository.

        Args:
            repo_root: Repository root path
            branch: Default branch name ("main" or "master")

        Returns:
            Self for method chaining
        """
        self._default_branches[repo_root] = branch
        return self

    def with_git_common_dir(self, cwd: Path, git_dir: Path) -> "GitOpsBuilder":
        """Configure git common directory.

        Args:
            cwd: Directory path
            git_dir: Git common directory path

        Returns:
            Self for method chaining
        """
        self._git_common_dirs[cwd] = git_dir
        return self

    def build(self) -> FakeGitOps:
        """Build the configured FakeGitOps instance.

        Returns:
            FakeGitOps with all configured state
        """
        return FakeGitOps(
            worktrees=self._worktrees,
            current_branches=self._current_branches,
            default_branches=self._default_branches,
            git_common_dirs=self._git_common_dirs,
        )
