"""Graphite CLI operations interface.

This module provides a clean abstraction over graphite subprocess calls,
making the codebase more testable and maintainable.

Architecture:
- GraphiteOps: Abstract base class defining the interface
- RealGraphiteOps: Production implementation using subprocess
"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

import click

# ============================================================================
# Abstract Interface
# ============================================================================


class GraphiteOps(ABC):
    """Abstract interface for Graphite CLI operations.

    All implementations (real and fake) must implement this interface.
    This interface contains ONLY runtime operations - no test setup methods.
    """

    @abstractmethod
    def sync(self, cwd: Path, force: bool = False) -> None:
        """Run gt sync command.

        Args:
            cwd: Directory to run command from
            force: Whether to use --force flag

        Raises:
            FileNotFoundError: If gt command is not installed
            subprocess.CalledProcessError: If gt sync fails
        """
        ...


# ============================================================================
# Production Implementation
# ============================================================================


class RealGraphiteOps(GraphiteOps):
    """Production implementation using subprocess.

    All graphite operations execute actual CLI commands via subprocess.
    """

    def sync(self, cwd: Path, force: bool = False) -> None:
        """Run gt sync command.

        Args:
            cwd: Directory to run command from
            force: Whether to use --force flag

        Raises:
            FileNotFoundError: If gt command is not installed
            subprocess.CalledProcessError: If gt sync fails
        """
        cmd = ["gt", "sync"]
        if force:
            cmd.append("-f")

        subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=False,
        )


# ============================================================================
# Dry-Run Wrapper
# ============================================================================


class DryRunGraphiteOps(GraphiteOps):
    """Wrapper that prints dry-run messages instead of executing operations.

    This wrapper intercepts graphite operations and prints what would happen
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
            wrapped: The GraphiteOps implementation to wrap
        """
        self._wrapped = wrapped

    def sync(self, cwd: Path, force: bool = False) -> None:
        """Print dry-run message instead of running gt sync."""
        force_flag = "-f " if force else ""
        click.echo(f"[DRY RUN] Would run: gt sync {force_flag}".strip())
