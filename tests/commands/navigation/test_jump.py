"""Tests for workstack jump command."""

from pathlib import Path

from click.testing import CliRunner

from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from tests.fakes.shell_ops import FakeShellOps
from tests.test_utils.graphite_helpers import setup_graphite_stack
from workstack.cli.cli import cli
from workstack.core.context import WorkstackContext
from workstack.core.gitops import WorktreeInfo


def test_jump_to_branch_in_single_worktree() -> None:
    """Test jumping to a branch that exists in exactly one worktree (with branching stacks)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        work_dir = cwd / "workstacks" / cwd.name
        work_dir.mkdir(parents=True)
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Set up branching stacks:
        # main -> feature-1 -> feature-2
        # main -> other-feature
        # This way feature-2 is only in one worktree's stack
        setup_graphite_stack(
            git_dir,
            {
                "main": {
                    "parent": None,
                    "children": ["feature-1", "other-feature"],
                    "is_trunk": True,
                },
                "feature-1": {"parent": "main", "children": ["feature-2"]},
                "feature-2": {"parent": "feature-1", "children": []},
                "other-feature": {"parent": "main", "children": []},
            },
        )

        # Create worktree directories
        feature_wt = work_dir / "feature-wt"
        other_wt = work_dir / "other-wt"
        feature_wt.mkdir(parents=True, exist_ok=True)
        other_wt.mkdir(parents=True, exist_ok=True)

        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=other_wt, branch="other-feature"),  # No main worktree
                    WorktreeInfo(path=feature_wt, branch="feature-1"),
                ]
            },
            current_branches={cwd: "other-feature"},
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

        # Jump to feature-2 which is only in the feature-1 worktree's stack
        result = runner.invoke(
            cli, ["jump", "feature-2", "--script"], obj=test_ctx, catch_exceptions=False
        )

        if result.exit_code != 0:
            print(f"stderr: {result.stderr}")
            print(f"stdout: {result.stdout}")
        assert result.exit_code == 0

        # Should checkout feature-2 in the worktree and generate activation script
        assert any(branch == "feature-2" for _, branch in git_ops.checked_out_branches)
        script_path = Path(result.stdout.strip())
        assert script_path.exists()
        script_content = script_path.read_text()
        assert str(feature_wt) in script_content


def test_jump_to_branch_not_found() -> None:
    """Test jumping to a branch that doesn't exist in any stack."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        work_dir = cwd / "workstacks" / cwd.name
        work_dir.mkdir(parents=True)
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Set up stack: main -> feature-1
        setup_graphite_stack(
            git_dir,
            {
                "main": {"parent": None, "children": ["feature-1"], "is_trunk": True},
                "feature-1": {"parent": "main", "children": []},
            },
        )

        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=work_dir / "feature-1-wt", branch="feature-1"),
                ]
            },
            current_branches={cwd: "main"},
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

        # Jump to a branch that doesn't exist
        result = runner.invoke(
            cli, ["jump", "nonexistent-branch"], obj=test_ctx, catch_exceptions=False
        )

        assert result.exit_code == 1
        assert "not found in any worktree stack" in result.stderr
        assert "workstack create --from-branch nonexistent-branch" in result.stderr


def test_jump_multiple_worktrees_contain_branch() -> None:
    """Test jumping when multiple worktrees contain the target branch in their stacks.

    This test verifies the error case where a branch is in multiple worktree stacks
    but is NOT directly checked out in any of them.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        work_dir = cwd / "workstacks" / cwd.name
        work_dir.mkdir(parents=True)
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Set up stack: main -> feature-base
        # feature-base is in both worktree stacks but not directly checked out anywhere
        setup_graphite_stack(
            git_dir,
            {
                "main": {"parent": None, "children": ["feature-base"], "is_trunk": True},
                "feature-base": {"parent": "main", "children": ["feature-1", "feature-2"]},
                "feature-1": {"parent": "feature-base", "children": []},
                "feature-2": {"parent": "feature-base", "children": []},
            },
        )

        wt1 = work_dir / "feature-1-wt"
        wt2 = work_dir / "feature-2-wt"
        wt1.mkdir(parents=True, exist_ok=True)
        wt2.mkdir(parents=True, exist_ok=True)

        # feature-base is in both stacks but neither worktree has it checked out
        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=wt1, branch="feature-1"),
                    WorktreeInfo(path=wt2, branch="feature-2"),
                ]
            },
            current_branches={cwd: "main"},
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

        # Jump to feature-base which is in both stacks but not directly checked out
        result = runner.invoke(cli, ["jump", "feature-base"], obj=test_ctx, catch_exceptions=False)

        assert result.exit_code == 1
        assert "exists in multiple worktrees" in result.stderr
        assert "workstack switch" in result.stderr


def test_jump_graphite_not_enabled() -> None:
    """Test that jump requires Graphite to be enabled."""
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

        result = runner.invoke(cli, ["jump", "feature-1"], obj=test_ctx, catch_exceptions=False)

        assert result.exit_code == 1
        assert "requires Graphite" in result.stderr
        assert "workstack config set use_graphite true" in result.stderr


def test_jump_already_on_target_branch() -> None:
    """Test jumping when the target branch is already checked out in a single worktree."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        work_dir = cwd / "workstacks" / cwd.name
        work_dir.mkdir(parents=True)
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Set up branching stacks to avoid multiple matches:
        # main -> feature-1 -> feature-1-child
        # main -> other-feature
        setup_graphite_stack(
            git_dir,
            {
                "main": {
                    "parent": None,
                    "children": ["feature-1", "other-feature"],
                    "is_trunk": True,
                },
                "feature-1": {"parent": "main", "children": ["feature-1-child"]},
                "feature-1-child": {"parent": "feature-1", "children": []},
                "other-feature": {"parent": "main", "children": []},
            },
        )

        feature_wt = work_dir / "feature-1-wt"
        other_wt = work_dir / "other-wt"
        feature_wt.mkdir(parents=True, exist_ok=True)
        other_wt.mkdir(parents=True, exist_ok=True)

        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=other_wt, branch="other-feature"),
                    WorktreeInfo(path=feature_wt, branch="feature-1"),  # Already on feature-1
                ]
            },
            current_branches={cwd: "other-feature"},
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

        # Jump to feature-1 which is already checked out
        result = runner.invoke(
            cli, ["jump", "feature-1", "--script"], obj=test_ctx, catch_exceptions=False
        )

        # Should succeed without checking out (already on the branch)
        assert result.exit_code == 0
        #  Should not have checked out (it's already checked out)
        assert len(git_ops.checked_out_branches) == 0


def test_jump_to_branch_needs_checkout() -> None:
    """Test jumping to a branch that exists in a worktree but is not checked out."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        work_dir = cwd / "workstacks" / cwd.name
        work_dir.mkdir(parents=True)
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Set up branching stack:
        # main -> feature-1 -> feature-2 -> feature-3
        # main -> other-feature
        setup_graphite_stack(
            git_dir,
            {
                "main": {
                    "parent": None,
                    "children": ["feature-1", "other-feature"],
                    "is_trunk": True,
                },
                "feature-1": {"parent": "main", "children": ["feature-2"]},
                "feature-2": {"parent": "feature-1", "children": ["feature-3"]},
                "feature-3": {"parent": "feature-2", "children": []},
                "other-feature": {"parent": "main", "children": []},
            },
        )

        feature_wt = work_dir / "feature-wt"
        other_wt = work_dir / "other-wt"
        feature_wt.mkdir(parents=True, exist_ok=True)
        other_wt.mkdir(parents=True, exist_ok=True)

        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=other_wt, branch="other-feature"),
                    WorktreeInfo(path=feature_wt, branch="feature-3"),  # Currently on feature-3
                ]
            },
            current_branches={cwd: "other-feature"},
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

        # Jump to feature-2 which is in the stack but not checked out
        result = runner.invoke(
            cli, ["jump", "feature-2", "--script"], obj=test_ctx, catch_exceptions=False
        )

        assert result.exit_code == 0
        # Should have checked out feature-2
        assert any(branch == "feature-2" for _, branch in git_ops.checked_out_branches)
        # Should generate activation script
        script_path = Path(result.stdout.strip())
        assert script_path.exists()


def test_jump_prioritizes_directly_checked_out_branch() -> None:
    """Test that jump prioritizes worktrees with the branch directly checked out.

    When multiple worktrees contain the target branch in their stacks,
    but only one has it directly checked out, jump should go to that one.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        work_dir = cwd / "workstacks" / cwd.name
        work_dir.mkdir(parents=True)
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Set up stack where target branch is in multiple worktree stacks:
        # main -> feature-1 -> feature-2 -> feature-3
        # This means feature-2 is in the stacks of worktrees on feature-1, feature-2, and feature-3
        setup_graphite_stack(
            git_dir,
            {
                "main": {"parent": None, "children": ["feature-1"], "is_trunk": True},
                "feature-1": {"parent": "main", "children": ["feature-2"]},
                "feature-2": {"parent": "feature-1", "children": ["feature-3"]},
                "feature-3": {"parent": "feature-2", "children": []},
            },
        )

        wt1 = work_dir / "feature-1-wt"
        wt2 = work_dir / "feature-2-wt"
        wt3 = work_dir / "feature-3-wt"
        wt1.mkdir(parents=True, exist_ok=True)
        wt2.mkdir(parents=True, exist_ok=True)
        wt3.mkdir(parents=True, exist_ok=True)

        # feature-2 is directly checked out in wt2, but is in the stacks of all three worktrees
        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=wt1, branch="feature-1"),
                    WorktreeInfo(path=wt2, branch="feature-2"),  # Directly checked out here
                    WorktreeInfo(path=wt3, branch="feature-3"),
                ]
            },
            current_branches={cwd: "main"},
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

        # Jump to feature-2 which is in multiple stacks but directly checked out in wt2
        result = runner.invoke(
            cli, ["jump", "feature-2", "--script"], obj=test_ctx, catch_exceptions=False
        )

        if result.exit_code != 0:
            print(f"stderr: {result.stderr}")
            print(f"stdout: {result.stdout}")

        # Should succeed and jump to wt2 (no checkout needed)
        assert result.exit_code == 0
        # Should not checkout (already on feature-2 in wt2)
        assert len(git_ops.checked_out_branches) == 0
        # Should generate activation script pointing to wt2
        script_path = Path(result.stdout.strip())
        assert script_path.exists()
        script_content = script_path.read_text()
        assert str(wt2) in script_content
