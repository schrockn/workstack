"""Stack exec subcommand for parallel execution across worktrees."""

import asyncio
import subprocess
from pathlib import Path

import click

from workstack.cli.commands.stack import stack_group
from workstack.cli.output.stack_formatter import OutputMode, StackOutputFormatter
from workstack.core.context import WorkstackContext
from workstack.core.execution_result import ExecutionResult
from workstack.core.parallel_executor import ParallelExecutor
from workstack.core.stack_ops import GraphiteStackOps


@stack_group.command("exec")
@click.argument("command", required=True)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["summary", "streaming", "quiet"]),
    default="summary",
    help="Output mode (default: summary)",
)
@click.option(
    "--stop-on-failure",
    "-s",
    is_flag=True,
    help="Stop execution when first failure occurs",
)
@click.option(
    "--timeout",
    "-t",
    type=int,
    help="Timeout in seconds per worktree",
)
@click.option(
    "--max-parallel",
    "-p",
    type=int,
    help="Maximum parallel executions (default: unlimited)",
)
@click.pass_obj
def exec_command(
    ctx: WorkstackContext,
    command: str,
    output: str,
    stop_on_failure: bool,
    timeout: int | None,
    max_parallel: int | None,
) -> None:
    """Execute COMMAND in all worktrees in the current stack.

    Uses Graphite to detect the current stack and executes the command
    in parallel across all worktrees in the stack.

    Examples:

        # Run tests in all stack worktrees
        workstack stack exec "pytest"

        # Build with streaming output
        workstack stack exec "npm run build" --output streaming

        # Run with timeout
        workstack stack exec "make test" --timeout 300
    """
    current_dir = Path.cwd()
    output_mode: OutputMode = output  # type: ignore[assignment]
    formatter = StackOutputFormatter(mode=output_mode)

    stack_ops = GraphiteStackOps()

    try:
        worktrees = stack_ops.get_stack_worktrees(ctx.git_ops, current_dir)
    except subprocess.CalledProcessError as e:
        formatter.show_error(
            "Failed to detect stack. Are you in a Graphite repository with a stack?"
        )
        raise SystemExit(1) from e

    if not worktrees:
        formatter.show_error(
            "No worktrees found in current stack. "
            "Make sure you're in a worktree that's part of a Graphite stack."
        )
        raise SystemExit(1)

    executor = ParallelExecutor()

    results: list[ExecutionResult] = []

    progress = formatter.show_progress(command, len(worktrees))

    if progress is not None:
        with progress:
            task_ids: dict[str, int] = {}
            for wt in worktrees:
                task_id = progress.add_task(f"{wt.path.name}", total=None)
                task_ids[wt.path.name] = task_id

            results = asyncio.run(
                executor.execute_all(
                    worktrees,
                    command,
                    stop_on_failure=stop_on_failure,
                    max_parallel=max_parallel,
                    timeout=timeout,
                )
            )
    else:
        results = asyncio.run(
            executor.execute_all(
                worktrees,
                command,
                stop_on_failure=stop_on_failure,
                max_parallel=max_parallel,
                timeout=timeout,
            )
        )

        for result in results:
            formatter.show_streaming_result(result)

    formatter.show_final_results(results)

    failed_count = sum(1 for r in results if not r.succeeded)
    if failed_count > 0:
        raise SystemExit(failed_count)
