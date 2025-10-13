"""Parallel command execution across worktrees using asyncio."""

import asyncio
import time

from workstack.core.execution_result import ExecutionResult
from workstack.core.gitops import WorktreeInfo


class ParallelExecutor:
    """Executes shell commands in parallel across multiple worktrees.

    Uses asyncio for concurrent subprocess execution, ensuring clean output
    buffering and proper timeout handling.
    """

    async def execute_in_worktree(
        self,
        worktree: WorktreeInfo,
        command: str,
        timeout: int | None = None,
    ) -> ExecutionResult:
        """Execute command in a single worktree.

        Args:
            worktree: Worktree information
            command: Shell command to execute
            timeout: Optional timeout in seconds

        Returns:
            ExecutionResult with command output and status
        """
        start_time = time.time()
        worktree_name = worktree.path.name

        process = await asyncio.create_subprocess_shell(
            command,
            cwd=worktree.path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_bytes = b""
        stderr_bytes = b""
        timed_out = False

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            timed_out = True

        duration = time.time() - start_time

        return ExecutionResult(
            worktree_name=worktree_name,
            branch=worktree.branch,
            exit_code=process.returncode if process.returncode is not None else -1,
            duration=duration,
            stdout=stdout_bytes.decode("utf-8", errors="replace"),
            stderr=stderr_bytes.decode("utf-8", errors="replace"),
            timed_out=timed_out,
        )

    async def execute_all(
        self,
        worktrees: list[WorktreeInfo],
        command: str,
        stop_on_failure: bool = False,
        max_parallel: int | None = None,
        timeout: int | None = None,
    ) -> list[ExecutionResult]:
        """Execute command across all worktrees in parallel.

        Args:
            worktrees: List of worktrees to execute in
            command: Shell command to execute
            stop_on_failure: If True, stop execution when first failure occurs
            max_parallel: Maximum concurrent executions (None = unlimited)
            timeout: Optional timeout per worktree in seconds

        Returns:
            List of ExecutionResult, one per worktree
        """
        if not worktrees:
            return []

        semaphore = asyncio.Semaphore(max_parallel or len(worktrees))

        async def execute_with_limit(wt: WorktreeInfo) -> ExecutionResult:
            async with semaphore:
                return await self.execute_in_worktree(wt, command, timeout)

        tasks = [asyncio.create_task(execute_with_limit(wt)) for wt in worktrees]

        if stop_on_failure:
            results: list[ExecutionResult] = []
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
                if not result.succeeded:
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    break

            await asyncio.gather(*tasks, return_exceptions=True)
            return results
        else:
            return await asyncio.gather(*tasks)
