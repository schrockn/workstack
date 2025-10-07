"""High-level GitHub operations interface.

This module provides a clean abstraction over GitHub CLI (gh) calls, making the
codebase more testable and maintainable.

Architecture:
- GitHubOps: Abstract base class defining the interface
- RealGitHubOps: Production implementation using gh CLI
- Standalone functions: Convenience wrappers if needed
"""

import json
import re
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


def _parse_github_pr_url(url: str) -> tuple[str, str] | None:
    """Parse owner and repo from GitHub PR URL.

    Args:
        url: GitHub PR URL (e.g., "https://github.com/owner/repo/pull/123")

    Returns:
        Tuple of (owner, repo) or None if URL doesn't match expected pattern

    Example:
        >>> _parse_github_pr_url("https://github.com/schrockn/workstack/pull/23")
        ("schrockn", "workstack")
    """
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/\d+", url)
    if match:
        return (match.group(1), match.group(2))
    return None


@dataclass(frozen=True)
class PullRequestInfo:
    """Information about a GitHub pull request."""

    number: int
    state: str  # "OPEN", "MERGED", "CLOSED"
    url: str
    is_draft: bool
    checks_passing: bool | None  # None if no checks, True if all pass, False if any fail
    owner: str  # GitHub repo owner (e.g., "schrockn")
    repo: str  # GitHub repo name (e.g., "workstack")


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

    @abstractmethod
    def get_pr_status(
        self, repo_root: Path, branch: str, *, debug: bool
    ) -> tuple[str, int | None, str | None]:
        """Get PR status for a specific branch.

        Args:
            repo_root: Repository root directory
            branch: Branch name to check
            debug: If True, print debug information

        Returns:
            Tuple of (state, pr_number, title)
            - state: "OPEN", "MERGED", "CLOSED", or "NONE" if no PR exists
            - pr_number: PR number or None if no PR exists
            - title: PR title or None if no PR exists
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

                # Parse owner and repo from GitHub URL
                url = pr["url"]
                parsed = _parse_github_pr_url(url)
                if parsed is None:
                    # Skip PRs with malformed URLs (shouldn't happen in practice)
                    continue
                owner, repo = parsed

                prs[branch] = PullRequestInfo(
                    number=pr["number"],
                    state=pr["state"],
                    url=url,
                    is_draft=pr["isDraft"],
                    checks_passing=checks_passing,
                    owner=owner,
                    repo=repo,
                )

            return prs

        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            # gh not installed, not authenticated, or JSON parsing failed
            return {}

    def get_pr_status(
        self, repo_root: Path, branch: str, *, debug: bool
    ) -> tuple[str, int | None, str | None]:
        """Get PR status for a specific branch.

        Note: Uses try/except as an acceptable error boundary for handling gh CLI
        availability and authentication. We cannot reliably check gh installation
        and authentication status a priori without duplicating gh's logic.
        """
        try:
            # Query gh for PR info for this specific branch
            cmd = [
                "gh",
                "pr",
                "list",
                "--head",
                branch,
                "--state",
                "all",
                "--json",
                "number,state,title",
                "--limit",
                "1",
            ]

            if debug:
                import click

                click.echo(f"$ {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            prs_data = json.loads(result.stdout)

            # If no PR exists for this branch
            if not prs_data:
                return ("NONE", None, None)

            # Take the first (and should be only) PR
            pr = prs_data[0]
            return (pr["state"], pr["number"], pr["title"])

        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            # gh not installed, not authenticated, or JSON parsing failed
            return ("NONE", None, None)

    def _determine_checks_status(self, check_rollup: list[dict]) -> bool | None:
        """Determine overall CI checks status.

        Returns:
            None if no checks configured
            True if all checks passed (SUCCESS, SKIPPED, or NEUTRAL)
            False if any check failed or is pending
        """
        if not check_rollup:
            return None

        # GitHub check conclusions that should be treated as passing
        passing_conclusions = {"SUCCESS", "SKIPPED", "NEUTRAL"}

        for check in check_rollup:
            status = check.get("status")
            conclusion = check.get("conclusion")

            # If any check is not completed, consider it failing
            if status != "COMPLETED":
                return False

            # If any completed check didn't pass, consider it failing
            if conclusion not in passing_conclusions:
                return False

        return True
