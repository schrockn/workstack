"""High-level Graphite operations interface.

This module provides a clean abstraction over Graphite CLI (gt) calls, making the
codebase more testable and maintainable.

Architecture:
- GraphiteOps: Abstract base class defining the interface
- RealGraphiteOps: Production implementation using gt CLI
"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path


class GraphiteOps(ABC):
    """Abstract interface for Graphite operations.

    All implementations (real and fake) must implement this interface.
    """

    @abstractmethod
    def get_graphite_url(self, owner: str, repo: str, pr_number: int) -> str:
        """Get Graphite PR URL for a pull request.

        Args:
            owner: GitHub repository owner (e.g., "schrockn")
            repo: GitHub repository name (e.g., "workstack")
            pr_number: GitHub PR number

        Returns:
            Graphite PR URL (e.g., "https://app.graphite.dev/github/pr/schrockn/workstack/23")
        """
        ...

    @abstractmethod
    def sync(self, repo_root: Path, *, force: bool) -> None:
        """Run gt sync to synchronize with remote.

        Args:
            repo_root: Repository root directory
            force: If True, pass --force flag to gt sync
        """
        ...


class RealGraphiteOps(GraphiteOps):
    """Production implementation using gt CLI.

    All Graphite operations execute actual gt commands via subprocess.
    """

    def get_graphite_url(self, owner: str, repo: str, pr_number: int) -> str:
        """Get Graphite PR URL for a pull request.

        Constructs the Graphite URL directly from GitHub repo information.
        No subprocess calls or external dependencies required.

        Args:
            owner: GitHub repository owner (e.g., "schrockn")
            repo: GitHub repository name (e.g., "workstack")
            pr_number: GitHub PR number

        Returns:
            Graphite PR URL (e.g., "https://app.graphite.dev/github/pr/schrockn/workstack/23")
        """
        return f"https://app.graphite.dev/github/pr/{owner}/{repo}/{pr_number}"

    def sync(self, repo_root: Path, *, force: bool) -> None:
        """Run gt sync to synchronize with remote."""
        cmd = ["gt", "sync"]
        if force:
            cmd.append("-f")

        subprocess.run(
            cmd,
            cwd=repo_root,
            check=True,
        )
