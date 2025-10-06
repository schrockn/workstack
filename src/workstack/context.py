"""Application context with dependency injection."""

from dataclasses import dataclass

from workstack.gitops import GitOps, RealGitOps


@dataclass(frozen=True)
class WorkstackContext:
    """Immutable context holding all dependencies for workstack operations.

    Created at CLI entry point and threaded through the application.
    Frozen to prevent accidental modification at runtime.
    """

    git_ops: GitOps


def create_context() -> WorkstackContext:
    """Create production context with real implementations.

    Called at CLI entry point to create the context for the entire
    command execution.

    Returns:
        WorkstackContext with real implementations (RealGitOps, etc.)

    Example:
        >>> ctx = create_context()
        >>> worktrees = ctx.git_ops.list_worktrees(Path("/repo"))
    """
    return WorkstackContext(git_ops=RealGitOps())
