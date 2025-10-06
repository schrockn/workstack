"""Factory functions for creating test contexts."""

from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from workstack.context import WorkstackContext


def create_test_context(
    git_ops: FakeGitOps | None = None,
    global_config_ops: FakeGlobalConfigOps | None = None,
) -> WorkstackContext:
    """Create test context with optional pre-configured git ops and config ops.

    Args:
        git_ops: Optional FakeGitOps with test configuration.
                If None, creates empty FakeGitOps.
        global_config_ops: Optional FakeGlobalConfigOps with test configuration.
                          If None, creates FakeGlobalConfigOps with no config (doesn't exist).

    Returns:
        Frozen WorkstackContext for use in tests

    Example:
        # With pre-configured git ops
        >>> git_ops = FakeGitOps(default_branches={Path("/repo"): "main"})
        >>> ctx = create_test_context(git_ops=git_ops)

        # With pre-configured global config
        >>> from workstack.config import GlobalConfig
        >>> config_ops = FakeGlobalConfigOps(
        ...     config=GlobalConfig(
        ...         workstacks_root=Path("/tmp/workstacks"),
        ...         use_graphite=False,
        ...         shell_setup_complete=False,
        ...     )
        ... )
        >>> ctx = create_test_context(global_config_ops=config_ops)

        # Without any ops (empty fakes)
        >>> ctx = create_test_context()
    """
    if git_ops is None:
        git_ops = FakeGitOps()

    if global_config_ops is None:
        global_config_ops = FakeGlobalConfigOps()

    return WorkstackContext(git_ops=git_ops, global_config_ops=global_config_ops)
