from pathlib import Path

from click.testing import CliRunner

from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from tests.fakes.shell_ops import FakeShellOps
from workstack.cli.cli import cli
from workstack.core.context import WorkstackContext
from workstack.core.gitops import DryRunGitOps


def test_rename_successful() -> None:
    """Test successful rename of a worktree."""
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
        old_wt = workstacks_root / repo_name / "old-name"
        old_wt.mkdir(parents=True)
        (old_wt / ".env").write_text(
            'WORKTREE_PATH="/old/path"\nWORKTREE_NAME="old-name"\n', encoding="utf-8"
        )

        # Build fake git ops and global config ops
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

        result = runner.invoke(cli, ["rename", "old-name", "new-name"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        assert "new-name" in result.output


def test_rename_old_worktree_not_found() -> None:
    """Test rename fails when old worktree doesn't exist."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create worktree directory but not the specific worktree
        repo_name = cwd.name
        (workstacks_root / repo_name).mkdir(parents=True)

        # Build fake git ops and global config ops
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

        result = runner.invoke(cli, ["rename", "nonexistent", "new-name"], obj=test_ctx)
        assert result.exit_code == 1
        assert "Worktree not found" in result.output


def test_rename_new_name_already_exists() -> None:
    """Test rename fails when new name already exists."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create two worktrees
        repo_name = cwd.name
        old_wt = workstacks_root / repo_name / "old-name"
        old_wt.mkdir(parents=True)
        new_wt = workstacks_root / repo_name / "new-name"
        new_wt.mkdir(parents=True)

        # Build fake git ops and global config ops
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

        result = runner.invoke(cli, ["rename", "old-name", "new-name"], obj=test_ctx)
        assert result.exit_code == 1
        assert "already exists" in result.output


def test_rename_sanitizes_new_name() -> None:
    """Test that new name is sanitized."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create worktree
        repo_name = cwd.name
        old_wt = workstacks_root / repo_name / "old-name"
        old_wt.mkdir(parents=True)
        (old_wt / ".env").write_text('WORKTREE_NAME="old-name"\n', encoding="utf-8")

        # Build fake git ops and global config ops
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

        # Use a name with special characters that should be sanitized
        result = runner.invoke(cli, ["rename", "old-name", "New_Name_123"], obj=test_ctx)

        # Should be sanitized to lowercase with hyphens
        assert result.exit_code == 0, result.output
        assert "new-name-123" in result.output


def test_rename_regenerates_env_file() -> None:
    """Test that .env file is regenerated with correct values."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create worktree with old .env
        repo_name = cwd.name
        old_wt = workstacks_root / repo_name / "old-name"
        old_wt.mkdir(parents=True)
        (old_wt / ".env").write_text('WORKTREE_NAME="old-name"\n', encoding="utf-8")

        # Build fake git ops and global config ops
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

        result = runner.invoke(cli, ["rename", "old-name", "new-name"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Verify .env was regenerated with new values
        new_wt = workstacks_root / repo_name / "new-name"
        env_content = (new_wt / ".env").read_text(encoding="utf-8")
        assert 'WORKTREE_NAME="new-name"' in env_content
        assert str(new_wt) in env_content
        assert "old-name" not in env_content


def test_rename_dry_run_does_not_move() -> None:
    """Test dry-run mode prints but doesn't actually rename or modify files."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create worktree with .env file
        repo_name = cwd.name
        old_wt = workstacks_root / repo_name / "old-name"
        old_wt.mkdir(parents=True)
        old_env_content = 'WORKTREE_NAME="old-name"\n'
        (old_wt / ".env").write_text(old_env_content, encoding="utf-8")

        # Build fake git ops wrapped with dry-run
        fake_git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        git_ops = DryRunGitOps(fake_git_ops)

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

        result = runner.invoke(cli, ["rename", "old-name", "new-name"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Verify dry-run messages printed
        assert "[DRY RUN]" in result.output
        assert "Would run: git worktree move" in result.output
        assert "Would write .env file" in result.output

        # Verify nothing was actually changed
        # Old directory should still exist
        assert old_wt.exists()

        # New directory should NOT exist (move didn't happen)
        new_wt = workstacks_root / repo_name / "new-name"
        assert not new_wt.exists()

        # .env file should still have old content
        env_content = (old_wt / ".env").read_text(encoding="utf-8")
        assert env_content == old_env_content
