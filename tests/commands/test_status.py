"""Integration tests for workstack status command."""

import os
import subprocess
from pathlib import Path


def test_status_command_basic(tmp_path: Path) -> None:
    """Test basic status command execution."""
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

    # Create a worktree
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    subprocess.run(
        ["uv", "run", "workstack", "create", "test-feature", "--no-post"],
        cwd=repo,
        env=env,
        check=True,
    )

    worktree_path = workstacks_root / "repo" / "test-feature"
    assert worktree_path.exists()

    # Run status command
    result = subprocess.run(
        ["uv", "run", "workstack", "status"],
        cwd=worktree_path,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert "test-feature" in result.stdout
    assert "Git Status:" in result.stdout


def test_status_command_with_changes(tmp_path: Path) -> None:
    """Test status command with modified files."""
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

    # Create a worktree
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    subprocess.run(
        ["uv", "run", "workstack", "create", "test-feature", "--no-post"],
        cwd=repo,
        env=env,
        check=True,
    )

    worktree_path = workstacks_root / "repo" / "test-feature"

    # Make some changes
    (worktree_path / "newfile.py").write_text("print('hello')")
    (worktree_path / "README.md").write_text("modified")

    # Run status command
    result = subprocess.run(
        ["uv", "run", "workstack", "status"],
        cwd=worktree_path,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert "Working tree has changes" in result.stdout
    assert "Modified:" in result.stdout or "Untracked:" in result.stdout


def test_status_command_with_plan(tmp_path: Path) -> None:
    """Test status command with .PLAN.md file."""
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

    # Create a plan file
    plan_file = repo / "Feature_Plan.md"
    plan_content = """# Feature Implementation Plan
## Overview
Implement the new feature.
This is line 4.
This is line 5."""
    plan_file.write_text(plan_content)

    # Create a worktree with plan
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    subprocess.run(
        ["uv", "run", "workstack", "create", "--plan", "Feature_Plan.md", "--no-post"],
        cwd=repo,
        env=env,
        check=True,
    )

    worktree_path = workstacks_root / "repo" / "feature"

    # Run status command
    result = subprocess.run(
        ["uv", "run", "workstack", "status"],
        cwd=worktree_path,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert "Plan:" in result.stdout
    assert "# Feature Implementation Plan" in result.stdout
    assert "## Overview" in result.stdout


def test_status_command_clean_worktree(tmp_path: Path) -> None:
    """Test status command with clean worktree."""
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

    # Create a worktree
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    subprocess.run(
        ["uv", "run", "workstack", "create", "clean-feature", "--no-post"],
        cwd=repo,
        env=env,
        check=True,
    )

    worktree_path = workstacks_root / "repo" / "clean-feature"

    # Run status command
    result = subprocess.run(
        ["uv", "run", "workstack", "status"],
        cwd=worktree_path,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    # The worktree will have .env as untracked file
    assert "Git Status:" in result.stdout
    assert ".env" in result.stdout or "Working tree clean" in result.stdout


def test_status_command_not_in_worktree(tmp_path: Path) -> None:
    """Test status command fails when not in a worktree."""
    # Just try to run status in a non-git directory
    result = subprocess.run(
        ["uv", "run", "workstack", "status"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    # Should fail
    assert result.returncode != 0
