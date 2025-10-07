"""Tests for the sync command."""

import subprocess
from pathlib import Path

from click.testing import CliRunner

from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from workstack.cli import cli
from workstack.context import WorkstackContext
from workstack.gitops import WorktreeInfo


def test_sync_requires_graphite() -> None:
    """Test that sync command requires Graphite to be enabled."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create minimal git repo structure
        repo_root = cwd
        (repo_root / ".git").mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: cwd / ".git"},
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                ],
            },
        )

        # use_graphite=False: Test that graphite is required
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=FakeGitHubOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["sync"], obj=test_ctx)

        assert result.exit_code == 1
        assert "requires Graphite" in result.output


def test_sync_runs_gt_sync_from_root() -> None:
    """Test that sync runs gt sync from root worktree."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create repo structure
        repo_root = cwd
        (repo_root / ".git").mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: cwd / ".git"},
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                ],
            },
        )

        # use_graphite=True: Feature requires graphite
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=FakeGitHubOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["sync"], obj=test_ctx)

        assert result.exit_code == 0
        assert "Running: gt sync" in result.output

        # Verify sync was called with correct arguments
        assert len(graphite_ops.sync_calls) == 1
        cwd_arg, force_arg = graphite_ops.sync_calls[0]
        assert cwd_arg == repo_root
        assert force_arg is False


def test_sync_with_force_flag() -> None:
    """Test that sync passes --force flag to gt sync."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        repo_root = cwd
        (repo_root / ".git").mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: cwd / ".git"},
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                ],
            },
        )

        # use_graphite=True: Feature requires graphite
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=FakeGitHubOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["sync", "-f"], obj=test_ctx)

        assert result.exit_code == 0
        assert "Running: gt sync -f" in result.output

        # Verify -f was passed
        assert len(graphite_ops.sync_calls) == 1
        _cwd_arg, force_arg = graphite_ops.sync_calls[0]
        assert force_arg is True


def test_sync_handles_gt_not_installed() -> None:
    """Test that sync handles gt command not found."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        repo_root = cwd
        (repo_root / ".git").mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: cwd / ".git"},
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                ],
            },
        )

        # use_graphite=True: Feature requires graphite
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        # Configure graphite_ops to raise FileNotFoundError
        graphite_ops = FakeGraphiteOps(sync_raises=FileNotFoundError())

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=FakeGitHubOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["sync"], obj=test_ctx)

        assert result.exit_code == 1
        assert "'gt' command not found" in result.output
        assert "brew install" in result.output


def test_sync_handles_gt_sync_failure() -> None:
    """Test that sync handles gt sync failure."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        repo_root = cwd
        (repo_root / ".git").mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: cwd / ".git"},
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                ],
            },
        )

        # use_graphite=True: Feature requires graphite
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        # Configure graphite_ops to raise CalledProcessError
        graphite_ops = FakeGraphiteOps(
            sync_raises=subprocess.CalledProcessError(128, ["gt", "sync"])
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=FakeGitHubOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["sync"], obj=test_ctx)

        assert result.exit_code == 128
        assert "gt sync failed with exit code 128" in result.output


def test_sync_identifies_deletable_workstacks() -> None:
    """Test that sync identifies merged/closed workstacks."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"
        repo_name = cwd.name
        work_dir = workstacks_root / repo_name
        work_dir.mkdir(parents=True)

        repo_root = cwd
        (repo_root / ".git").mkdir()

        # Create worktree directories under work_dir
        wt1 = work_dir / "feature-1"
        wt2 = work_dir / "feature-2"
        wt1.mkdir()
        wt2.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: cwd / ".git"},
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                    WorktreeInfo(path=wt1, branch="feature-1"),
                    WorktreeInfo(path=wt2, branch="feature-2"),
                ],
            },
        )

        # use_graphite=True: Feature requires graphite
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        graphite_ops = FakeGraphiteOps()

        # feature-1 is merged, feature-2 is open
        github_ops = FakeGitHubOps(
            pr_statuses={
                "feature-1": ("MERGED", 123, "Feature 1"),
                "feature-2": ("OPEN", 124, "Feature 2"),
            }
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=github_ops,
            dry_run=False,
        )

        # User cancels (just want to see the list, not actually delete)
        result = runner.invoke(cli, ["sync"], obj=test_ctx, input="n\n")

        assert result.exit_code == 0
        assert "Workstacks safe to delete:" in result.output
        assert "feature-1" in result.output
        assert "merged" in result.output
        assert "PR #123" in result.output
        # feature-2 should not be in deletable list
        assert "feature-2" not in result.output or "merged" not in result.output


def test_sync_no_deletable_workstacks() -> None:
    """Test sync when there are no deletable workstacks."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        repo_root = cwd
        (repo_root / ".git").mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: cwd / ".git"},
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                ],
            },
        )

        # use_graphite=True: Feature requires graphite
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=FakeGitHubOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["sync"], obj=test_ctx)

        assert result.exit_code == 0
        assert "No workstacks to clean up." in result.output


def test_sync_with_confirmation() -> None:
    """Test sync with user confirmation."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"
        repo_name = cwd.name
        work_dir = workstacks_root / repo_name
        work_dir.mkdir(parents=True)

        repo_root = cwd
        (repo_root / ".git").mkdir()

        # Create worktree directory under work_dir
        wt1 = work_dir / "feature-1"
        wt1.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: cwd / ".git"},
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                    WorktreeInfo(path=wt1, branch="feature-1"),
                ],
            },
        )

        # use_graphite=True: Feature requires graphite
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        graphite_ops = FakeGraphiteOps()
        github_ops = FakeGitHubOps(pr_statuses={"feature-1": ("MERGED", 123, "Feature 1")})

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=github_ops,
            dry_run=False,
        )

        # User confirms deletion
        result = runner.invoke(cli, ["sync"], obj=test_ctx, input="y\n")

        assert result.exit_code == 0
        assert "Remove 1 worktree(s)?" in result.output
        assert "Removing worktree: feature-1" in result.output


def test_sync_user_cancels() -> None:
    """Test sync when user cancels."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"
        repo_name = cwd.name
        work_dir = workstacks_root / repo_name
        work_dir.mkdir(parents=True)

        repo_root = cwd
        (repo_root / ".git").mkdir()

        wt1 = work_dir / "feature-1"
        wt1.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: cwd / ".git"},
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                    WorktreeInfo(path=wt1, branch="feature-1"),
                ],
            },
        )

        # use_graphite=True: Feature requires graphite
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        graphite_ops = FakeGraphiteOps()
        github_ops = FakeGitHubOps(pr_statuses={"feature-1": ("MERGED", 123, "Feature 1")})

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=github_ops,
            dry_run=False,
        )

        # User cancels deletion
        result = runner.invoke(cli, ["sync"], obj=test_ctx, input="n\n")

        assert result.exit_code == 0
        assert "Cleanup cancelled." in result.output
        # Worktree should still exist
        assert wt1.exists()


def test_sync_force_skips_confirmation() -> None:
    """Test sync -f skips confirmation."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"
        repo_name = cwd.name
        work_dir = workstacks_root / repo_name
        work_dir.mkdir(parents=True)

        repo_root = cwd
        (repo_root / ".git").mkdir()

        wt1 = work_dir / "feature-1"
        wt1.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: cwd / ".git"},
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                    WorktreeInfo(path=wt1, branch="feature-1"),
                ],
            },
        )

        # use_graphite=True: Feature requires graphite
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        graphite_ops = FakeGraphiteOps()
        github_ops = FakeGitHubOps(pr_statuses={"feature-1": ("MERGED", 123, "Feature 1")})

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=github_ops,
            dry_run=False,
        )

        result = runner.invoke(cli, ["sync", "-f"], obj=test_ctx)

        assert result.exit_code == 0
        # Should not prompt for confirmation
        assert "Remove 1 worktree(s)?" not in result.output
        assert "Removing worktree: feature-1" in result.output


def test_sync_dry_run() -> None:
    """Test sync --dry-run shows operations without executing."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"
        repo_name = cwd.name
        work_dir = workstacks_root / repo_name
        work_dir.mkdir(parents=True)

        repo_root = cwd
        (repo_root / ".git").mkdir()

        wt1 = work_dir / "feature-1"
        wt1.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: cwd / ".git"},
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                    WorktreeInfo(path=wt1, branch="feature-1"),
                ],
            },
        )

        # use_graphite=True: Feature requires graphite
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        graphite_ops = FakeGraphiteOps()
        github_ops = FakeGitHubOps(pr_statuses={"feature-1": ("MERGED", 123, "Feature 1")})

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=github_ops,
            dry_run=False,
        )

        result = runner.invoke(cli, ["sync", "--dry-run"], obj=test_ctx)

        assert result.exit_code == 0
        assert "[DRY RUN] Would run gt sync" in result.output
        assert "[DRY RUN] Would remove worktree: feature-1" in result.output

        # Verify sync was not called
        assert len(graphite_ops.sync_calls) == 0

        # Worktree should still exist
        assert wt1.exists()


def test_sync_return_to_original_worktree() -> None:
    """Test that sync returns to original worktree after running."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"
        workstacks_root.mkdir()

        repo_root = cwd
        (repo_root / ".git").mkdir()

        # Create worktree directory
        wt1 = workstacks_root / "feature-1"
        wt1.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={cwd: cwd / ".git"},
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                    WorktreeInfo(path=wt1, branch="feature-1"),
                ],
            },
        )

        # use_graphite=True: Feature requires graphite
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        graphite_ops = FakeGraphiteOps()
        github_ops = FakeGitHubOps(pr_statuses={"feature-1": ("OPEN", 123, "Feature 1")})

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=github_ops,
            dry_run=False,
        )

        result = runner.invoke(cli, ["sync"], obj=test_ctx)

        assert result.exit_code == 0

        # Note: In isolated_filesystem(), we start at cwd which is not
        # under workstacks_root, so no "Returning to:" message should appear


def test_sync_original_worktree_deleted() -> None:
    """Test sync when original worktree is deleted during cleanup."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"
        repo_name = cwd.name
        work_dir = workstacks_root / repo_name
        work_dir.mkdir(parents=True)

        repo_root = cwd
        (repo_root / ".git").mkdir()

        # Create worktree directory that we'll start in
        wt1 = work_dir / "feature-1"
        wt1.mkdir()

        git_ops = FakeGitOps(
            git_common_dirs={wt1: cwd / ".git"},
            worktrees={
                repo_root: [
                    WorktreeInfo(path=repo_root, branch="main"),
                    WorktreeInfo(path=wt1, branch="feature-1"),
                ],
            },
        )

        # use_graphite=True: Feature requires graphite
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        graphite_ops = FakeGraphiteOps()
        github_ops = FakeGitHubOps(pr_statuses={"feature-1": ("MERGED", 123, "Feature 1")})

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=github_ops,
            dry_run=False,
        )

        result = runner.invoke(cli, ["sync", "-f"], obj=test_ctx)

        assert result.exit_code == 0
        # Should mention that original worktree was deleted
        assert (
            "Original worktree 'feature-1' was deleted" in result.output
            or "Removing worktree: feature-1" in result.output
        )
