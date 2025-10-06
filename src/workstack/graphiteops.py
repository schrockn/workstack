"""High-level Graphite operations interface.

This module provides a clean abstraction over Graphite CLI (gt) calls, making the
codebase more testable and maintainable.

Architecture:
- GraphiteOps: Abstract base class defining the interface
- RealGraphiteOps: Production implementation using gt CLI
"""

import re
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path


class GraphiteOps(ABC):
    """Abstract interface for Graphite operations.

    All implementations (real and fake) must implement this interface.
    """

    @abstractmethod
    def get_graphite_url(self, repo_root: Path, branch: str, pr_number: int) -> str | None:
        """Get Graphite PR URL for a branch.

        Args:
            repo_root: Repository root directory
            branch: Branch name
            pr_number: GitHub PR number

        Returns:
            Graphite PR URL if available, None otherwise
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

    def get_graphite_url(self, repo_root: Path, branch: str, pr_number: int) -> str | None:
        """Get Graphite PR URL for a branch.

        Note: Uses try/except as an acceptable error boundary for handling gt CLI
        availability. We cannot reliably check gt installation status a priori.
        """
        try:
            result = subprocess.run(
                ["gt", "branch", "info", branch],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse output for Graphite URL
            # Expected format: "https://app.graphite.dev/github/pr/owner/repo/NUMBER"
            match = re.search(r"https://app\.graphite\.dev/github/pr/[^\s]+", result.stdout)
            if match:
                return match.group(0)

            return None

        except (subprocess.CalledProcessError, FileNotFoundError):
            # gt not installed or branch not in Graphite
            return None

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

    def get_graphite_url(self, repo_root: Path, branch: str, pr_number: int) -> str | None:
        """Get Graphite PR URL (read-only, delegates to wrapped)."""
        return self._wrapped.get_graphite_url(repo_root, branch, pr_number)

    # Destructive operations: print dry-run message instead of executing

    def sync(self, repo_root: Path, *, force: bool) -> None:
        """Print dry-run message instead of running gt sync."""
        import click

        cmd = ["gt", "sync"]
        if force:
            cmd.append("-f")

        click.echo(f"[DRY RUN] Would run: {' '.join(cmd)}")
