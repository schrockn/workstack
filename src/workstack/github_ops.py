"""GitHub CLI operations interface.

This module provides a clean abstraction over GitHub CLI subprocess calls,
making the codebase more testable and maintainable.

Architecture:
- GithubOps: Abstract base class defining the interface
- RealGithubOps: Production implementation using subprocess
"""

import json
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

import click

# ============================================================================
# Abstract Interface
# ============================================================================


class GithubOps(ABC):
    """Abstract interface for GitHub CLI operations.

    All implementations (real and fake) must implement this interface.
    This interface contains ONLY runtime operations - no test setup methods.
    """

    @abstractmethod
    def get_pr_status(
        self, repo_root: Path, branch: str, debug: bool = False
    ) -> tuple[str | None, int | None, str | None]:
        """Get PR status for a branch using GitHub CLI.

        Args:
            repo_root: Repository root directory
            branch: Branch name to check
            debug: Whether to print debug messages

        Returns:
            Tuple of (state, pr_number, title) where:
            - state is "MERGED", "CLOSED", "OPEN", or None if no PR found
            - pr_number is the PR number or None
            - title is the PR title or None

        Note: Returns (None, None, None) if gh CLI is not installed or not authenticated.
        """
        ...


# ============================================================================
# Production Implementation
# ============================================================================


class RealGithubOps(GithubOps):
    """Production implementation using subprocess.

    All GitHub operations execute actual CLI commands via subprocess.
    """

    def get_pr_status(
        self, repo_root: Path, branch: str, debug: bool = False
    ) -> tuple[str | None, int | None, str | None]:
        """Get PR status for a branch using GitHub CLI.

        Returns tuple of (state, pr_number, title) where:
        - state is "MERGED", "CLOSED", "OPEN", or None if no PR found
        - pr_number is the PR number or None
        - title is the PR title or None

        Returns (None, None, None) if gh CLI is not installed or not authenticated.

        Note: Uses try/except as an acceptable error boundary for handling gh CLI
        availability and authentication. We cannot reliably check gh installation
        and authentication status a priori without duplicating gh's logic.
        """

        def debug_print(msg: str) -> None:
            if debug:
                click.echo(click.style(msg, fg="bright_black"))

        try:
            # Check merged PRs first, then closed, then open
            for state in ["merged", "closed", "open"]:
                cmd = [
                    "gh",
                    "pr",
                    "list",
                    "--state",
                    state,
                    "--head",
                    branch,
                    "--json",
                    "number,title,state",
                    "--jq",
                    ".[0] | {number, title, state}",
                ]

                debug_print(f"Running: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )

                output = result.stdout.strip()
                debug_print(f"Output: {output}")

                if not output or output == "null":
                    continue

                # Parse JSON output
                data = json.loads(output)
                pr_number = data.get("number")
                title = data.get("title")
                pr_state = data.get("state")

                if pr_number is not None:
                    return (pr_state, pr_number, title)

            # No PR found
            return (None, None, None)

        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            # gh not installed, not authenticated, or other error
            return (None, None, None)
