"""Fake GitHub operations for testing.

FakeGithubOps is an in-memory implementation that accepts pre-configured state
in its constructor. Construct instances directly with keyword arguments.
"""

from pathlib import Path

from workstack.github_ops import GithubOps


class FakeGithubOps(GithubOps):
    """In-memory fake implementation of GitHub operations.

    This class has NO public setup methods. All state is provided via constructor
    using keyword arguments with sensible defaults.
    """

    def __init__(
        self,
        *,
        pr_statuses: dict[str, tuple[str | None, int | None, str | None]] | None = None,
    ) -> None:
        """Create FakeGithubOps with pre-configured state.

        Args:
            pr_statuses: Mapping of branch name -> (state, pr_number, title)
                         If a branch is not in the mapping, returns (None, None, None)
        """
        self._pr_statuses = pr_statuses or {}

    def get_pr_status(
        self, repo_root: Path, branch: str, debug: bool = False
    ) -> tuple[str | None, int | None, str | None]:
        """Get PR status from configured mapping.

        Returns (None, None, None) if branch is not in the mapping.
        """
        return self._pr_statuses.get(branch, (None, None, None))
