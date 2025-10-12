"""Tests for ParallelExecutor."""

from pathlib import Path

import pytest

from workstack.core.gitops import WorktreeInfo
from workstack.core.parallel_executor import ParallelExecutor


@pytest.mark.asyncio
async def test_execute_simple_command(tmp_path: Path) -> None:
    """Test basic command execution in a worktree."""
    worktree_path = tmp_path / "test-worktree"
    worktree_path.mkdir()

    worktree = WorktreeInfo(path=worktree_path, branch="main")
    executor = ParallelExecutor()

    result = await executor.execute_in_worktree(worktree, "echo hello", timeout=None)

    assert result.exit_code == 0
    assert "hello" in result.stdout
    assert result.worktree_name == "test-worktree"
    assert result.branch == "main"
    assert not result.timed_out


@pytest.mark.asyncio
async def test_execute_with_timeout(tmp_path: Path) -> None:
    """Test timeout handling."""
    worktree_path = tmp_path / "test-worktree"
    worktree_path.mkdir()

    worktree = WorktreeInfo(path=worktree_path, branch="main")
    executor = ParallelExecutor()

    result = await executor.execute_in_worktree(worktree, "sleep 10", timeout=1)

    assert result.timed_out is True
    assert result.exit_code == -9


@pytest.mark.asyncio
async def test_execute_all_parallel(tmp_path: Path) -> None:
    """Test parallel execution across multiple worktrees."""
    worktrees = []
    for i in range(3):
        wt_path = tmp_path / f"worktree-{i}"
        wt_path.mkdir()
        worktrees.append(WorktreeInfo(path=wt_path, branch=f"branch-{i}"))

    executor = ParallelExecutor()

    results = await executor.execute_all(worktrees, "echo hello", stop_on_failure=False)

    assert len(results) == 3
    for result in results:
        assert result.exit_code == 0
        assert "hello" in result.stdout


@pytest.mark.asyncio
async def test_execute_all_with_failure(tmp_path: Path) -> None:
    """Test that failures are captured correctly."""
    worktrees = []
    for i in range(3):
        wt_path = tmp_path / f"worktree-{i}"
        wt_path.mkdir()
        worktrees.append(WorktreeInfo(path=wt_path, branch=f"branch-{i}"))

    executor = ParallelExecutor()

    results = await executor.execute_all(worktrees, "exit 1", stop_on_failure=False)

    assert len(results) == 3
    for result in results:
        assert result.exit_code == 1


@pytest.mark.asyncio
async def test_execute_all_stop_on_failure(tmp_path: Path) -> None:
    """Test stop-on-failure behavior."""
    worktrees = []
    for i in range(5):
        wt_path = tmp_path / f"worktree-{i}"
        wt_path.mkdir()
        worktrees.append(WorktreeInfo(path=wt_path, branch=f"branch-{i}"))

    executor = ParallelExecutor()

    results = await executor.execute_all(worktrees, "sleep 0.1 && exit 1", stop_on_failure=True)

    assert len(results) <= 5
    assert any(not r.succeeded for r in results)


@pytest.mark.asyncio
async def test_execute_all_max_parallel(tmp_path: Path) -> None:
    """Test max parallel execution limit."""
    worktrees = []
    for i in range(5):
        wt_path = tmp_path / f"worktree-{i}"
        wt_path.mkdir()
        worktrees.append(WorktreeInfo(path=wt_path, branch=f"branch-{i}"))

    executor = ParallelExecutor()

    results = await executor.execute_all(
        worktrees, "echo hello", stop_on_failure=False, max_parallel=2
    )

    assert len(results) == 5
    for result in results:
        assert result.exit_code == 0


@pytest.mark.asyncio
async def test_execute_empty_worktrees() -> None:
    """Test execution with no worktrees."""
    executor = ParallelExecutor()
    results = await executor.execute_all([], "echo hello", stop_on_failure=False)
    assert results == []
