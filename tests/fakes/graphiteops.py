"""Fake Graphite operations for testing.

FakeGraphiteOps is an in-memory implementation that constructs Graphite URLs
directly from owner/repo/pr_number, matching the real implementation.
"""

from pathlib import Path

from workstack.graphiteops import GraphiteOps


class FakeGraphiteOps(GraphiteOps):
    """In-memory fake implementation of Graphite operations.

    Constructs Graphite URLs using the same pattern as RealGraphiteOps.
    """

    def get_graphite_url(self, owner: str, repo: str, pr_number: int) -> str:
        """Get Graphite PR URL (constructs URL directly)."""
        return f"https://app.graphite.dev/github/pr/{owner}/{repo}/{pr_number}"

    def sync(self, repo_root: Path, *, force: bool) -> None:
        """Fake sync operation (no-op in tests)."""
        pass
