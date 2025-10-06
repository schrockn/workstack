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
