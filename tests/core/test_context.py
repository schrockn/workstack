"""Tests for the WorkstackContext."""

from pathlib import Path

from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from tests.fakes.shell_ops import FakeShellOps
from workstack.core.context import WorkstackContext


def test_context_initialization() -> None:
    """Test that WorkstackContext can be initialized with all ops."""
    git_ops = FakeGitOps()
    global_config_ops = FakeGlobalConfigOps(workstacks_root=Path("/tmp"))
    github_ops = FakeGitHubOps()
    graphite_ops = FakeGraphiteOps()

    ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=global_config_ops,
        github_ops=github_ops,
        graphite_ops=graphite_ops,
        shell_ops=FakeShellOps(),
        dry_run=False,
    )

    assert ctx.git_ops is git_ops
    assert ctx.global_config_ops is global_config_ops
    assert ctx.github_ops is github_ops
    assert ctx.graphite_ops is graphite_ops
    assert ctx.dry_run is False


def test_context_frozen_dataclass() -> None:
    """Test that WorkstackContext is frozen (immutable)."""
    ctx = WorkstackContext(
        git_ops=FakeGitOps(),
        global_config_ops=FakeGlobalConfigOps(workstacks_root=Path("/tmp")),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        shell_ops=FakeShellOps(),
        dry_run=False,
    )

    # Attempting to modify should raise
    try:
        ctx.dry_run = True  # type: ignore
        raise AssertionError("Should not be able to modify frozen dataclass")
    except AttributeError:
        pass  # Expected


def test_context_contains_required_fields() -> None:
    """Test that WorkstackContext contains all required fields."""
    ctx = WorkstackContext(
        git_ops=FakeGitOps(),
        global_config_ops=FakeGlobalConfigOps(workstacks_root=Path("/tmp")),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        shell_ops=FakeShellOps(),
        dry_run=True,
    )

    assert hasattr(ctx, "git_ops")
    assert hasattr(ctx, "global_config_ops")
    assert hasattr(ctx, "github_ops")
    assert hasattr(ctx, "graphite_ops")
    assert hasattr(ctx, "dry_run")
