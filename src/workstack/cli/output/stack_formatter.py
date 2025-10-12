"""Rich-based output formatting for stack exec command."""

from typing import Literal

import click
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from workstack.core.execution_result import ExecutionResult

OutputMode = Literal["summary", "streaming", "quiet"]


class StackOutputFormatter:
    """Formats execution results using Rich library for beautiful output.

    Supports three output modes:
    - summary: Progress bars with final results table
    - streaming: Live prefixed output as commands complete
    - quiet: Only exit codes
    """

    def __init__(self, mode: OutputMode, console: Console | None = None) -> None:
        """Initialize formatter with output mode.

        Args:
            mode: Output mode (summary, streaming, or quiet)
            console: Rich Console instance (None creates default)
        """
        self.mode = mode
        self.console = console or Console()

    def show_progress(self, command: str, num_worktrees: int) -> Progress | None:
        """Display progress UI during execution (summary mode only).

        Args:
            command: Command being executed
            num_worktrees: Number of worktrees

        Returns:
            Rich Progress instance if in summary mode, None otherwise
        """
        if self.mode != "summary":
            return None

        self.console.print(f"[bold]Executing:[/bold] {command}")
        self.console.print("─" * 40)

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=self.console,
        )

        return progress

    def update_progress(self, progress: Progress | None, task_id: TaskID, description: str) -> None:
        """Update progress task description.

        Args:
            progress: Progress instance (None is ignored)
            task_id: Task ID to update
            description: New description
        """
        if progress is not None:
            progress.update(task_id, description=description)

    def show_streaming_result(self, result: ExecutionResult) -> None:
        """Show result in streaming mode.

        Args:
            result: Execution result to display
        """
        if self.mode != "streaming":
            return

        prefix = f"[{result.worktree_name}]"
        status = "✓" if result.succeeded else "✗"
        self.console.print(
            f"{prefix} {status} Complete ({result.duration:.1f}s)",
            style="green" if result.succeeded else "red",
        )

    def show_final_results(self, results: list[ExecutionResult]) -> None:
        """Show final results summary.

        Args:
            results: List of all execution results
        """
        if self.mode == "quiet":
            self._show_quiet_results(results)
        elif self.mode == "summary":
            self._show_summary_results(results)
        elif self.mode == "streaming":
            pass

    def _show_quiet_results(self, results: list[ExecutionResult]) -> None:
        """Show minimal output (exit codes only).

        Args:
            results: Execution results
        """
        for result in results:
            click.echo(f"{result.worktree_name}: {result.exit_code}")

    def _show_summary_results(self, results: list[ExecutionResult]) -> None:
        """Show rich formatted summary with results table.

        Args:
            results: Execution results
        """
        self.console.print()
        self.console.print("[bold]Results[/bold]")
        self.console.print("─" * 40)

        table = Table(show_header=False, box=None)
        table.add_column("Status", style="bold")
        table.add_column("Worktree")
        table.add_column("Info", style="dim")

        for result in results:
            if result.succeeded:
                status = "✓"
                style = "green"
                info = f"({result.duration:.1f}s)"
            elif result.timed_out:
                status = "✗"
                style = "red"
                info = "TIMEOUT"
            else:
                status = "✗"
                style = "red"
                info = f"exit {result.exit_code} ({result.duration:.1f}s)"

            table.add_row(
                f"[{style}]{status}[/{style}]",
                result.worktree_name,
                info,
            )

        self.console.print(table)

        succeeded = sum(1 for r in results if r.succeeded)
        total = len(results)
        total_time = max((r.duration for r in results), default=0.0)

        if succeeded == total:
            style = "green"
        else:
            style = "red"

        self.console.print()
        self.console.print(
            f"[{style}]Total: {succeeded}/{total} succeeded • {total_time:.1f}s[/{style}]"
        )

    def show_error(self, message: str) -> None:
        """Show error message in appropriate format for mode.

        Args:
            message: Error message to display
        """
        click.echo(f"Error: {message}" if self.mode == "quiet" else message, err=True)
