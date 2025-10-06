from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from tests.fakes.gitops import FakeGitOps
from workstack.cli import cli
from workstack.context import WorkstackContext


def test_rename_successful() -> None:
    """Test successful rename of a worktree."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        global_config_dir = cwd / ".workstack_config"
        global_config_dir.mkdir()
        workstacks_root = cwd / "workstacks"
        (global_config_dir / "config.toml").write_text(
            f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
        )

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

        # Build fake git ops
        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        test_ctx = WorkstackContext(git_ops=git_ops)

        # Mock GLOBAL_CONFIG_PATH
        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["rename", "old-name", "new-name"], obj=test_ctx)

            assert result.exit_code == 0, result.output
            assert "new-name" in result.output


def test_rename_old_worktree_not_found() -> None:
    """Test rename fails when old worktree doesn't exist."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        global_config_dir = cwd / ".workstack_config"
        global_config_dir.mkdir()
        workstacks_root = cwd / "workstacks"
        (global_config_dir / "config.toml").write_text(
            f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
        )

        # Create git repo
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create worktree directory but not the specific worktree
        repo_name = cwd.name
        (workstacks_root / repo_name).mkdir(parents=True)

        # Build fake git ops
        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        test_ctx = WorkstackContext(git_ops=git_ops)

        # Mock GLOBAL_CONFIG_PATH
        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["rename", "nonexistent", "new-name"], obj=test_ctx)
            assert result.exit_code == 1
            assert "Worktree not found" in result.output


def test_rename_new_name_already_exists() -> None:
    """Test rename fails when new name already exists."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        global_config_dir = cwd / ".workstack_config"
        global_config_dir.mkdir()
        workstacks_root = cwd / "workstacks"
        (global_config_dir / "config.toml").write_text(
            f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
        )

        # Create git repo
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create two worktrees
        repo_name = cwd.name
        old_wt = workstacks_root / repo_name / "old-name"
        old_wt.mkdir(parents=True)
        new_wt = workstacks_root / repo_name / "new-name"
        new_wt.mkdir(parents=True)

        # Build fake git ops
        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        test_ctx = WorkstackContext(git_ops=git_ops)

        # Mock GLOBAL_CONFIG_PATH
        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["rename", "old-name", "new-name"], obj=test_ctx)
            assert result.exit_code == 1
            assert "already exists" in result.output


def test_rename_sanitizes_new_name() -> None:
    """Test that new name is sanitized."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        global_config_dir = cwd / ".workstack_config"
        global_config_dir.mkdir()
        workstacks_root = cwd / "workstacks"
        (global_config_dir / "config.toml").write_text(
            f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
        )

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create worktree
        repo_name = cwd.name
        old_wt = workstacks_root / repo_name / "old-name"
        old_wt.mkdir(parents=True)
        (old_wt / ".env").write_text('WORKTREE_NAME="old-name"\n', encoding="utf-8")

        # Build fake git ops
        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        test_ctx = WorkstackContext(git_ops=git_ops)

        # Mock GLOBAL_CONFIG_PATH
        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
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
        global_config_dir = cwd / ".workstack_config"
        global_config_dir.mkdir()
        workstacks_root = cwd / "workstacks"
        (global_config_dir / "config.toml").write_text(
            f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
        )

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create worktree with old .env
        repo_name = cwd.name
        old_wt = workstacks_root / repo_name / "old-name"
        old_wt.mkdir(parents=True)
        (old_wt / ".env").write_text('WORKTREE_NAME="old-name"\n', encoding="utf-8")

        # Build fake git ops
        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        test_ctx = WorkstackContext(git_ops=git_ops)

        # Mock GLOBAL_CONFIG_PATH
        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["rename", "old-name", "new-name"], obj=test_ctx)
            assert result.exit_code == 0, result.output

            # Verify .env was regenerated with new values
            new_wt = workstacks_root / repo_name / "new-name"
            env_content = (new_wt / ".env").read_text(encoding="utf-8")
            assert 'WORKTREE_NAME="new-name"' in env_content
            assert str(new_wt) in env_content
            assert "old-name" not in env_content
