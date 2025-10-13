"""Execution result data models for stack exec operations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionResult:
    """Result of executing a command in a worktree.

    Attributes:
        worktree_name: Name of the worktree (e.g., "backend-feature")
        branch: Branch name (e.g., "feature/auth")
        exit_code: Process exit code (0 = success)
        duration: Execution time in seconds
        stdout: Captured standard output
        stderr: Captured standard error
        timed_out: True if execution was terminated due to timeout
    """

    worktree_name: str
    branch: str | None
    exit_code: int
    duration: float
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def succeeded(self) -> bool:
        """Check if command succeeded (exit code 0 and no timeout)."""
        return self.exit_code == 0 and not self.timed_out
