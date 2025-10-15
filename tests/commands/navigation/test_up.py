"""Tests for workstack up command."""

import json
from pathlib import Path

from click.testing import CliRunner

from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from tests.fakes.shell_ops import FakeShellOps
from workstack.cli.cli import cli
from workstack.core.context import WorkstackContext
from workstack.core.gitops import WorktreeInfo


def setup_graphite_stack(
    git_dir: Path, branches: dict[str, dict[str, list[str] | str | bool | None]]
) -> None:
    """Set up a fake Graphite cache file with a stack structure.

    Args:
        git_dir: Path to .git directory
        branches: Dict mapping branch name to metadata with keys:
            - parent: parent branch name or None for trunk
            - children: list of child branch names
            - is_trunk: optional bool, defaults to False
    """
    cache_file = git_dir / ".graphite_cache_persist"
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    branches_data = []
    for branch_name, metadata in branches.items():
        branch_data = {
            "children": metadata.get("children", []),
        }
        if metadata.get("parent") is not None:
            branch_data["parentBranchName"] = metadata["parent"]
        if metadata.get("is_trunk", False):
            branch_data["validationResult"] = "TRUNK"

        branches_data.append([branch_name, branch_data])

    cache_data = {"branches": branches_data}
    cache_file.write_text(json.dumps(cache_data), encoding="utf-8")


def test_up_with_existing_worktree() -> None:
    """Test up command when child branch has a worktree."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        # Work dir is constructed as workstacks_root / repo_name, where repo_name = cwd.name
        workstacks_dir = cwd / "workstacks" / cwd.name
        workstacks_dir.mkdir(parents=True)
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Set up stack: main -> feature-1 -> feature-2
        setup_graphite_stack(
            git_dir,
            {
                "main": {"parent": None, "children": ["feature-1"], "is_trunk": True},
                "feature-1": {"parent": "main", "children": ["feature-2"]},
                "feature-2": {"parent": "feature-1", "children": []},
            },
        )

        # Set up worktrees
        feature_1_path = workstacks_dir / "feature-1"
        feature_1_path.mkdir(parents=True, exist_ok=True)

        # The test runs from cwd, so we simulate being in feature-1 by setting
        # cwd's current branch to feature-1
        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=workstacks_dir / "feature-1", branch="feature-1"),
                    WorktreeInfo(path=workstacks_dir / "feature-2", branch="feature-2"),
                ]
            },
            current_branches={
                cwd: "feature-1",  # Simulate being in feature-1 worktree
            },
            default_branches={cwd: "main"},
            git_common_dirs={
                cwd: git_dir,
            },
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=cwd / "workstacks",
            use_graphite=True,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        # Navigate up from feature-1 to feature-2
        # Run from feature-1 worktree
        (workstacks_dir / "feature-1").mkdir(parents=True, exist_ok=True)
        (workstacks_dir / "feature-2").mkdir(parents=True, exist_ok=True)

        result = runner.invoke(cli, ["up", "--script"], obj=test_ctx, catch_exceptions=False)

        if result.exit_code != 0:
            print(f"stderr: {result.stderr}")
            print(f"stdout: {result.stdout}")
        assert result.exit_code == 0
        # Should generate script for feature-2
        script_path = Path(result.stdout.strip())
        assert script_path.exists()
        script_content = script_path.read_text()
        assert str(workstacks_dir / "feature-2") in script_content


def test_up_at_top_of_stack() -> None:
    """Test up command when at the top of stack (no children)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        # Work dir is constructed as workstacks_root / repo_name, where repo_name = cwd.name
        workstacks_dir = cwd / "workstacks" / cwd.name
        workstacks_dir.mkdir(parents=True)
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Set up stack: main -> feature-1 -> feature-2 (at top)
        setup_graphite_stack(
            git_dir,
            {
                "main": {"parent": None, "children": ["feature-1"], "is_trunk": True},
                "feature-1": {"parent": "main", "children": ["feature-2"]},
                "feature-2": {"parent": "feature-1", "children": []},
            },
        )

        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=workstacks_dir / "feature-2", branch="feature-2"),
                ]
            },
            current_branches={cwd: "feature-2"},  # Simulate being in feature-2 worktree
            git_common_dirs={cwd: git_dir},
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=cwd / "workstacks",
            use_graphite=True,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["up"], obj=test_ctx, catch_exceptions=False)

        assert result.exit_code == 1
        assert "Already at the top of the stack" in result.stderr


def test_up_child_has_no_worktree() -> None:
    """Test up command when child branch exists but has no worktree."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        # Work dir is constructed as workstacks_root / repo_name, where repo_name = cwd.name
        workstacks_dir = cwd / "workstacks" / cwd.name
        workstacks_dir.mkdir(parents=True)
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Set up stack: main -> feature-1 -> feature-2
        setup_graphite_stack(
            git_dir,
            {
                "main": {"parent": None, "children": ["feature-1"], "is_trunk": True},
                "feature-1": {"parent": "main", "children": ["feature-2"]},
                "feature-2": {"parent": "feature-1", "children": []},
            },
        )

        # Only feature-1 has a worktree, feature-2 does not
        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=workstacks_dir / "feature-1", branch="feature-1"),
                ]
            },
            current_branches={cwd: "feature-1"},  # Simulate being in feature-1 worktree
            git_common_dirs={cwd: git_dir},
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=cwd / "workstacks",
            use_graphite=True,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["up"], obj=test_ctx, catch_exceptions=False)

        assert result.exit_code == 1
        assert "feature-2" in result.stderr
        assert "no worktree" in result.stderr
        assert "workstack create feature-2" in result.stderr


def test_up_graphite_not_enabled() -> None:
    """Test up command requires Graphite to be enabled."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        git_ops = FakeGitOps(
            worktrees={cwd: [WorktreeInfo(path=cwd, branch="main")]},
            current_branches={cwd: "main"},
            git_common_dirs={cwd: git_dir},
        )

        # Graphite is NOT enabled
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=cwd / "workstacks",
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["up"], obj=test_ctx, catch_exceptions=False)

        assert result.exit_code == 1
        assert "requires Graphite to be enabled" in result.stderr
        assert "workstack config set use_graphite true" in result.stderr


def test_up_detached_head() -> None:
    """Test up command fails gracefully on detached HEAD."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Current branch is None (detached HEAD)
        git_ops = FakeGitOps(
            worktrees={cwd: [WorktreeInfo(path=cwd, branch=None)]},
            current_branches={cwd: None},
            git_common_dirs={cwd: git_dir},
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=cwd / "workstacks",
            use_graphite=True,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["up"], obj=test_ctx, catch_exceptions=False)

        assert result.exit_code == 1
        assert "Not currently on a branch" in result.stderr
        assert "detached HEAD" in result.stderr


def test_up_script_flag() -> None:
    """Test up command with --script flag generates activation script."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        # Work dir is constructed as workstacks_root / repo_name, where repo_name = cwd.name
        workstacks_dir = cwd / "workstacks" / cwd.name
        workstacks_dir.mkdir(parents=True)
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Set up stack: main -> feature-1 -> feature-2
        setup_graphite_stack(
            git_dir,
            {
                "main": {"parent": None, "children": ["feature-1"], "is_trunk": True},
                "feature-1": {"parent": "main", "children": ["feature-2"]},
                "feature-2": {"parent": "feature-1", "children": []},
            },
        )

        # Set up worktrees
        (workstacks_dir / "feature-1").mkdir(parents=True, exist_ok=True)
        (workstacks_dir / "feature-2").mkdir(parents=True, exist_ok=True)

        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=workstacks_dir / "feature-1", branch="feature-1"),
                    WorktreeInfo(path=workstacks_dir / "feature-2", branch="feature-2"),
                ]
            },
            current_branches={cwd: "feature-1"},  # Simulate being in feature-1 worktree
            default_branches={cwd: "main"},
            git_common_dirs={cwd: git_dir},
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=cwd / "workstacks",
            use_graphite=True,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["up", "--script"], obj=test_ctx, catch_exceptions=False)

        assert result.exit_code == 0
        # Output should be a script path
        script_path = Path(result.stdout.strip())
        assert script_path.exists()
        script_content = script_path.read_text()
        # Verify script contains the target worktree path
        assert str(workstacks_dir / "feature-2") in script_content
