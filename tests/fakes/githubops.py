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

    def get_pr_status(
        self, repo_root: Path, branch: str, *, debug: bool
    ) -> tuple[str, int | None, str | None]:
        """Get PR status from configured PRs.

        Returns ("NONE", None, None) if branch not found.
        Note: Returns URL in place of title since PullRequestInfo has no title field.
        """
        pr = self._prs.get(branch)
        if pr is None:
            return ("NONE", None, None)
        # PullRequestInfo has: number, state, url, is_draft, checks_passing
        # But get_pr_status expects: state, number, title
        # Using url as title since PullRequestInfo doesn't have a title field
        return (pr.state, pr.number, pr.url)
