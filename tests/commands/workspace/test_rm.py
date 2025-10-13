from pathlib import Path

from click.testing import CliRunner

from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from tests.fakes.shell_ops import FakeShellOps
from workstack.cli.cli import cli
from workstack.core.context import WorkstackContext


def test_rm_force_removes_directory() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create worktree in the location determined by global config
        repo_name = cwd.name
        wt = workstacks_root / repo_name / "foo"
        wt.mkdir(parents=True)
        (wt / "hello.txt").write_text("hello world", encoding="utf-8")

        # Build fake git ops
        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})

        # Build fake global config ops
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=graphite_ops,
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["rm", "foo", "-f"], obj=test_ctx)
        assert result.exit_code == 0, result.output
        # Should print the removed path
        assert result.output.strip().endswith(str(wt))
        assert not wt.exists()


def test_rm_prompts_and_aborts_on_no() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create worktree in the location determined by global config
        repo_name = cwd.name
        wt = workstacks_root / repo_name / "bar"
        wt.mkdir(parents=True)

        # Build fake git ops
        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})

        # Build fake global config ops
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=graphite_ops,
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["rm", "bar"], input="n\n", obj=test_ctx)
        assert result.exit_code == 0, result.output
        # Should not remove when user says 'n'
        assert wt.exists()


def test_rm_dry_run_does_not_delete() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create worktree in the location determined by global config
        repo_name = cwd.name
        wt = workstacks_root / repo_name / "test-stack"
        wt.mkdir(parents=True)
        (wt / "file.txt").write_text("test content", encoding="utf-8")

        # Build fake git ops (will be wrapped with DryRunGitOps)
        from workstack.core.gitops import DryRunGitOps

        git_ops = DryRunGitOps(FakeGitOps(git_common_dirs={cwd: git_dir}))

        # Build fake global config ops
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=graphite_ops,
            shell_ops=FakeShellOps(),
            dry_run=True,
        )

        result = runner.invoke(cli, ["rm", "test-stack", "-f"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Verify dry-run messages printed
        assert "[DRY RUN]" in result.output
        assert "Would run: git worktree remove" in result.output
        assert "Would delete directory" in result.output

        # Directory should still exist (not deleted)
        assert wt.exists()
        assert (wt / "file.txt").exists()


def test_rm_dry_run_with_delete_stack() -> None:
    """Test dry-run with --delete-stack flag prints but doesn't delete branches."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create graphite cache file with stack data
        cache_file = git_dir / ".graphite_cache_persist"
        cache_content = {
            "branches": [
                ["main", {"validationResult": "TRUNK", "children": ["feature-1"]}],
                ["feature-1", {"parentBranchName": "main", "children": ["feature-2"]}],
                ["feature-2", {"parentBranchName": "feature-1", "children": []}],
            ]
        }
        import json

        cache_file.write_text(json.dumps(cache_content), encoding="utf-8")

        # Create worktree
        repo_name = cwd.name
        wt = workstacks_root / repo_name / "test-stack"
        wt.mkdir(parents=True)

        # Build fake git ops with worktree info
        from workstack.core.gitops import DryRunGitOps, WorktreeInfo

        fake_git_ops = FakeGitOps(
            worktrees={cwd: [WorktreeInfo(path=wt, branch="feature-2")]},
            git_common_dirs={cwd: git_dir},
        )
        git_ops = DryRunGitOps(fake_git_ops)

        # Build fake global config ops with graphite enabled
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=graphite_ops,
            shell_ops=FakeShellOps(),
            dry_run=True,
        )

        result = runner.invoke(cli, ["rm", "test-stack", "-f", "-s"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Verify dry-run messages for branch deletion
        assert "[DRY RUN]" in result.output
        assert "Would run: gt delete" in result.output

        # Verify no branches were actually deleted
        assert len(fake_git_ops.deleted_branches) == 0

        # Directory should still exist
        assert wt.exists()


def test_rm_rejects_dot_dot() -> None:
    """Test that rm rejects '..' as a worktree name."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=graphite_ops,
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["rm", "..", "-f"], obj=test_ctx)
        assert result.exit_code == 1
        assert "Error: Cannot remove '..'" in result.output
        assert "directory references not allowed" in result.output


def test_rm_rejects_root_slash() -> None:
    """Test that rm rejects '/' as a worktree name."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=graphite_ops,
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["rm", "/", "-f"], obj=test_ctx)
        assert result.exit_code == 1
        assert "Error: Cannot remove '/'" in result.output
        assert "absolute paths not allowed" in result.output


def test_rm_rejects_path_with_slash() -> None:
    """Test that rm rejects worktree names containing path separators."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=graphite_ops,
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["rm", "foo/bar", "-f"], obj=test_ctx)
        assert result.exit_code == 1
        assert "Error: Cannot remove 'foo/bar'" in result.output
        assert "path separators not allowed" in result.output


def test_rm_rejects_root_name() -> None:
    """Test that rm rejects 'root' as a worktree name."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=graphite_ops,
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["rm", "root", "-f"], obj=test_ctx)
        assert result.exit_code == 1
        assert "Error: Cannot remove 'root'" in result.output
        assert "root worktree name not allowed" in result.output
