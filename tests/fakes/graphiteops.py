"""Fake Graphite operations for testing.

FakeGraphiteOps is an in-memory implementation that accepts pre-configured state
in its constructor. Construct instances directly with keyword arguments.
"""

from pathlib import Path

from workstack.graphiteops import GraphiteOps


class FakeGraphiteOps(GraphiteOps):
    """In-memory fake implementation of Graphite operations.

    This class has NO public setup methods. All state is provided via constructor
    using keyword arguments with sensible defaults (empty dicts).
    """

    def __init__(
        self,
        *,
        graphite_urls: dict[str, str] | None = None,
    ) -> None:
        """Create FakeGraphiteOps with pre-configured state.

        Args:
            graphite_urls: Mapping of branch name -> Graphite PR URL
        """
        self._graphite_urls = graphite_urls or {}

    def get_graphite_url(self, repo_root: Path, branch: str, pr_number: int) -> str | None:
        """Get Graphite PR URL (returns pre-configured data)."""
        return self._graphite_urls.get(branch)
