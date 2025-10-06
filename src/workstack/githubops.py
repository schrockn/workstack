"""High-level GitHub operations interface.

This module provides a clean abstraction over GitHub CLI (gh) calls, making the
codebase more testable and maintainable.

Architecture:
- GitHubOps: Abstract base class defining the interface
- RealGitHubOps: Production implementation using gh CLI
- Standalone functions: Convenience wrappers if needed
"""

import json
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PullRequestInfo:
    """Information about a GitHub pull request."""

    number: int
    state: str  # "OPEN", "MERGED", "CLOSED"
    url: str
    is_draft: bool
    checks_passing: bool | None  # None if no checks, True if all pass, False if any fail


class GitHubOps(ABC):
    """Abstract interface for GitHub operations.

    All implementations (real and fake) must implement this interface.
    """

    @abstractmethod
    def get_prs_for_repo(self, repo_root: Path) -> dict[str, PullRequestInfo]:
        """Get PR information for all branches in the repository.

        Returns:
            Mapping of branch name -> PullRequestInfo
            Empty dict if gh CLI is not available or not authenticated
        """
        ...


class RealGitHubOps(GitHubOps):
    """Production implementation using gh CLI.

    All GitHub operations execute actual gh commands via subprocess.
    """

    def get_prs_for_repo(self, repo_root: Path) -> dict[str, PullRequestInfo]:
        """Get PR information for all branches in the repository.

        Note: Uses try/except as an acceptable error boundary for handling gh CLI
        availability and authentication. We cannot reliably check gh installation
        and authentication status a priori without duplicating gh's logic.
        """
        try:
            # Fetch all PRs in one call for efficiency
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "list",
                    "--state",
                    "all",
                    "--json",
                    "number,headRefName,url,state,isDraft,statusCheckRollup",
                ],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            prs_data = json.loads(result.stdout)
            prs: dict[str, PullRequestInfo] = {}

            for pr in prs_data:
                branch = pr["headRefName"]
                checks_passing = self._determine_checks_status(pr.get("statusCheckRollup", []))

                prs[branch] = PullRequestInfo(
                    number=pr["number"],
                    state=pr["state"],
                    url=pr["url"],
                    is_draft=pr["isDraft"],
                    checks_passing=checks_passing,
                )

            return prs

        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            # gh not installed, not authenticated, or JSON parsing failed
            return {}

    def _determine_checks_status(self, check_rollup: list[dict]) -> bool | None:
        """Determine overall CI checks status.

        Returns:
            None if no checks configured
            True if all checks passed
            False if any check failed or is pending
        """
        if not check_rollup:
            return None

        for check in check_rollup:
            status = check.get("status")
            conclusion = check.get("conclusion")

            # If any check is not completed, consider it failing
            if status != "COMPLETED":
                return False

            # If any completed check didn't succeed, consider it failing
            if conclusion != "SUCCESS":
                return False

        return True
