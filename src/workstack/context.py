"""Application context with dependency injection."""

from dataclasses import dataclass

from workstack.github_ops import GitHubOps, RealGitHubOps
from workstack.gitops import DryRunGitOps, GitOps, RealGitOps
from workstack.global_config_ops import GlobalConfigOps, RealGlobalConfigOps
from workstack.graphite_ops import DryRunGraphiteOps, GraphiteOps, RealGraphiteOps


@dataclass(frozen=True)
class WorkstackContext:
    """Immutable context holding all dependencies for workstack operations.

    Created at CLI entry point and threaded through the application.
    Frozen to prevent accidental modification at runtime.
    """

    git_ops: GitOps
    global_config_ops: GlobalConfigOps
    github_ops: GitHubOps
    graphite_ops: GraphiteOps
    dry_run: bool


def create_context(*, dry_run: bool) -> WorkstackContext:
    """Create production context with real implementations.

    Called at CLI entry point to create the context for the entire
    command execution.

    Args:
        dry_run: If True, wrap GitOps/GraphiteOps with dry-run wrappers

    Returns:
        WorkstackContext with real implementations (RealGitOps, RealGlobalConfigOps, etc.)

    Example:
        >>> ctx = create_context()
        >>> worktrees = ctx.git_ops.list_worktrees(Path("/repo"))
        >>> workstacks_root = ctx.global_config_ops.get_workstacks_root()
    """
    git_ops: GitOps = RealGitOps()
    graphite_ops: GraphiteOps = RealGraphiteOps()

    if dry_run:
        git_ops = DryRunGitOps(git_ops)
        graphite_ops = DryRunGraphiteOps(graphite_ops)

    return WorkstackContext(
        git_ops=git_ops,
        global_config_ops=RealGlobalConfigOps(),
        github_ops=RealGitHubOps(),
        graphite_ops=graphite_ops,
        dry_run=dry_run,
    )
