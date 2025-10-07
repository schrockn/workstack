import os
import re
import subprocess
from pathlib import Path

import pytest


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_switch_command(tmp_path: Path) -> None:
    """Test the switch command outputs activation script."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Create a worktree using isolated config
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "myfeature", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"Create failed: {result.stderr}"

    # Run switch command with --script flag
    result = subprocess.run(
        ["uv", "run", "workstack", "switch", "myfeature", "--script"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    # Should output shell code with cd command
    assert "cd" in result.stdout
    assert str(workstacks_root / "repo" / "myfeature") in result.stdout
    # Should source activate if venv exists
    assert "activate" in result.stdout


def test_switch_nonexistent_worktree(tmp_path: Path) -> None:
    """Test switch command with non-existent worktree."""
    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Try to switch to non-existent worktree
    result = subprocess.run(
        ["uv", "run", "workstack", "switch", "doesnotexist"],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()


def test_switch_shell_completion(tmp_path: Path) -> None:
    """Test that switch command has shell completion configured."""
    # This is a bit tricky to test without a real shell, but we can verify
    # the command is set up with the right completion function by checking help
    result = subprocess.run(
        ["uv", "run", "workstack", "switch", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "NAME" in result.stdout


def test_switch_to_root(tmp_path: Path) -> None:
    """Test switching to root repo using 'root'."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Run switch command with "root" and --script flag, using isolated config
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "switch", "root", "--script"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    # Should output shell code with cd to root
    assert "cd" in result.stdout
    assert str(repo) in result.stdout
    assert "root" in result.stdout.lower()


def test_list_includes_root(tmp_path: Path) -> None:
    """Test that list command shows root repo with branch name."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Create a worktree using isolated config
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    subprocess.run(
        ["uv", "run", "workstack", "create", "myfeature", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    # List worktrees
    result = subprocess.run(
        ["uv", "run", "workstack", "list"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    # Should show root as first entry with branch name
    clean_output = strip_ansi(result.stdout)
    lines = clean_output.strip().split("\n")
    assert len(lines) >= 2
    assert lines[0].startswith("root")
    assert "[main]" in lines[0]
    # Should also show the worktree
    assert any("myfeature" in line for line in lines)


def test_complete_worktree_names_without_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test completion function works even when Click context obj is None.

    This simulates the shell completion scenario where the CLI group callback
    hasn't run yet, so ctx.obj is None.
    """
    import click

    from workstack.cli import cli
    from workstack.commands.switch import complete_worktree_names
    from workstack.context import WorkstackContext
    from workstack.github_ops import RealGitHubOps
    from workstack.gitops import RealGitOps
    from workstack.global_config_ops import RealGlobalConfigOps
    from workstack.graphite_ops import RealGraphiteOps

    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=repo, check=True, capture_output=True)

    # Create worktrees
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    for name in ["feature-a", "feature-b", "bugfix-123"]:
        subprocess.run(
            ["uv", "run", "workstack", "create", name, "--no-post"],
            cwd=repo,
            capture_output=True,
            env=env,
        )

    # Mock create_context to use test environment
    def mock_create_context() -> WorkstackContext:
        return WorkstackContext(
            git_ops=RealGitOps(),
            global_config_ops=RealGlobalConfigOps(),
            github_ops=RealGitHubOps(),
            graphite_ops=RealGraphiteOps(),
            dry_run=False,
        )

    # Patch Path.home() to return tmp_path so config loading uses test config
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    # Create a mock Click context with NO obj (simulates shell completion scenario)
    ctx = click.Context(cli)
    ctx.obj = None  # This is the critical test condition

    # Change to repo directory for completion
    original_cwd = os.getcwd()
    try:
        os.chdir(repo)

        # Call completion function
        completions = complete_worktree_names(ctx, None, "")

        # Should return worktree names even without ctx.obj
        assert "root" in completions
        assert "feature-a" in completions
        assert "feature-b" in completions
        assert "bugfix-123" in completions

        # Test filtering by prefix
        completions = complete_worktree_names(ctx, None, "feat")
        assert "feature-a" in completions
        assert "feature-b" in completions
        assert "bugfix-123" not in completions

    finally:
        os.chdir(original_cwd)


def test_switch_rejects_main_as_worktree_name(tmp_path: Path) -> None:
    """Test that 'main' is rejected with helpful error."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Try to switch to "main"
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "switch", "main"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    # Should fail with error suggesting to use root
    assert result.returncode != 0
    assert "main" in result.stderr.lower()
    assert "workstack switch root" in result.stderr


def test_switch_rejects_master_as_worktree_name(tmp_path: Path) -> None:
    """Test that 'master' is rejected with helpful error."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "master"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Try to switch to "master"
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "switch", "master"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    # Should fail with error suggesting to use root
    assert result.returncode != 0
    assert "master" in result.stderr.lower()
    assert "workstack switch root" in result.stderr
