"""Unit tests for GraphiteStackCollector."""

from pathlib import Path

from tests.fakes.context import create_test_context
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from workstack.core.branch_metadata import BranchMetadata
from workstack.status.collectors.graphite import GraphiteStackCollector


def test_graphite_stack_collector_single_branch_no_stack(tmp_path: Path) -> None:
    """Test GraphiteStackCollector with a single branch that's not in a stack."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "standalone-branch"},
    )
    graphite_ops = FakeGraphiteOps(
        stacks={}  # No stacks defined
    )
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)

    ctx = create_test_context(
        git_ops=git_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GraphiteStackCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is None  # Branch not in any stack


def test_graphite_stack_collector_multi_branch_stack(tmp_path: Path) -> None:
    """Test GraphiteStackCollector with a multi-branch stack."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "feature-2"},
    )
    graphite_ops = FakeGraphiteOps(
        stacks={
            "feature-2": ["main", "feature-1", "feature-2", "feature-3"],
        }
    )
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)

    ctx = create_test_context(
        git_ops=git_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GraphiteStackCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.current_branch == "feature-2"
    assert result.stack == ["main", "feature-1", "feature-2", "feature-3"]
    assert result.parent_branch == "feature-1"
    assert result.children_branches == ["feature-3"]
    assert result.is_trunk is False


def test_graphite_stack_collector_current_at_stack_top(tmp_path: Path) -> None:
    """Test GraphiteStackCollector when current branch is at the top of the stack."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "feature-final"},
    )
    graphite_ops = FakeGraphiteOps(
        stacks={
            "feature-final": ["main", "feature-base", "feature-mid", "feature-final"],
        }
    )
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)

    ctx = create_test_context(
        git_ops=git_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GraphiteStackCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.current_branch == "feature-final"
    assert result.parent_branch == "feature-mid"
    assert result.children_branches == []  # No children at the top
    assert result.is_trunk is False


def test_graphite_stack_collector_current_at_stack_middle(tmp_path: Path) -> None:
    """Test GraphiteStackCollector when current branch is in the middle of the stack."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "feature-middle"},
    )
    graphite_ops = FakeGraphiteOps(
        stacks={
            "feature-middle": ["main", "feature-bottom", "feature-middle", "feature-top"],
        }
    )
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)

    ctx = create_test_context(
        git_ops=git_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GraphiteStackCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.current_branch == "feature-middle"
    assert result.parent_branch == "feature-bottom"
    assert result.children_branches == ["feature-top"]
    assert result.is_trunk is False


def test_graphite_stack_collector_current_at_stack_bottom(tmp_path: Path) -> None:
    """Test GraphiteStackCollector when current branch is at the bottom of the stack."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "main"},
    )
    graphite_ops = FakeGraphiteOps(
        stacks={
            "main": ["main", "feature-1", "feature-2"],
        }
    )
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)

    ctx = create_test_context(
        git_ops=git_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GraphiteStackCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.current_branch == "main"
    assert result.parent_branch is None  # Trunk has no parent
    assert result.children_branches == ["feature-1"]
    assert result.is_trunk is True  # Main is the trunk


def test_graphite_stack_collector_stack_with_prs(tmp_path: Path) -> None:
    """Test GraphiteStackCollector with a stack that has PRs.

    Note: The collector doesn't check PRs directly.
    """
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "pr-branch"},
    )
    # The collector only cares about the stack structure, not PRs
    graphite_ops = FakeGraphiteOps(
        stacks={
            "pr-branch": ["main", "pr-branch", "next-branch"],
        }
    )
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)

    ctx = create_test_context(
        git_ops=git_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GraphiteStackCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.current_branch == "pr-branch"
    assert result.parent_branch == "main"
    assert result.children_branches == ["next-branch"]


def test_graphite_stack_collector_stack_with_mixed_pr_states(tmp_path: Path) -> None:
    """Test GraphiteStackCollector with different PR states (collector ignores PR state)."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "middle"},
    )
    graphite_ops = FakeGraphiteOps(
        stacks={
            "middle": ["main", "merged-branch", "middle", "open-branch"],
        }
    )
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)

    ctx = create_test_context(
        git_ops=git_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GraphiteStackCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.current_branch == "middle"
    assert result.stack == ["main", "merged-branch", "middle", "open-branch"]


def test_graphite_stack_collector_orphaned_branch(tmp_path: Path) -> None:
    """Test GraphiteStackCollector with an orphaned branch (not in any stack)."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "orphaned"},
    )
    graphite_ops = FakeGraphiteOps(
        stacks={
            "other-branch": ["main", "other-branch", "another-branch"],
        }
        # "orphaned" is not in any stack
    )
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)

    ctx = create_test_context(
        git_ops=git_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GraphiteStackCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is None  # Orphaned branch has no stack


def test_graphite_stack_collector_non_graphite_repo(tmp_path: Path) -> None:
    """Test GraphiteStackCollector when Graphite is disabled."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    git_ops = FakeGitOps(
        current_branches={worktree_path: "branch"},
    )
    graphite_ops = FakeGraphiteOps()
    global_config_ops = FakeGlobalConfigOps(use_graphite=False)  # Graphite disabled

    ctx = create_test_context(
        git_ops=git_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GraphiteStackCollector()

    # Act
    available = collector.is_available(ctx, worktree_path)

    # Assert
    assert available is False  # Not available when Graphite is disabled


def test_graphite_stack_collector_handles_gt_errors(tmp_path: Path) -> None:
    """Test GraphiteStackCollector handles gt command errors gracefully."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "error-branch"},
    )
    # Empty stacks simulates gt error or no Graphite data
    graphite_ops = FakeGraphiteOps(stacks={})
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)

    ctx = create_test_context(
        git_ops=git_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GraphiteStackCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is None  # Handles missing data gracefully


def test_graphite_stack_collector_is_available_path_not_exists(tmp_path: Path) -> None:
    """Test GraphiteStackCollector availability when worktree path doesn't exist."""
    # Arrange
    nonexistent_path = tmp_path / "does_not_exist"

    global_config_ops = FakeGlobalConfigOps(use_graphite=True)
    ctx = create_test_context(global_config_ops=global_config_ops)
    collector = GraphiteStackCollector()

    # Act
    available = collector.is_available(ctx, nonexistent_path)

    # Assert
    assert available is False


def test_graphite_stack_collector_is_available_enabled(tmp_path: Path) -> None:
    """Test GraphiteStackCollector availability when properly configured."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    global_config_ops = FakeGlobalConfigOps(use_graphite=True)
    ctx = create_test_context(global_config_ops=global_config_ops)
    collector = GraphiteStackCollector()

    # Act
    available = collector.is_available(ctx, worktree_path)

    # Assert
    assert available is True


def test_graphite_stack_collector_detached_head(tmp_path: Path) -> None:
    """Test GraphiteStackCollector when in detached HEAD state."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: None},  # Detached HEAD
    )
    graphite_ops = FakeGraphiteOps()
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)

    ctx = create_test_context(
        git_ops=git_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GraphiteStackCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is None  # No branch means no stack


def test_graphite_stack_collector_using_branch_metadata(tmp_path: Path) -> None:
    """Test GraphiteStackCollector building stack from BranchMetadata."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "feature-2"},
    )

    # Use BranchMetadata instead of direct stacks
    branches = {
        "main": BranchMetadata(
            name="main",
            parent=None,
            children=["feature-1"],
            is_trunk=True,
            commit_sha="abc123",
        ),
        "feature-1": BranchMetadata(
            name="feature-1",
            parent="main",
            children=["feature-2"],
            is_trunk=False,
            commit_sha="def456",
        ),
        "feature-2": BranchMetadata(
            name="feature-2",
            parent="feature-1",
            children=["feature-3"],
            is_trunk=False,
            commit_sha="ghi789",
        ),
        "feature-3": BranchMetadata(
            name="feature-3",
            parent="feature-2",
            children=[],
            is_trunk=False,
            commit_sha="jkl012",
        ),
    }

    graphite_ops = FakeGraphiteOps(branches=branches)
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)

    ctx = create_test_context(
        git_ops=git_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GraphiteStackCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.current_branch == "feature-2"
    assert result.stack == ["main", "feature-1", "feature-2", "feature-3"]
    assert result.parent_branch == "feature-1"
    assert result.children_branches == ["feature-3"]
    assert result.is_trunk is False


def test_graphite_stack_collector_complex_tree_structure(tmp_path: Path) -> None:
    """Test GraphiteStackCollector with a branching tree (follows first child only)."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "branch-a"},
    )

    # Complex tree with multiple children
    branches = {
        "main": BranchMetadata(
            name="main",
            parent=None,
            children=["branch-a", "branch-x"],  # Two children
            is_trunk=True,
            commit_sha="abc123",
        ),
        "branch-a": BranchMetadata(
            name="branch-a",
            parent="main",
            children=["branch-b"],
            is_trunk=False,
            commit_sha="def456",
        ),
        "branch-b": BranchMetadata(
            name="branch-b",
            parent="branch-a",
            children=[],
            is_trunk=False,
            commit_sha="ghi789",
        ),
        "branch-x": BranchMetadata(
            name="branch-x",
            parent="main",
            children=[],
            is_trunk=False,
            commit_sha="xyz999",
        ),
    }

    graphite_ops = FakeGraphiteOps(branches=branches)
    global_config_ops = FakeGlobalConfigOps(use_graphite=True)

    ctx = create_test_context(
        git_ops=git_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GraphiteStackCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.current_branch == "branch-a"
    # Should follow the linear stack through branch-a, not include branch-x
    assert result.stack == ["main", "branch-a", "branch-b"]
    assert result.parent_branch == "main"
    assert result.children_branches == ["branch-b"]
    assert result.is_trunk is False
