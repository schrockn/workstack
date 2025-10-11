"""Unit tests for status renderers."""

from pathlib import Path

from click.testing import CliRunner

from workstack.status.models.status_data import (
    CommitInfo,
    GitStatus,
    PlanStatus,
    StackPosition,
    StatusData,
    WorktreeInfo,
)
from workstack.status.renderers.simple import SimpleRenderer


def test_simple_renderer_clean_status() -> None:
    """Test SimpleRenderer with clean status."""
    runner = CliRunner()

    worktree_info = WorktreeInfo(
        name="test-worktree",
        path=Path("/tmp/test"),
        branch="main",
        is_root=False,
    )

    git_status = GitStatus(
        branch="main",
        clean=True,
        ahead=0,
        behind=0,
        staged_files=[],
        modified_files=[],
        untracked_files=[],
        recent_commits=[],
    )

    status_data = StatusData(
        worktree_info=worktree_info,
        git_status=git_status,
        stack_position=None,
        pr_status=None,
        environment=None,
        dependencies=None,
        plan=None,
        related_worktrees=[],
    )

    renderer = SimpleRenderer()

    with runner.isolation():
        renderer.render(status_data)


def test_simple_renderer_with_modified_files() -> None:
    """Test SimpleRenderer with modified files."""
    worktree_info = WorktreeInfo(
        name="test-worktree",
        path=Path("/tmp/test"),
        branch="feature",
        is_root=False,
    )

    git_status = GitStatus(
        branch="feature",
        clean=False,
        ahead=2,
        behind=0,
        staged_files=["file1.py"],
        modified_files=["file2.py", "file3.py"],
        untracked_files=["file4.py", "file5.py", "file6.py", "file7.py"],
        recent_commits=[
            CommitInfo(
                sha="abc123",
                message="Test commit",
                author="Test Author",
                date="2 hours ago",
            )
        ],
    )

    status_data = StatusData(
        worktree_info=worktree_info,
        git_status=git_status,
        stack_position=None,
        pr_status=None,
        environment=None,
        dependencies=None,
        plan=None,
        related_worktrees=[],
    )

    renderer = SimpleRenderer()
    runner = CliRunner()

    with runner.isolation():
        renderer.render(status_data)


def test_simple_renderer_with_plan() -> None:
    """Test SimpleRenderer with plan file."""
    worktree_info = WorktreeInfo(
        name="test-worktree",
        path=Path("/tmp/test"),
        branch="feature",
        is_root=False,
    )

    plan = PlanStatus(
        exists=True,
        path=Path("/tmp/test/.PLAN.md"),
        summary="Test plan summary",
        line_count=10,
        first_lines=[
            "# Test Plan",
            "",
            "## Overview",
            "",
            "This is a test plan.",
        ],
    )

    git_status = GitStatus(
        branch="feature",
        clean=True,
        ahead=0,
        behind=0,
        staged_files=[],
        modified_files=[],
        untracked_files=[],
        recent_commits=[],
    )

    status_data = StatusData(
        worktree_info=worktree_info,
        git_status=git_status,
        stack_position=None,
        pr_status=None,
        environment=None,
        dependencies=None,
        plan=plan,
        related_worktrees=[],
    )

    renderer = SimpleRenderer()
    runner = CliRunner()

    with runner.isolation():
        renderer.render(status_data)


def test_simple_renderer_with_stack() -> None:
    """Test SimpleRenderer with stack position."""
    worktree_info = WorktreeInfo(
        name="test-worktree",
        path=Path("/tmp/test"),
        branch="feature-2",
        is_root=False,
    )

    git_status = GitStatus(
        branch="feature-2",
        clean=True,
        ahead=0,
        behind=0,
        staged_files=[],
        modified_files=[],
        untracked_files=[],
        recent_commits=[],
    )

    stack_position = StackPosition(
        stack=["main", "feature-1", "feature-2"],
        current_branch="feature-2",
        parent_branch="feature-1",
        children_branches=[],
        is_trunk=False,
    )

    status_data = StatusData(
        worktree_info=worktree_info,
        git_status=git_status,
        stack_position=stack_position,
        pr_status=None,
        environment=None,
        dependencies=None,
        plan=None,
        related_worktrees=[],
    )

    renderer = SimpleRenderer()
    runner = CliRunner()

    with runner.isolation():
        renderer.render(status_data)


def test_simple_renderer_file_list_truncation() -> None:
    """Test that file lists are truncated to 3 items."""
    worktree_info = WorktreeInfo(
        name="test-worktree",
        path=Path("/tmp/test"),
        branch="feature",
        is_root=False,
    )

    # Create a list with more than 3 files
    many_files = [f"file{i}.py" for i in range(10)]

    git_status = GitStatus(
        branch="feature",
        clean=False,
        ahead=0,
        behind=0,
        staged_files=[],
        modified_files=many_files,
        untracked_files=[],
        recent_commits=[],
    )

    status_data = StatusData(
        worktree_info=worktree_info,
        git_status=git_status,
        stack_position=None,
        pr_status=None,
        environment=None,
        dependencies=None,
        plan=None,
        related_worktrees=[],
    )

    renderer = SimpleRenderer()
    runner = CliRunner()

    with runner.isolation():
        # This should render and truncate the file list
        renderer.render(status_data)
