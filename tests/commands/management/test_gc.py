"""Tests for the gc command."""

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


def test_gc_lists_merged_pr_worktrees() -> None:
    """Test that gc lists worktrees with merged PRs."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        workstacks_dir = workstacks_root / cwd.name
        workstacks_dir.mkdir(parents=True)

        # Create worktree directories
        wt1 = workstacks_dir / "feature-1"
        wt1.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=wt1, branch="feature-1"),
                ]
            },
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
        )
        github_ops = FakeGitHubOps(
            pr_statuses={
                "feature-1": ("MERGED", 123, "Feature 1"),
            }
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=github_ops,
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["gc"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        assert "feature-1" in result.output
        assert "merged" in result.output.lower()
        assert "PR #123" in result.output


def test_gc_lists_closed_pr_worktrees() -> None:
    """Test that gc lists worktrees with closed PRs."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        workstacks_dir = workstacks_root / cwd.name
        workstacks_dir.mkdir(parents=True)

        wt1 = workstacks_dir / "feature-2"
        wt1.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=wt1, branch="feature-2"),
                ]
            },
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
        )
        github_ops = FakeGitHubOps(
            pr_statuses={
                "feature-2": ("CLOSED", 456, "Feature 2"),
            }
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=github_ops,
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["gc"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        assert "feature-2" in result.output
        assert "closed" in result.output.lower()
        assert "PR #456" in result.output


def test_gc_skips_root_repo() -> None:
    """Test that gc skips the root repository."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                ]
            },
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
        )
        github_ops = FakeGitHubOps(
            pr_statuses={
                "main": ("MERGED", 999, "Main PR"),
            }
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=github_ops,
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["gc"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        # Should not list root repo even if it has merged PR
        assert "No workstacks found" in result.output


def test_gc_skips_detached_head() -> None:
    """Test that gc skips worktrees with detached HEAD."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        workstacks_dir = workstacks_root / cwd.name
        workstacks_dir.mkdir(parents=True)

        wt1 = workstacks_dir / "detached"
        wt1.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=wt1, branch=None),  # Detached HEAD
                ]
            },
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["gc"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        assert "No workstacks found" in result.output


def test_gc_skips_non_managed_worktrees() -> None:
    """Test that gc skips worktrees outside the workstacks_dir."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        # Create non-managed worktree
        other_wt = cwd / "other-worktree"
        other_wt.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=other_wt, branch="other-branch"),
                ]
            },
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
        )
        github_ops = FakeGitHubOps(
            pr_statuses={
                "other-branch": ("MERGED", 100, "Other"),
            }
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=github_ops,
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["gc"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        # Should not list non-managed worktrees
        assert "No workstacks found" in result.output


def test_gc_displays_deletion_suggestions() -> None:
    """Test that gc displays deletion command suggestions."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        workstacks_dir = workstacks_root / cwd.name
        workstacks_dir.mkdir(parents=True)

        wt1 = workstacks_dir / "old-feature"
        wt1.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=wt1, branch="old-feature"),
                ]
            },
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
        )
        github_ops = FakeGitHubOps(
            pr_statuses={
                "old-feature": ("MERGED", 789, "Old Feature"),
            }
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=github_ops,
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["gc"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        assert "workstack rm old-feature" in result.output


def test_gc_queries_pr_status_for_each_branch() -> None:
    """Test that gc queries PR status for each managed worktree branch."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        workstacks_dir = workstacks_root / cwd.name
        workstacks_dir.mkdir(parents=True)

        wt1 = workstacks_dir / "feature-1"
        wt2 = workstacks_dir / "feature-2"
        wt1.mkdir()
        wt2.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=wt1, branch="feature-1"),
                    WorktreeInfo(path=wt2, branch="feature-2"),
                ]
            },
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
        )
        github_ops = FakeGitHubOps(
            pr_statuses={
                "feature-1": ("MERGED", 111, "F1"),
                "feature-2": ("OPEN", 222, "F2"),
            }
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=github_ops,
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["gc"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        # Should only list merged PR in the deletable section
        assert "feature-1" in result.output
        # feature-2 should show as checked but not in the deletable list
        assert "workstack rm feature-1" in result.output
        assert "workstack rm feature-2" not in result.output


def test_gc_handles_branches_without_prs() -> None:
    """Test that gc handles branches without PRs."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        workstacks_dir = workstacks_root / cwd.name
        workstacks_dir.mkdir(parents=True)

        wt1 = workstacks_dir / "no-pr-branch"
        wt1.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=wt1, branch="no-pr-branch"),
                ]
            },
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
        )
        # Branch not in pr_statuses means no PR found
        github_ops = FakeGitHubOps(pr_statuses={})

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=github_ops,
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["gc"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        assert "No workstacks found" in result.output


def test_gc_handles_open_prs() -> None:
    """Test that gc doesn't list worktrees with open PRs."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        workstacks_dir = workstacks_root / cwd.name
        workstacks_dir.mkdir(parents=True)

        wt1 = workstacks_dir / "active-feature"
        wt1.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=wt1, branch="active-feature"),
                ]
            },
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
        )
        github_ops = FakeGitHubOps(
            pr_statuses={
                "active-feature": ("OPEN", 333, "Active Feature"),
            }
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=github_ops,
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["gc"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        assert "No workstacks found" in result.output


def test_gc_debug_shows_commands() -> None:
    """Test that gc debug mode shows executed commands."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                ]
            },
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["gc", "--debug"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        # Debug mode message is always shown
        assert "Debug mode is enabled" in result.output


def test_gc_no_deletable_worktrees() -> None:
    """Test gc output when no deletable worktrees found."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                ]
            },
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["gc"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        assert "No workstacks found that are safe to delete" in result.output
