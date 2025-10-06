"""Fake GitHub operations for testing.

FakeGitHubOps is an in-memory implementation that accepts pre-configured state
in its constructor. Construct instances directly with keyword arguments.
"""

from pathlib import Path

from workstack.githubops import GitHubOps, PullRequestInfo


class FakeGitHubOps(GitHubOps):
    """In-memory fake implementation of GitHub operations.

    This class has NO public setup methods. All state is provided via constructor
    using keyword arguments with sensible defaults (empty dicts).
    """

    def __init__(
        self,
        *,
        prs: dict[str, PullRequestInfo] | None = None,
    ) -> None:
        """Create FakeGitHubOps with pre-configured state.

        Args:
            prs: Mapping of branch name -> PullRequestInfo
        """
        self._prs = prs or {}

    def get_prs_for_repo(self, repo_root: Path) -> dict[str, PullRequestInfo]:
        """Get PR information for all branches (returns pre-configured data)."""
        return self._prs
