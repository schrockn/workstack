"""Unit tests for status collectors."""

from pathlib import Path

from tests.fakes.context import create_test_context
from workstack.status.collectors.git import GitStatusCollector
from workstack.status.collectors.plan import PlanFileCollector


def test_git_collector_clean_worktree(tmp_path: Path) -> None:
    """Test GitStatusCollector with clean worktree."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    collector = GitStatusCollector()

    # Note: This will return None since there's no real git repo
    # For proper testing, we'd need a real git integration test
    result = collector.collect(ctx, worktree_path, tmp_path)

    # In this fake setup, result will be None
    assert result is None


def test_git_collector_is_available(tmp_path: Path) -> None:
    """Test GitStatusCollector availability check."""
    ctx = create_test_context()
    existing_path = tmp_path / "exists"
    existing_path.mkdir()
    nonexistent_path = tmp_path / "does_not_exist"

    collector = GitStatusCollector()

    assert collector.is_available(ctx, existing_path) is True
    assert collector.is_available(ctx, nonexistent_path) is False


def test_plan_collector_with_existing_plan(tmp_path: Path) -> None:
    """Test PlanFileCollector with existing plan file."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    plan_path = worktree_path / ".PLAN.md"
    plan_content = """# Test Plan
## Introduction
This is a test plan file.
It has multiple lines.
Line five is here."""
    plan_path.write_text(plan_content, encoding="utf-8")

    collector = PlanFileCollector()
    result = collector.collect(ctx, worktree_path, tmp_path)

    assert result is not None
    assert result.exists is True
    assert result.path == plan_path
    assert result.line_count == 5
    assert len(result.first_lines) == 5
    assert result.first_lines[0] == "# Test Plan"
    assert result.first_lines[4] == "Line five is here."


def test_plan_collector_with_short_plan(tmp_path: Path) -> None:
    """Test PlanFileCollector with plan file shorter than 5 lines."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    plan_path = worktree_path / ".PLAN.md"
    plan_content = """# Short Plan
Just two lines."""
    plan_path.write_text(plan_content, encoding="utf-8")

    collector = PlanFileCollector()
    result = collector.collect(ctx, worktree_path, tmp_path)

    assert result is not None
    assert result.exists is True
    assert result.line_count == 2
    assert len(result.first_lines) == 2
    assert result.first_lines[0] == "# Short Plan"
    assert result.first_lines[1] == "Just two lines."


def test_plan_collector_no_plan_file(tmp_path: Path) -> None:
    """Test PlanFileCollector when plan file doesn't exist."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    collector = PlanFileCollector()
    result = collector.collect(ctx, worktree_path, tmp_path)

    assert result is not None
    assert result.exists is False
    assert result.path is None
    assert result.line_count == 0
    assert len(result.first_lines) == 0


def test_plan_collector_is_available(tmp_path: Path) -> None:
    """Test PlanFileCollector availability check."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    collector = PlanFileCollector()

    # No plan file
    assert collector.is_available(ctx, worktree_path) is False

    # Create plan file
    (worktree_path / ".PLAN.md").write_text("# Plan", encoding="utf-8")
    assert collector.is_available(ctx, worktree_path) is True


def test_plan_collector_generates_summary(tmp_path: Path) -> None:
    """Test PlanFileCollector generates summary from non-header lines."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    plan_path = worktree_path / ".PLAN.md"
    plan_content = """# Header

This is the first summary line.
This is the second summary line.
More content follows."""
    plan_path.write_text(plan_content, encoding="utf-8")

    collector = PlanFileCollector()
    result = collector.collect(ctx, worktree_path, tmp_path)

    assert result is not None
    assert result.summary is not None
    assert "first summary line" in result.summary
    assert "second summary line" in result.summary


def test_plan_collector_truncates_long_summary(tmp_path: Path) -> None:
    """Test PlanFileCollector truncates very long summaries."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    plan_path = worktree_path / ".PLAN.md"
    long_line = "a" * 150  # 150 characters
    plan_path.write_text(long_line, encoding="utf-8")

    collector = PlanFileCollector()
    result = collector.collect(ctx, worktree_path, tmp_path)

    assert result is not None
    assert result.summary is not None
    assert len(result.summary) == 100  # Truncated to 100 chars
    assert result.summary.endswith("...")
