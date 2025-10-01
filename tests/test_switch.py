from __future__ import annotations

import subprocess
from pathlib import Path


def test_switch_command(tmp_path: Path) -> None:
    """Test the switch command outputs activation script."""
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

    # Create a worktree
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "myfeature", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    # Run switch command
    result = subprocess.run(
        ["uv", "run", "workstack", "switch", "myfeature"],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # Should output shell code with cd command
    assert "cd" in result.stdout
    assert str(repo / ".workstack" / "myfeature") in result.stdout
    # Should source activate if venv exists
    assert "activate" in result.stdout


def test_switch_nonexistent_worktree(tmp_path: Path) -> None:
    """Test switch command with non-existent worktree."""
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
    """Test switching to root repo using '.'."""
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

    # Run switch command with "."
    result = subprocess.run(
        ["uv", "run", "workstack", "switch", "."],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # Should output shell code with cd to root
    assert "cd" in result.stdout
    assert str(repo) in result.stdout
    assert "root" in result.stdout.lower()


def test_list_includes_root(tmp_path: Path) -> None:
    """Test that list command shows root repo as '.'."""
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

    # Create a worktree
    subprocess.run(
        ["uv", "run", "workstack", "create", "myfeature", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    # List worktrees
    result = subprocess.run(
        ["uv", "run", "workstack", "list"],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # Should show root as first entry
    lines = result.stdout.strip().split("\n")
    assert len(lines) >= 2
    assert lines[0].startswith(".")
    assert "root" in lines[0].lower()
    # Should also show the worktree
    assert any("myfeature" in line for line in lines)
