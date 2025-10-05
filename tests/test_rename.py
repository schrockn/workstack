from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from workstack.cli import cli


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

        # Track git worktree move call
        move_called = False

        def mock_move_worktree_git(repo_root, old_path, new_path):
            nonlocal move_called
            move_called = True
            # Simulate the move
            old_path.rename(new_path)

        # Mock GLOBAL_CONFIG_PATH and move_worktree_git
        with (
            mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"),
            mock.patch(
                "workstack.commands.rename.move_worktree_git", side_effect=mock_move_worktree_git
            ),
        ):
            result = runner.invoke(cli, ["rename", "old-name", "new-name"])

            assert result.exit_code == 0, result.output
            assert move_called, "move_worktree_git should have been called"
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
        Path(".git").mkdir()

        # Create worktree directory but not the specific worktree
        repo_name = cwd.name
        (workstacks_root / repo_name).mkdir(parents=True)

        # Mock GLOBAL_CONFIG_PATH
        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["rename", "nonexistent", "new-name"])
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
        Path(".git").mkdir()

        # Create two worktrees
        repo_name = cwd.name
        old_wt = workstacks_root / repo_name / "old-name"
        old_wt.mkdir(parents=True)
        new_wt = workstacks_root / repo_name / "new-name"
        new_wt.mkdir(parents=True)

        # Mock GLOBAL_CONFIG_PATH
        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["rename", "old-name", "new-name"])
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

        # Track sanitized name
        sanitized_name = None

        def mock_move_worktree_git(repo_root, old_path, new_path):
            nonlocal sanitized_name
            # Capture the sanitized name from the new path
            sanitized_name = new_path.name
            # Simulate the move
            old_path.rename(new_path)

        # Mock GLOBAL_CONFIG_PATH and move_worktree_git
        with (
            mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"),
            mock.patch(
                "workstack.commands.rename.move_worktree_git", side_effect=mock_move_worktree_git
            ),
        ):
            # Use a name with special characters that should be sanitized
            result = runner.invoke(cli, ["rename", "old-name", "New_Name_123"])

            # Should be sanitized to lowercase with hyphens
            assert sanitized_name == "new-name-123"
            assert result.exit_code == 0, result.output


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

        def mock_move_worktree_git(repo_root, old_path, new_path):
            # Simulate the move
            old_path.rename(new_path)

        # Mock GLOBAL_CONFIG_PATH and move_worktree_git
        with (
            mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"),
            mock.patch(
                "workstack.commands.rename.move_worktree_git", side_effect=mock_move_worktree_git
            ),
        ):
            result = runner.invoke(cli, ["rename", "old-name", "new-name"])
            assert result.exit_code == 0, result.output

            # Verify .env was regenerated with new values
            new_wt = workstacks_root / repo_name / "new-name"
            env_content = (new_wt / ".env").read_text(encoding="utf-8")
            assert 'WORKTREE_NAME="new-name"' in env_content
            assert str(new_wt) in env_content
            assert "old-name" not in env_content
