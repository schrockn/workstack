"""Tests for workstack tree command."""

import json
import os
import tempfile
from pathlib import Path

from click.testing import CliRunner

from tests.fakes.context import create_test_context
from tests.fakes.gitops import FakeGitOps, WorktreeInfo
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from workstack.cli.cli import cli
from workstack.cli.tree import (
    BranchGraph,
    TreeNode,
    WorktreeMapping,
    _build_tree_from_graph,
    _filter_graph_to_active_branches,
    _get_worktree_mapping,
    _load_graphite_branch_graph,
    render_tree,
)


def test_filter_graph_keeps_only_active_branches() -> None:
    """Test that graph filtering removes inactive branches."""
    graph = BranchGraph(
        parent_of={
            "feature-a": "main",
            "feature-b": "main",
            "feature-c": "feature-b",
        },
        children_of={
            "main": ["feature-a", "feature-b"],
            "feature-b": ["feature-c"],
            "feature-a": [],
            "feature-c": [],
        },
        trunk_branches=["main"],
    )

    # Only feature-a and main have worktrees
    active = {"main", "feature-a"}

    filtered = _filter_graph_to_active_branches(graph, active)

    assert filtered.parent_of == {"feature-a": "main"}
    assert filtered.children_of == {"main": ["feature-a"]}
    assert filtered.trunk_branches == ["main"]


def test_filter_graph_preserves_multi_level_hierarchy() -> None:
    """Test filtering with nested branches."""
    graph = BranchGraph(
        parent_of={
            "child": "parent",
            "grandchild": "child",
        },
        children_of={
            "parent": ["child"],
            "child": ["grandchild"],
            "grandchild": [],
        },
        trunk_branches=["parent"],
    )

    # All branches are active
    active = {"parent", "child", "grandchild"}

    filtered = _filter_graph_to_active_branches(graph, active)

    assert filtered.parent_of == {"child": "parent", "grandchild": "child"}
    assert filtered.children_of == {
        "parent": ["child"],
        "child": ["grandchild"],
    }
    assert filtered.trunk_branches == ["parent"]


def test_build_tree_creates_correct_structure() -> None:
    """Test tree building from graph."""
    graph = BranchGraph(
        parent_of={"feature-a": "main"},
        children_of={"main": ["feature-a"], "feature-a": []},
        trunk_branches=["main"],
    )

    mapping = WorktreeMapping(
        branch_to_worktree={"main": "root", "feature-a": "feature-a"},
        worktree_to_path={
            "root": Path("/repo"),
            "feature-a": Path("/repo/work/feature-a"),
        },
        current_worktree="root",
    )

    roots = _build_tree_from_graph(graph, mapping)

    assert len(roots) == 1
    assert roots[0].branch_name == "main"
    assert roots[0].worktree_name == "root"
    assert roots[0].is_current is True
    assert len(roots[0].children) == 1
    assert roots[0].children[0].branch_name == "feature-a"
    assert roots[0].children[0].is_current is False


def test_build_tree_handles_multiple_children() -> None:
    """Test tree building with multiple children per parent."""
    graph = BranchGraph(
        parent_of={
            "feature-a": "main",
            "feature-b": "main",
        },
        children_of={
            "main": ["feature-a", "feature-b"],
            "feature-a": [],
            "feature-b": [],
        },
        trunk_branches=["main"],
    )

    mapping = WorktreeMapping(
        branch_to_worktree={
            "main": "root",
            "feature-a": "feature-a",
            "feature-b": "feature-b",
        },
        worktree_to_path={
            "root": Path("/repo"),
            "feature-a": Path("/repo/work/feature-a"),
            "feature-b": Path("/repo/work/feature-b"),
        },
        current_worktree=None,
    )

    roots = _build_tree_from_graph(graph, mapping)

    assert len(roots) == 1
    assert roots[0].branch_name == "main"
    assert len(roots[0].children) == 2
    child_names = {child.branch_name for child in roots[0].children}
    assert child_names == {"feature-a", "feature-b"}


def test_render_tree_single_branch() -> None:
    """Test rendering a single branch."""
    root = TreeNode(
        branch_name="main",
        worktree_name="root",
        children=[],
        is_current=False,
    )

    output = render_tree([root])

    # Should just show the branch with annotation, no tree characters
    assert "main" in output
    assert "[@root]" in output
    assert "├─" not in output
    assert "└─" not in output


def test_render_tree_with_children() -> None:
    """Test rendering tree with parent and children."""
    root = TreeNode(
        branch_name="main",
        worktree_name="root",
        children=[
            TreeNode("feature-a", "feature-a", [], False),
            TreeNode("feature-b", "feature-b", [], False),
        ],
        is_current=False,
    )

    output = render_tree([root])

    assert "main" in output
    assert "[@root]" in output
    assert "feature-a" in output
    assert "[@feature-a]" in output
    assert "feature-b" in output
    assert "[@feature-b]" in output
    # Should have branch and last-child connectors
    assert "├─" in output
    assert "└─" in output


def test_render_tree_nested_hierarchy() -> None:
    """Test rendering deeply nested tree."""
    root = TreeNode(
        branch_name="main",
        worktree_name="root",
        children=[
            TreeNode(
                branch_name="parent",
                worktree_name="parent",
                children=[
                    TreeNode("child", "child", [], False),
                ],
                is_current=False,
            ),
        ],
        is_current=False,
    )

    output = render_tree([root])

    assert "main" in output
    assert "[@root]" in output
    assert "parent" in output
    assert "[@parent]" in output
    assert "child" in output
    assert "[@child]" in output
    # Should have vertical continuation line
    assert "│" in output or "└─" in output


def test_get_worktree_mapping(monkeypatch) -> None:
    """Test worktree mapping creation from git worktrees."""
    repo_root = Path("/repo")
    workstacks_dir = Path("/repo/work")

    # Mock Path.cwd() to return repo_root so it detects as current worktree
    monkeypatch.setattr("pathlib.Path.cwd", lambda: repo_root)

    git_ops = FakeGitOps(
        worktrees={
            repo_root: [
                WorktreeInfo(path=repo_root, branch="main"),
                WorktreeInfo(path=workstacks_dir / "feature-a", branch="feature-a"),
                WorktreeInfo(path=workstacks_dir / "feature-b", branch="feature-b"),
            ]
        },
        current_branches={repo_root: "main"},
    )

    ctx = create_test_context(git_ops=git_ops)

    mapping = _get_worktree_mapping(ctx, repo_root)

    assert mapping.branch_to_worktree == {
        "main": "root",
        "feature-a": "feature-a",
        "feature-b": "feature-b",
    }
    assert "root" in mapping.worktree_to_path
    assert mapping.current_worktree == "root"


def test_get_worktree_mapping_skips_detached_head(monkeypatch) -> None:
    """Test that worktrees with detached HEAD are skipped."""
    repo_root = Path("/repo")

    # Mock Path.cwd() to return repo_root
    monkeypatch.setattr("pathlib.Path.cwd", lambda: repo_root)

    git_ops = FakeGitOps(
        worktrees={
            repo_root: [
                WorktreeInfo(path=repo_root, branch="main"),
                WorktreeInfo(path=Path("/repo/work/detached"), branch=None),
            ]
        },
    )

    ctx = create_test_context(git_ops=git_ops)

    mapping = _get_worktree_mapping(ctx, repo_root)

    # Should only have main, not the detached HEAD worktree
    assert mapping.branch_to_worktree == {"main": "root"}


def test_load_graphite_branch_graph() -> None:
    """Test loading branch graph from Graphite cache."""
    repo_root = Path("/repo")

    cache_data = {
        "branches": [
            [
                "main",
                {
                    "validationResult": "TRUNK",
                    "children": ["feature-a", "feature-b"],
                },
            ],
            [
                "feature-a",
                {
                    "parentBranchName": "main",
                    "children": [],
                },
            ],
            [
                "feature-b",
                {
                    "parentBranchName": "main",
                    "children": ["feature-b-2"],
                },
            ],
            [
                "feature-b-2",
                {
                    "parentBranchName": "feature-b",
                    "children": [],
                },
            ],
        ]
    }

    # Create fake filesystem with cache file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_git_dir = Path(tmpdir) / ".git"
        tmp_git_dir.mkdir()
        cache_file = tmp_git_dir / ".graphite_cache_persist"
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        git_ops = FakeGitOps(git_common_dirs={repo_root: tmp_git_dir})
        ctx = create_test_context(git_ops=git_ops)

        graph = _load_graphite_branch_graph(ctx, repo_root)

        assert graph is not None
        assert graph.trunk_branches == ["main"]
        assert graph.parent_of == {
            "feature-a": "main",
            "feature-b": "main",
            "feature-b-2": "feature-b",
        }
        assert graph.children_of == {
            "main": ["feature-a", "feature-b"],
            "feature-a": [],
            "feature-b": ["feature-b-2"],
            "feature-b-2": [],
        }


def test_load_graphite_branch_graph_returns_none_when_missing() -> None:
    """Test that missing cache returns None."""
    repo_root = Path("/repo")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_git_dir = Path(tmpdir) / ".git"
        tmp_git_dir.mkdir()
        # No cache file created

        git_ops = FakeGitOps(git_common_dirs={repo_root: tmp_git_dir})
        ctx = create_test_context(git_ops=git_ops)

        graph = _load_graphite_branch_graph(ctx, repo_root)

        assert graph is None


def test_tree_command_displays_hierarchy() -> None:
    """Test that tree command shows worktree hierarchy."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        repo_root = cwd / "repo"
        repo_root.mkdir()

        # Create fake git directory with Graphite cache
        git_dir = repo_root / ".git"
        git_dir.mkdir()

        cache_data = {
            "branches": [
                [
                    "main",
                    {
                        "validationResult": "TRUNK",
                        "children": ["feature-a"],
                    },
                ],
                [
                    "feature-a",
                    {
                        "parentBranchName": "main",
                        "children": [],
                    },
                ],
            ]
        }
        cache_file = git_dir / ".graphite_cache_persist"
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        git_ops = FakeGitOps(
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                    WorktreeInfo(
                        path=repo_root / "work" / "feature-a",
                        branch="feature-a",
                    ),
                ]
            },
            git_common_dirs={repo_root: git_dir},
            current_branches={repo_root: "main"},
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=cwd / "workstacks", use_graphite=True
        )

        ctx = create_test_context(git_ops=git_ops, global_config_ops=global_config_ops)

        # Change to repo directory so discover_repo_context can find .git
        os.chdir(repo_root)

        result = runner.invoke(cli, ["tree"], obj=ctx)

        assert result.exit_code == 0
        assert "main" in result.output
        assert "[@root]" in result.output
        assert "feature-a" in result.output
        assert "[@feature-a]" in result.output
        # Check for tree characters
        assert "└─" in result.output or "├─" in result.output


def test_tree_command_filters_branches_without_worktrees() -> None:
    """Test that branches without worktrees are not shown."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        repo_root = cwd / "repo"
        repo_root.mkdir()

        git_dir = repo_root / ".git"
        git_dir.mkdir()

        # Cache has 3 branches, but only 2 have worktrees
        cache_data = {
            "branches": [
                [
                    "main",
                    {
                        "validationResult": "TRUNK",
                        "children": ["feature-a", "feature-b"],
                    },
                ],
                [
                    "feature-a",
                    {
                        "parentBranchName": "main",
                        "children": [],
                    },
                ],
                [
                    "feature-b",
                    {
                        "parentBranchName": "main",
                        "children": [],
                    },
                ],
            ]
        }
        cache_file = git_dir / ".graphite_cache_persist"
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        # Only main and feature-a have worktrees (feature-b does not)
        git_ops = FakeGitOps(
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                    WorktreeInfo(
                        path=repo_root / "work" / "feature-a",
                        branch="feature-a",
                    ),
                ]
            },
            git_common_dirs={repo_root: git_dir},
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=cwd / "workstacks", use_graphite=True
        )

        ctx = create_test_context(git_ops=git_ops, global_config_ops=global_config_ops)

        # Change to repo directory so discover_repo_context can find .git
        os.chdir(repo_root)

        result = runner.invoke(cli, ["tree"], obj=ctx)

        assert result.exit_code == 0
        assert "main" in result.output
        assert "feature-a" in result.output
        # feature-b should NOT appear
        assert "feature-b" not in result.output


def test_tree_command_fails_without_graphite_cache() -> None:
    """Test that tree command fails when Graphite cache is missing."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        repo_root = cwd / "repo"
        repo_root.mkdir()

        git_dir = repo_root / ".git"
        git_dir.mkdir()
        # Note: No .graphite_cache_persist file created

        git_ops = FakeGitOps(
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                ]
            },
            git_common_dirs={repo_root: git_dir},
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=cwd / "workstacks", use_graphite=True
        )

        ctx = create_test_context(git_ops=git_ops, global_config_ops=global_config_ops)

        # Change to repo directory so discover_repo_context can find .git
        os.chdir(repo_root)

        result = runner.invoke(cli, ["tree"], obj=ctx)

        assert result.exit_code == 1
        assert "Graphite cache not found" in result.output
        assert "tree' command requires Graphite" in result.output


def test_tree_command_shows_nested_hierarchy() -> None:
    """Test tree command with 3-level nested hierarchy."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        repo_root = cwd / "repo"
        repo_root.mkdir()

        git_dir = repo_root / ".git"
        git_dir.mkdir()

        cache_data = {
            "branches": [
                [
                    "main",
                    {
                        "validationResult": "TRUNK",
                        "children": ["parent"],
                    },
                ],
                [
                    "parent",
                    {
                        "parentBranchName": "main",
                        "children": ["child"],
                    },
                ],
                [
                    "child",
                    {
                        "parentBranchName": "parent",
                        "children": [],
                    },
                ],
            ]
        }
        cache_file = git_dir / ".graphite_cache_persist"
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        git_ops = FakeGitOps(
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                    WorktreeInfo(path=repo_root / "work" / "parent", branch="parent"),
                    WorktreeInfo(path=repo_root / "work" / "child", branch="child"),
                ]
            },
            git_common_dirs={repo_root: git_dir},
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=cwd / "workstacks", use_graphite=True
        )

        ctx = create_test_context(git_ops=git_ops, global_config_ops=global_config_ops)

        # Change to repo directory so discover_repo_context can find .git
        os.chdir(repo_root)

        result = runner.invoke(cli, ["tree"], obj=ctx)

        assert result.exit_code == 0
        assert "main" in result.output
        assert "parent" in result.output
        assert "child" in result.output
        # Should have vertical continuation for nested structure
        assert "│" in result.output or "└─" in result.output


def test_get_worktree_mapping_detects_current_from_subdirectory(monkeypatch) -> None:
    """Test that current worktree is detected when cwd is a subdirectory."""
    repo_root = Path("/repo")
    feature_worktree = Path("/repo/work/feature-a")
    subdirectory = feature_worktree / "src" / "module"

    # Mock Path.cwd() to return subdirectory within feature-a worktree
    monkeypatch.setattr("pathlib.Path.cwd", lambda: subdirectory)

    git_ops = FakeGitOps(
        worktrees={
            repo_root: [
                WorktreeInfo(path=repo_root, branch="main"),
                WorktreeInfo(path=feature_worktree, branch="feature-a"),
            ]
        },
    )

    ctx = create_test_context(git_ops=git_ops)

    mapping = _get_worktree_mapping(ctx, repo_root)

    # Should detect feature-a as current even though cwd is in subdirectory
    assert mapping.current_worktree == "feature-a"


def test_get_worktree_mapping_handles_user_outside_all_worktrees(monkeypatch) -> None:
    """Test behavior when user is not in any worktree."""
    repo_root = Path("/repo")
    outside_path = Path("/tmp/somewhere-else")

    # Mock Path.cwd() to return path outside all worktrees
    monkeypatch.setattr("pathlib.Path.cwd", lambda: outside_path)

    git_ops = FakeGitOps(
        worktrees={
            repo_root: [
                WorktreeInfo(path=repo_root, branch="main"),
                WorktreeInfo(path=Path("/repo/work/feature-a"), branch="feature-a"),
            ]
        },
    )

    ctx = create_test_context(git_ops=git_ops)

    mapping = _get_worktree_mapping(ctx, repo_root)

    # Should have no current worktree
    assert mapping.current_worktree is None


def test_build_tree_handles_multiple_trunk_branches() -> None:
    """Test tree building with multiple trunk branches."""
    graph = BranchGraph(
        parent_of={"feature-a": "main", "feature-b": "develop"},
        children_of={
            "main": ["feature-a"],
            "develop": ["feature-b"],
            "feature-a": [],
            "feature-b": [],
        },
        trunk_branches=["main", "develop"],
    )

    mapping = WorktreeMapping(
        branch_to_worktree={
            "main": "root",
            "develop": "develop",
            "feature-a": "feature-a",
            "feature-b": "feature-b",
        },
        worktree_to_path={
            "root": Path("/repo"),
            "develop": Path("/repo/work/develop"),
            "feature-a": Path("/repo/work/feature-a"),
            "feature-b": Path("/repo/work/feature-b"),
        },
        current_worktree=None,
    )

    roots = _build_tree_from_graph(graph, mapping)

    # Should have 2 root nodes
    assert len(roots) == 2
    root_branches = {root.branch_name for root in roots}
    assert root_branches == {"main", "develop"}

    # Each root should have its child
    for root in roots:
        if root.branch_name == "main":
            assert len(root.children) == 1
            assert root.children[0].branch_name == "feature-a"
        elif root.branch_name == "develop":
            assert len(root.children) == 1
            assert root.children[0].branch_name == "feature-b"


def test_render_tree_with_very_deep_nesting() -> None:
    """Test rendering tree with 5+ levels of nesting."""
    root = TreeNode(
        branch_name="main",
        worktree_name="root",
        children=[
            TreeNode(
                branch_name="level1",
                worktree_name="level1",
                children=[
                    TreeNode(
                        branch_name="level2",
                        worktree_name="level2",
                        children=[
                            TreeNode(
                                branch_name="level3",
                                worktree_name="level3",
                                children=[
                                    TreeNode(
                                        branch_name="level4",
                                        worktree_name="level4",
                                        children=[
                                            TreeNode(
                                                branch_name="level5",
                                                worktree_name="level5",
                                                children=[],
                                                is_current=False,
                                            ),
                                        ],
                                        is_current=False,
                                    ),
                                ],
                                is_current=False,
                            ),
                        ],
                        is_current=False,
                    ),
                ],
                is_current=False,
            ),
        ],
        is_current=False,
    )

    output = render_tree([root])

    # All levels should be present
    assert "main" in output
    assert "level1" in output
    assert "level2" in output
    assert "level3" in output
    assert "level4" in output
    assert "level5" in output

    # Should have proper tree structure
    lines = output.split("\n")
    assert len(lines) == 6  # 6 levels deep


def test_tree_command_shows_three_level_hierarchy_with_correct_indentation() -> None:
    """Test tree command displays 3-level stack with proper indentation.

    Reproduces bug where workstack-dev-cli-implementation and
    create-agents-symlinks-implementation-plan appear at same level
    instead of nested hierarchy.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        repo_root = cwd / "repo"
        repo_root.mkdir()

        git_dir = repo_root / ".git"
        git_dir.mkdir()

        # Setup 3-level stack matching the real bug scenario
        cache_data = {
            "branches": [
                [
                    "main",
                    {
                        "validationResult": "TRUNK",
                        "children": ["workstack-dev-cli-implementation"],
                    },
                ],
                [
                    "workstack-dev-cli-implementation",
                    {
                        "parentBranchName": "main",
                        "children": ["create-agents-symlinks-implementation-plan"],
                        "validationResult": "VALID",
                    },
                ],
                [
                    "create-agents-symlinks-implementation-plan",
                    {
                        "parentBranchName": "workstack-dev-cli-implementation",
                        "children": [],
                        "validationResult": "VALID",
                    },
                ],
            ]
        }
        cache_file = git_dir / ".graphite_cache_persist"
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        # All 3 branches have active worktrees
        git_ops = FakeGitOps(
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                    WorktreeInfo(
                        path=repo_root / "work" / "workstack-dev-cli-implementation",
                        branch="workstack-dev-cli-implementation",
                    ),
                    WorktreeInfo(
                        path=repo_root / "work" / "create-agents-symlinks-implementation-plan",
                        branch="create-agents-symlinks-implementation-plan",
                    ),
                ]
            },
            git_common_dirs={repo_root: git_dir},
            current_branches={repo_root: "main"},
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=cwd / "workstacks", use_graphite=True
        )

        ctx = create_test_context(git_ops=git_ops, global_config_ops=global_config_ops)

        # Change to repo directory so discover_repo_context can find .git
        os.chdir(repo_root)

        result = runner.invoke(cli, ["tree"], obj=ctx)

        assert result.exit_code == 0

        # Verify the exact structure with proper indentation
        # Expected:
        # main [@root]
        # └─ workstack-dev-cli-implementation [@workstack-dev-cli-implementation]
        #    └─ create-agents-symlinks-implementation-plan
        #       [@create-agents-symlinks-implementation-plan]

        lines = result.output.strip().split("\n")
        assert len(lines) == 3

        # Line 0: main (no indentation, no connector)
        assert lines[0].startswith("main")
        assert "[@root]" in lines[0]

        # Line 1: workstack-dev-cli-implementation (has connector, no leading spaces)
        assert "└─ workstack-dev-cli-implementation" in lines[1]
        assert "[@workstack-dev-cli-implementation]" in lines[1]

        # Line 2: create-agents-symlinks-implementation-plan (has connector
        # AND leading spaces for nesting). This is the critical check - it
        # should have "   └─" (3 spaces + connector), NOT just "└─" at the
        # beginning
        assert "   └─ create-agents-symlinks-implementation-plan" in lines[2]
        assert "[@create-agents-symlinks-implementation-plan]" in lines[2]
