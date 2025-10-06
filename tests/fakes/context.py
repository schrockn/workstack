"""Factory functions for creating test contexts."""

from tests.fakes.gitops import FakeGitOps
from workstack.context import WorkstackContext


def create_test_context(git_ops: FakeGitOps | None = None) -> WorkstackContext:
    """Create test context with optional pre-configured git ops.

    Args:
        git_ops: Optional FakeGitOps with test configuration.
                If None, creates empty FakeGitOps.

    Returns:
        Frozen WorkstackContext for use in tests

    Example:
        # With pre-configured git ops
        >>> git_ops = FakeGitOps(default_branches={Path("/repo"): "main"})
        >>> ctx = create_test_context(git_ops)

        # Without git ops (empty fake)
        >>> ctx = create_test_context()
    """
    if git_ops is None:
        git_ops = FakeGitOps()

    return WorkstackContext(git_ops=git_ops)
