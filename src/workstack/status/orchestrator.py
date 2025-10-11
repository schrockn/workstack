"""Orchestrator for collecting and assembling status information."""

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from pathlib import Path

from workstack.core.context import WorkstackContext
from workstack.status.collectors.base import StatusCollector
from workstack.status.models.status_data import StatusData, WorktreeInfo

logger = logging.getLogger(__name__)


class StatusOrchestrator:
    """Coordinates all status collectors and assembles final data.

    The orchestrator runs collectors in parallel with timeouts to ensure
    responsive output even if some collectors are slow or fail.
    """

    def __init__(self, collectors: list[StatusCollector], *, timeout_seconds: float = 2.0) -> None:
        """Create a status orchestrator.

        Args:
            collectors: List of status collectors to run
            timeout_seconds: Maximum time to wait for each collector (default: 2.0)
        """
        self.collectors = collectors
        self.timeout_seconds = timeout_seconds

    def collect_status(
        self, ctx: WorkstackContext, worktree_path: Path, repo_root: Path
    ) -> StatusData:
        """Collect all status information in parallel.

        Each collector runs in its own thread with a timeout. Failed or slow
        collectors will return None for their section.

        Args:
            ctx: Workstack context with operations
            worktree_path: Path to the worktree
            repo_root: Path to repository root

        Returns:
            StatusData with all collected information
        """
        # Determine worktree info
        worktree_info = self._get_worktree_info(ctx, worktree_path, repo_root)

        # Run collectors in parallel
        results: dict[str, object] = {}

        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all available collectors
            futures = {}
            for collector in self.collectors:
                if collector.is_available(ctx, worktree_path):
                    future = executor.submit(collector.collect, ctx, worktree_path, repo_root)
                    futures[future] = collector.name

            # Collect results with timeout per collector
            # Use a separate timeout for as_completed (total time for all collectors)
            total_timeout = self.timeout_seconds * len(futures) if futures else 1.0

            try:
                for future in as_completed(futures, timeout=total_timeout):
                    collector_name = futures[future]
                    try:
                        result = future.result(timeout=0.1)  # Should be immediate once complete
                        results[collector_name] = result
                    except TimeoutError:
                        # Error boundary: Collector timeouts shouldn't fail entire command
                        # Log for debugging but continue with other collectors
                        logger.debug(
                            f"Collector '{collector_name}' timed out after {self.timeout_seconds}s"
                        )
                        results[collector_name] = None
                    except Exception as e:
                        # Error boundary: Individual collector failures shouldn't fail
                        # entire command. This is an acceptable use of exception handling
                        # at error boundaries per EXCEPTION_HANDLING.md - parallel
                        # collectors should degrade gracefully
                        logger.debug(f"Collector '{collector_name}' failed: {e}")
                        results[collector_name] = None
            except TimeoutError:
                # Some collectors didn't complete in time
                # Mark incomplete collectors as None
                for future, collector_name in futures.items():
                    if future.running() or not future.done():
                        logger.debug(f"Collector '{collector_name}' did not complete in time")
                        results[collector_name] = None

        # Get related worktrees
        related_worktrees = self._get_related_worktrees(ctx, repo_root, worktree_path)

        # Assemble StatusData - cast results to expected types
        # Results are either the correct type or None (from collector failures)
        from workstack.status.models.status_data import (
            DependencyStatus,
            EnvironmentStatus,
            GitStatus,
            PlanStatus,
            PullRequestStatus,
            StackPosition,
        )

        git_result = results.get("git")
        stack_result = results.get("stack")
        pr_result = results.get("pr")
        env_result = results.get("environment")
        deps_result = results.get("dependencies")
        plan_result = results.get("plan")

        return StatusData(
            worktree_info=worktree_info,
            git_status=git_result if isinstance(git_result, GitStatus) else None,
            stack_position=stack_result if isinstance(stack_result, StackPosition) else None,
            pr_status=pr_result if isinstance(pr_result, PullRequestStatus) else None,
            environment=env_result if isinstance(env_result, EnvironmentStatus) else None,
            dependencies=deps_result if isinstance(deps_result, DependencyStatus) else None,
            plan=plan_result if isinstance(plan_result, PlanStatus) else None,
            related_worktrees=related_worktrees,
        )

    def _get_worktree_info(
        self, ctx: WorkstackContext, worktree_path: Path, repo_root: Path
    ) -> WorktreeInfo:
        """Get basic worktree information.

        Args:
            ctx: Workstack context
            worktree_path: Path to worktree
            repo_root: Path to repository root

        Returns:
            WorktreeInfo with basic information
        """
        # Check paths exist before resolution to avoid OSError
        is_root = False
        if worktree_path.exists() and repo_root.exists():
            is_root = worktree_path.resolve() == repo_root.resolve()

        name = "root" if is_root else worktree_path.name
        branch = ctx.git_ops.get_current_branch(worktree_path)

        return WorktreeInfo(name=name, path=worktree_path, branch=branch, is_root=is_root)

    def _get_related_worktrees(
        self, ctx: WorkstackContext, repo_root: Path, current_path: Path
    ) -> list[WorktreeInfo]:
        """Get list of other worktrees in the repository.

        Args:
            ctx: Workstack context
            repo_root: Path to repository root
            current_path: Path to current worktree (excluded from results)

        Returns:
            List of WorktreeInfo for other worktrees
        """
        worktrees = ctx.git_ops.list_worktrees(repo_root)

        # Check paths exist before resolution to avoid OSError
        if not current_path.exists():
            return []

        current_resolved = current_path.resolve()

        related = []
        for wt in worktrees:
            # Skip if worktree path doesn't exist
            if not wt.path.exists():
                continue

            wt_resolved = wt.path.resolve()

            # Skip current worktree
            if wt_resolved == current_resolved:
                continue

            # Determine if this is the root worktree
            is_root = False
            if repo_root.exists():
                is_root = wt_resolved == repo_root.resolve()

            name = "root" if is_root else wt.path.name

            related.append(WorktreeInfo(name=name, path=wt.path, branch=wt.branch, is_root=is_root))

        return related
