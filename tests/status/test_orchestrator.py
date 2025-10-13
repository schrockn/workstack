"""Unit tests for StatusOrchestrator."""

from pathlib import Path

from tests.fakes.context import create_test_context
from workstack.status.collectors.base import StatusCollector
from workstack.status.collectors.git import GitStatusCollector
from workstack.status.collectors.plan import PlanFileCollector
from workstack.status.orchestrator import StatusOrchestrator


def test_orchestrator_collects_all_data(tmp_path: Path) -> None:
    """Test StatusOrchestrator collects data from all collectors."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    # Create a plan file
    (worktree_path / ".PLAN.md").write_text("# Test Plan", encoding="utf-8")

    collectors = [
        GitStatusCollector(),
        PlanFileCollector(),
    ]

    orchestrator = StatusOrchestrator(collectors)
    status = orchestrator.collect_status(ctx, worktree_path, tmp_path)

    assert status is not None
    assert status.worktree_info is not None
    assert status.worktree_info.path == worktree_path
    # Plan should be collected
    assert status.plan is not None
    assert status.plan.exists is True


def test_orchestrator_with_no_collectors(tmp_path: Path) -> None:
    """Test StatusOrchestrator with no collectors."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    orchestrator = StatusOrchestrator([])
    status = orchestrator.collect_status(ctx, worktree_path, tmp_path)

    assert status is not None
    assert status.worktree_info is not None
    assert status.git_status is None
    assert status.plan is None


def test_orchestrator_handles_missing_plan(tmp_path: Path) -> None:
    """Test StatusOrchestrator when plan file doesn't exist."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    collectors: list[StatusCollector] = [PlanFileCollector()]

    orchestrator = StatusOrchestrator(collectors)
    status = orchestrator.collect_status(ctx, worktree_path, tmp_path)

    assert status is not None
    # Plan collector is not available (is_available returns False)
    # so plan should be None
    assert status.plan is None
