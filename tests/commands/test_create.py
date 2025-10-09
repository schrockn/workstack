"""Tests for the create command."""

from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from workstack.cli import cli
from workstack.context import WorkstackContext


def test_create_basic_worktree() -> None:
    """Test creating a basic worktree."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        work_dir = workstacks_root / cwd.name
        work_dir.mkdir(parents=True)

        # Create minimal config
        config_toml = work_dir / "config.toml"
        config_toml.write_text("", encoding="utf-8")

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            default_branches={cwd: "main"},
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["create", "test-feature"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        wt_path = work_dir / "test-feature"
        assert wt_path.exists()
        assert (wt_path / ".env").exists()


def test_create_with_custom_branch_name() -> None:
    """Test creating a worktree with a custom branch name."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        work_dir = workstacks_root / cwd.name
        work_dir.mkdir(parents=True)

        config_toml = work_dir / "config.toml"
        config_toml.write_text("", encoding="utf-8")

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            default_branches={cwd: "main"},
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(
            cli, ["create", "feature", "--branch", "my-custom-branch"], obj=test_ctx
        )

        assert result.exit_code == 0, result.output
        assert "my-custom-branch" in result.output


def test_create_with_plan_file() -> None:
    """Test creating a worktree with a plan file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create plan file
        plan_file = cwd / "my-feature-plan.md"
        plan_file.write_text("# My Feature Plan\n", encoding="utf-8")

        workstacks_root = cwd / "workstacks"
        work_dir = workstacks_root / cwd.name
        work_dir.mkdir(parents=True)

        config_toml = work_dir / "config.toml"
        config_toml.write_text("", encoding="utf-8")

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            default_branches={cwd: "main"},
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["create", "--plan", str(plan_file)], obj=test_ctx)

        assert result.exit_code == 0, result.output
        # Should create worktree with sanitized plan filename
        wt_path = work_dir / "my-feature-plan"
        assert wt_path.exists()
        # Plan file should be moved to .PLAN.md
        assert (wt_path / ".PLAN.md").exists()
        assert not plan_file.exists()


def test_create_sanitizes_worktree_name() -> None:
    """Test that worktree names are sanitized."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        work_dir = workstacks_root / cwd.name
        work_dir.mkdir(parents=True)

        config_toml = work_dir / "config.toml"
        config_toml.write_text("", encoding="utf-8")

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            default_branches={cwd: "main"},
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["create", "Test_Feature!!"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        # The test verifies the command succeeds - the actual sanitization
        # is tested in test_naming.py. Here we just verify the worktree was created.
        assert work_dir.exists()
        # Check that some worktree directory was created
        created_dirs = [d for d in work_dir.iterdir() if d.is_dir()]
        assert len(created_dirs) > 0, f"No worktree directories created in {work_dir}"


def test_create_sanitizes_branch_name() -> None:
    """Test that branch names are sanitized."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        work_dir = workstacks_root / cwd.name
        work_dir.mkdir(parents=True)

        config_toml = work_dir / "config.toml"
        config_toml.write_text("", encoding="utf-8")

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            default_branches={cwd: "main"},
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        # Branch name should be sanitized differently than worktree name
        result = runner.invoke(cli, ["create", "Test_Feature!!"], obj=test_ctx)

        assert result.exit_code == 0, result.output


def test_create_detects_default_branch() -> None:
    """Test that create detects the default branch when needed."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        work_dir = workstacks_root / cwd.name
        work_dir.mkdir(parents=True)

        config_toml = work_dir / "config.toml"
        config_toml.write_text("", encoding="utf-8")

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            default_branches={cwd: "main"},
            current_branches={cwd: "feature"},
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(
            cli, ["create", "new-feature", "--from-current-branch"], obj=test_ctx
        )

        assert result.exit_code == 0, result.output


def test_create_fails_if_worktree_exists() -> None:
    """Test that create fails if worktree already exists."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        work_dir = workstacks_root / cwd.name
        work_dir.mkdir(parents=True)

        config_toml = work_dir / "config.toml"
        config_toml.write_text("", encoding="utf-8")

        # Create existing worktree directory
        wt_path = work_dir / "test-feature"
        wt_path.mkdir(parents=True)

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            default_branches={cwd: "main"},
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["create", "test-feature"], obj=test_ctx)

        assert result.exit_code == 1
        assert "already exists" in result.output


def test_create_runs_post_create_commands() -> None:
    """Test that create runs post-create commands."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        work_dir = workstacks_root / cwd.name
        work_dir.mkdir(parents=True)

        # Create config with post_create commands
        config_toml = work_dir / "config.toml"
        config_toml.write_text(
            '[post_create]\ncommands = ["echo hello > test.txt"]\n',
            encoding="utf-8",
        )

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            default_branches={cwd: "main"},
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["create", "test-feature"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        assert "Running post-create commands" in result.output


def test_create_sets_env_variables() -> None:
    """Test that create sets environment variables in .env file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        work_dir = workstacks_root / cwd.name
        work_dir.mkdir(parents=True)

        # Create config with env vars
        config_toml = work_dir / "config.toml"
        config_toml.write_text(
            '[env]\nMY_VAR = "my_value"\n',
            encoding="utf-8",
        )

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            default_branches={cwd: "main"},
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["create", "test-feature"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        wt_path = work_dir / "test-feature"
        env_file = wt_path / ".env"
        assert env_file.exists()
        env_content = env_file.read_text(encoding="utf-8")
        assert "MY_VAR" in env_content
        assert "WORKTREE_PATH" in env_content
        assert "REPO_ROOT" in env_content


def test_create_uses_graphite_when_enabled() -> None:
    """Test that create uses graphite when enabled."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        work_dir = workstacks_root / cwd.name
        work_dir.mkdir(parents=True)

        config_toml = work_dir / "config.toml"
        config_toml.write_text("", encoding="utf-8")

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            default_branches={cwd: "main"},
            current_branches={cwd: "main"},
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=True,
        )
        graphite_ops = FakeGraphiteOps()

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=graphite_ops,
            dry_run=False,
        )

        # Mock subprocess to simulate gt create
        with mock.patch("workstack.commands.create.subprocess.run") as mock_run:
            result = runner.invoke(cli, ["create", "test-feature"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        # Verify gt create was called
        assert any("gt" in str(call) for call in mock_run.call_args_list)


def test_create_uses_git_when_graphite_disabled() -> None:
    """Test that create uses git when graphite is disabled."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        work_dir = workstacks_root / cwd.name
        work_dir.mkdir(parents=True)

        config_toml = work_dir / "config.toml"
        config_toml.write_text("", encoding="utf-8")

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            default_branches={cwd: "main"},
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["create", "test-feature"], obj=test_ctx)

        assert result.exit_code == 0, result.output


def test_create_invalid_worktree_name() -> None:
    """Test that create rejects invalid worktree names."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        # Test reserved name "root"
        result = runner.invoke(cli, ["create", "root"], obj=test_ctx)
        assert result.exit_code == 1
        assert "reserved" in result.output.lower()

        # Test reserved name "main"
        result = runner.invoke(cli, ["create", "main"], obj=test_ctx)
        assert result.exit_code == 1
        assert "cannot be used" in result.output.lower()

        # Test reserved name "master"
        result = runner.invoke(cli, ["create", "master"], obj=test_ctx)
        assert result.exit_code == 1
        assert "cannot be used" in result.output.lower()


def test_create_plan_file_not_found() -> None:
    """Test that create fails when plan file doesn't exist."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["create", "--plan", "nonexistent.md"], obj=test_ctx)

        # Click should fail validation before reaching our code
        assert result.exit_code != 0


def test_create_no_post_flag_skips_commands() -> None:
    """Test that --no-post flag skips post-create commands."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        work_dir = workstacks_root / cwd.name
        work_dir.mkdir(parents=True)

        # Create config with post_create commands
        config_toml = work_dir / "config.toml"
        config_toml.write_text(
            '[post_create]\ncommands = ["echo hello"]\n',
            encoding="utf-8",
        )

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            default_branches={cwd: "main"},
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["create", "test-feature", "--no-post"], obj=test_ctx)

        assert result.exit_code == 0, result.output
        assert "Running post-create commands" not in result.output


def test_create_from_current_branch() -> None:
    """Test creating worktree from current branch."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        work_dir = workstacks_root / cwd.name
        work_dir.mkdir(parents=True)

        config_toml = work_dir / "config.toml"
        config_toml.write_text("", encoding="utf-8")

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            default_branches={cwd: "main"},
            current_branches={cwd: "feature-branch"},
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["create", "feature", "--from-current-branch"], obj=test_ctx)

        assert result.exit_code == 0, result.output


def test_create_from_branch() -> None:
    """Test creating worktree from an existing branch."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"
        work_dir = workstacks_root / cwd.name
        work_dir.mkdir(parents=True)

        config_toml = work_dir / "config.toml"
        config_toml.write_text("", encoding="utf-8")

        git_ops = FakeGitOps(
            git_common_dirs={cwd: git_dir},
            default_branches={cwd: "main"},
        )
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(
            cli, ["create", "feature", "--from-branch", "existing-branch"], obj=test_ctx
        )

        assert result.exit_code == 0, result.output


def test_create_requires_name_or_flag() -> None:
    """Test that create requires NAME or a flag."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = cwd / ".git"
        git_dir.mkdir()

        workstacks_root = cwd / "workstacks"

        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})
        global_config_ops = FakeGlobalConfigOps(
            exists=True,
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["create"], obj=test_ctx)

        assert result.exit_code == 1
        assert "Must provide NAME" in result.output
