from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_create_with_plan_file(tmp_path: Path) -> None:
    """Test creating a worktree from a plan file."""
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
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Create a plan file
    plan_file = repo / "Add_Auth_Feature.md"
    plan_content = "# Auth Feature Plan\n\n- Add login\n- Add signup\n"
    plan_file.write_text(plan_content)

    # Run workstack create with --plan, using isolated config
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "--plan", "Add_Auth_Feature.md", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify worktree was created with sanitized name
    worktree_path = workstacks_root / "repo" / "add-auth-feature"
    assert worktree_path.exists()
    assert worktree_path.is_dir()

    # Verify plan file was moved to .PLAN.md in worktree
    plan_dest = worktree_path / ".PLAN.md"
    assert plan_dest.exists()
    assert plan_dest.read_text() == plan_content

    # Verify original plan file was moved (not copied)
    assert not plan_file.exists()

    # Verify other standard files were created
    assert (worktree_path / ".env").exists()
    assert (worktree_path / "activate.sh").exists()


def test_create_with_plan_name_sanitization(tmp_path: Path) -> None:
    """Test that plan filename gets properly sanitized for worktree name."""
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
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Create a plan file with underscores and mixed case
    plan_file = repo / "MY_COOL_Plan_File.md"
    plan_file.write_text("# Cool Plan\n")

    # Run workstack create with --plan, using isolated config
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "--plan", "MY_COOL_Plan_File.md", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify worktree name is lowercase with hyphens
    worktree_path = workstacks_root / "repo" / "my-cool-plan-file"
    assert worktree_path.exists()

    # Verify plan was moved
    assert (worktree_path / ".PLAN.md").exists()
    assert not plan_file.exists()


def test_create_with_both_name_and_plan_fails(tmp_path: Path) -> None:
    """Test that providing both NAME and --plan is an error."""
    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Create a plan file
    plan_file = repo / "plan.md"
    plan_file.write_text("# Plan\n")

    # Run workstack create with both NAME and --plan
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "myname", "--plan", "plan.md"],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    # Should fail
    assert result.returncode != 0
    assert (
        "Cannot specify both NAME and --plan" in result.stdout
        or "Cannot specify both NAME and --plan" in result.stderr
    )
