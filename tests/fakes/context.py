"""Factory functions for creating test contexts."""

from tests.builders.gitops import GitOpsBuilder
from workstack.context import WorkstackContext


def create_test_context(git_ops_builder: GitOpsBuilder | None = None) -> WorkstackContext:
    """Create test context with optional pre-configured builder.

    Args:
        git_ops_builder: Optional GitOpsBuilder with test configuration.
                        If None, creates empty FakeGitOps.

    Returns:
        Frozen WorkstackContext for use in tests

    Example:
        # With builder
        >>> builder = GitOpsBuilder().with_default_branch(Path("/repo"), "main")
        >>> ctx = create_test_context(builder)

        # Without builder (empty fake)
        >>> ctx = create_test_context()
    """
    if git_ops_builder is None:
        git_ops_builder = GitOpsBuilder()

    return WorkstackContext(git_ops=git_ops_builder.build())
