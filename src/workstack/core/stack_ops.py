"""High-level stack operations interface.

This module provides a clean abstraction over stack detection using Graphite,
making the codebase more testable and maintainable.

Architecture:
- StackOps: Abstract base class defining the interface
- GraphiteStackOps: Production implementation using Graphite CLI
"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from workstack.core.gitops import GitOps, WorktreeInfo


class StackOps(ABC):
    """Abstract interface for stack operations.

    All implementations (real and fake) must implement this interface.
    """

    @abstractmethod
    def get_stack_worktrees(self, git_ops: GitOps, current_dir: Path) -> list[WorktreeInfo]:
        """Get all worktrees in current stack.

        Args:
            git_ops: GitOps instance for git operations
            current_dir: Current working directory

        Returns:
            List of WorktreeInfo for all worktrees in the stack
        """
        ...


class GraphiteStackOps(StackOps):
    """Production implementation using Graphite CLI.

    Uses 'gt log --show-stack' to detect stack boundaries and maps branches
    to worktrees.
    """

    def get_stack_worktrees(self, git_ops: GitOps, current_dir: Path) -> list[WorktreeInfo]:
        """Get all worktrees in current stack using Graphite.

        Algorithm:
        1. Get current branch from git
        2. Run 'gt log --show-stack' to get branches in current stack
        3. Parse output to extract branch names
        4. Map branches to worktrees using git_ops.list_worktrees()

        Args:
            git_ops: GitOps instance for git operations
            current_dir: Current working directory

        Returns:
            List of WorktreeInfo for all worktrees in the stack
        """
        current_branch = git_ops.get_current_branch(current_dir)
        if current_branch is None:
            return []

        git_common_dir = git_ops.get_git_common_dir(current_dir)
        if git_common_dir is None:
            return []

        repo_root = git_common_dir.parent

        result = subprocess.run(
            ["gt", "log", "--show-stack"],
            capture_output=True,
            text=True,
            cwd=current_dir,
            check=True,
        )

        stack_branches = self._parse_stack_output(result.stdout, current_branch)

        all_worktrees = git_ops.list_worktrees(repo_root)
        return [wt for wt in all_worktrees if wt.branch in stack_branches]

    def _parse_stack_output(self, output: str, current_branch: str) -> set[str]:
        """Parse gt log --show-stack output to extract branch names.

        The output format looks like:
            ◯ branch-name (commit-hash)
            │
            ◉ another-branch (commit-hash)

        We extract all branch names that appear in the stack.

        Args:
            output: Output from 'gt log --show-stack'
            current_branch: Current branch name

        Returns:
            Set of branch names in the stack
        """
        branches: set[str] = set()

        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("◯") or line.startswith("◉"):
                parts = line.split()
                if len(parts) >= 2:
                    branch_name = parts[1]
                    branches.add(branch_name)

        if current_branch not in branches and branches:
            branches.add(current_branch)

        return branches
