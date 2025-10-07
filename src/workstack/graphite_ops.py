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
        """Run gt sync to synchronize with remote.

        Note: Uses try/except as an acceptable error boundary for handling gt CLI
        availability. We cannot reliably check gt installation status a priori.
        """
        cmd = ["gt", "sync"]
        if force:
            cmd.append("-f")

        subprocess.run(
            cmd,
            cwd=repo_root,
            check=True,
        )


class DryRunGraphiteOps(GraphiteOps):
    """Wrapper that prints dry-run messages instead of executing destructive operations.

    This wrapper intercepts destructive graphite operations and prints what would happen
    instead of executing. Read-only operations are delegated to the wrapped implementation.

    Usage:
        real_ops = RealGraphiteOps()
        dry_run_ops = DryRunGraphiteOps(real_ops)

        # Prints message instead of running gt sync
        dry_run_ops.sync(repo_root, force=False)
    """

    def __init__(self, wrapped: GraphiteOps) -> None:
        """Create a dry-run wrapper around a GraphiteOps implementation.

        Args:
            wrapped: The GraphiteOps implementation to wrap (usually RealGraphiteOps)
        """
        self._wrapped = wrapped

    # Read-only operations: delegate to wrapped implementation

    def get_graphite_url(self, owner: str, repo: str, pr_number: int) -> str:
        """Get Graphite PR URL (read-only, delegates to wrapped)."""
        return self._wrapped.get_graphite_url(owner, repo, pr_number)

    # Destructive operations: print dry-run message instead of executing

    def sync(self, repo_root: Path, *, force: bool) -> None:
        """Print dry-run message instead of running gt sync."""
        import click

        cmd = ["gt", "sync"]
        if force:
            cmd.append("-f")

        click.echo(f"[DRY RUN] Would run: {' '.join(cmd)}")
