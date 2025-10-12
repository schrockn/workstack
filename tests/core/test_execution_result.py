"""Tests for ExecutionResult data model."""

from workstack.core.execution_result import ExecutionResult


def test_execution_result_succeeded() -> None:
    """Test succeeded property when command succeeds."""
    result = ExecutionResult(
        worktree_name="test-worktree",
        branch="feature/test",
        exit_code=0,
        duration=1.5,
        stdout="output",
        stderr="",
        timed_out=False,
    )
    assert result.succeeded is True


def test_execution_result_failed_nonzero_exit() -> None:
    """Test succeeded property when command fails with non-zero exit code."""
    result = ExecutionResult(
        worktree_name="test-worktree",
        branch="feature/test",
        exit_code=1,
        duration=1.5,
        stdout="output",
        stderr="error",
        timed_out=False,
    )
    assert result.succeeded is False


def test_execution_result_failed_timeout() -> None:
    """Test succeeded property when command times out."""
    result = ExecutionResult(
        worktree_name="test-worktree",
        branch="feature/test",
        exit_code=0,
        duration=1.5,
        stdout="output",
        stderr="",
        timed_out=True,
    )
    assert result.succeeded is False


def test_execution_result_frozen() -> None:
    """Test that ExecutionResult is immutable."""
    result = ExecutionResult(
        worktree_name="test-worktree",
        branch="feature/test",
        exit_code=0,
        duration=1.5,
        stdout="output",
        stderr="",
        timed_out=False,
    )

    try:
        result.exit_code = 1  # type: ignore[misc]
        raise AssertionError("Expected AttributeError")
    except AttributeError:
        pass
