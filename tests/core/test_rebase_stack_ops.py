"""Tests for rebase stack management.

These tests verify that RebaseStackOps correctly manages rebase stacks
(temporary worktrees) with proper isolation and state tracking.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from workstack.core.gitops import RealGitOps
from workstack.core.rebase_stack_ops import (
    RebaseStackOps,
    StackState,
)


def init_git_repo(repo_path: Path, default_branch: str = "main") -> None:
    """Initialize a git repository with initial commit."""
    subprocess.run(["git", "init", "-b", default_branch], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)

    # Create initial commit
    test_file = repo_path / "README.md"
    test_file.write_text("# Test Repository\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)


@pytest.fixture
def test_repo(tmp_path: Path) -> Path:
    """Create a test git repository."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create a feature branch
    subprocess.run(["git", "branch", "feature-branch"], cwd=repo, check=True)

    return repo


@pytest.fixture
def stack_ops() -> RebaseStackOps:
    """Create a RebaseStackOps instance with real git operations."""
    return RebaseStackOps(RealGitOps())


def test_create_stack(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test creating a rebase stack."""
    stack_path = stack_ops.create_stack(
        test_repo,
        "feature-branch",
        "main",
    )

    assert stack_path.exists()
    assert stack_path.name == ".rebase-stack-feature-branch"

    # Verify metadata
    metadata_file = stack_path / ".rebase-stack-metadata"
    assert metadata_file.exists()

    data = json.loads(metadata_file.read_text(encoding="utf-8"))
    assert data["branch_name"] == "feature-branch"
    assert data["target_branch"] == "main"
    assert data["state"] == "created"
    assert "original_commit" in data
    assert "created_at" in data


def test_cleanup_stack(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test removing a rebase stack."""
    # Create stack
    stack_path = stack_ops.create_stack(test_repo, "feature-branch", "main")
    assert stack_path.exists()

    # Cleanup
    stack_ops.cleanup_stack(test_repo, "feature-branch")
    assert not stack_path.exists()


def test_cleanup_nonexistent_stack(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test cleaning up a stack that doesn't exist."""
    # Should not raise an error
    stack_ops.cleanup_stack(test_repo, "nonexistent")


def test_list_stacks(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test listing active stacks."""
    # Create another feature branch
    subprocess.run(["git", "branch", "feature2"], cwd=test_repo, check=True)

    # Create multiple stacks
    stack_ops.create_stack(test_repo, "feature-branch", "main")
    stack_ops.create_stack(test_repo, "feature2", "main")

    stacks = stack_ops.list_stacks(test_repo)

    assert len(stacks) == 2
    branch_names = {s.branch_name for s in stacks}
    assert "feature-branch" in branch_names
    assert "feature2" in branch_names


def test_stack_exists(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test checking if stack exists."""
    assert not stack_ops.stack_exists(test_repo, "feature-branch")

    stack_ops.create_stack(test_repo, "feature-branch", "main")
    assert stack_ops.stack_exists(test_repo, "feature-branch")


def test_get_stack_info(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test getting stack information."""
    stack_path = stack_ops.create_stack(test_repo, "feature-branch", "main")

    info = stack_ops.get_stack_info(stack_path)

    assert info is not None
    assert info.branch_name == "feature-branch"
    assert info.target_branch == "main"
    assert info.state == StackState.CREATED


def test_get_stack_info_nonexistent(stack_ops: RebaseStackOps, tmp_path: Path) -> None:
    """Test getting info for non-existent stack."""
    nonexistent = tmp_path / "nonexistent"
    info = stack_ops.get_stack_info(nonexistent)
    assert info is None


def test_update_stack_state(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test updating stack state."""
    stack_path = stack_ops.create_stack(test_repo, "feature-branch", "main")

    stack_ops.update_stack_state(stack_path, StackState.RESOLVED)

    info = stack_ops.get_stack_info(stack_path)
    assert info is not None
    assert info.state == StackState.RESOLVED


def test_concurrent_stacks(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test multiple stacks can exist simultaneously."""
    # Create another feature branch
    subprocess.run(["git", "branch", "feature2"], cwd=test_repo, check=True)

    stack1 = stack_ops.create_stack(test_repo, "feature-branch", "main")
    stack2 = stack_ops.create_stack(test_repo, "feature2", "main")

    assert stack1.exists()
    assert stack2.exists()
    assert stack1 != stack2

    stacks = stack_ops.list_stacks(test_repo)
    assert len(stacks) == 2


def test_recreate_stack(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test recreating a stack removes the old one."""
    stack_path1 = stack_ops.create_stack(test_repo, "feature-branch", "main")
    metadata1 = stack_ops._load_metadata(stack_path1)
    assert metadata1 is not None
    original_commit = metadata1.original_commit

    # Cleanup the stack so we can check out the branch
    stack_ops.cleanup_stack(test_repo, "feature-branch")

    # Make a commit in the original branch
    subprocess.run(["git", "checkout", "feature-branch"], cwd=test_repo, check=True)
    test_file = test_repo / "new_file.txt"
    test_file.write_text("new content\n", encoding="utf-8")
    subprocess.run(["git", "add", "new_file.txt"], cwd=test_repo, check=True)
    subprocess.run(["git", "commit", "-m", "Add new file"], cwd=test_repo, check=True)
    subprocess.run(["git", "checkout", "main"], cwd=test_repo, check=True)

    # Recreate stack
    stack_path2 = stack_ops.create_stack(test_repo, "feature-branch", "main")
    metadata2 = stack_ops._load_metadata(stack_path2)
    assert metadata2 is not None
    new_commit = metadata2.original_commit

    assert stack_path1 == stack_path2
    assert original_commit != new_commit


def test_sanitize_branch_names(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test branch names with slashes are sanitized."""
    # Create a branch with slashes
    subprocess.run(["git", "branch", "feature/my-work"], cwd=test_repo, check=True)

    stack_path = stack_ops.create_stack(
        test_repo,
        "feature/my-work",
        "main",
    )

    assert "feature-my-work" in str(stack_path)
    assert "/" not in stack_path.name


def test_get_stack_path(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test getting stack path without creating stack."""
    stack_path = stack_ops.get_stack_path(test_repo, "my-branch")

    expected = test_repo.parent / ".rebase-stack-my-branch"
    assert stack_path == expected


def test_stack_metadata_persistence(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test that stack metadata persists correctly."""
    stack_path = stack_ops.create_stack(test_repo, "feature-branch", "main")

    # Load metadata directly
    metadata = stack_ops._load_metadata(stack_path)
    assert metadata is not None
    assert metadata.branch_name == "feature-branch"
    assert metadata.target_branch == "main"
    assert metadata.state == StackState.CREATED.value

    # Verify created_at is valid ISO format
    created_at = datetime.fromisoformat(metadata.created_at)
    assert created_at is not None

    # Verify original_commit is a valid git SHA (40 hex chars)
    assert len(metadata.original_commit) == 40
    assert all(c in "0123456789abcdef" for c in metadata.original_commit)


def test_list_stacks_empty(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test listing stacks when none exist."""
    stacks = stack_ops.list_stacks(test_repo)
    assert len(stacks) == 0


def test_stack_info_fields(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test that StackInfo contains all expected fields."""
    stack_path = stack_ops.create_stack(test_repo, "feature-branch", "main")
    info = stack_ops.get_stack_info(stack_path)

    assert info is not None
    assert isinstance(info.branch_name, str)
    assert isinstance(info.stack_path, Path)
    assert isinstance(info.created_at, datetime)
    assert isinstance(info.state, StackState)
    assert isinstance(info.target_branch, str) or info.target_branch is None
    assert isinstance(info.conflicts, list)
    assert isinstance(info.commits_to_rebase, int)
    assert isinstance(info.commits_applied, int)


def test_update_stack_state_nonexistent(stack_ops: RebaseStackOps, tmp_path: Path) -> None:
    """Test updating state for non-existent stack does nothing."""
    nonexistent = tmp_path / "nonexistent"
    # Should not raise an error
    stack_ops.update_stack_state(nonexistent, StackState.RESOLVED)


def test_stack_path_location(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test that stack is created in parent directory of repo."""
    stack_path = stack_ops.create_stack(test_repo, "feature-branch", "main")

    # Stack should be in parent directory of repo
    assert stack_path.parent == test_repo.parent
    # Stack should start with .rebase-stack-
    assert stack_path.name.startswith(".rebase-stack-")


def test_stack_cleanup_removes_metadata(stack_ops: RebaseStackOps, test_repo: Path) -> None:
    """Test that cleanup removes both worktree and metadata."""
    stack_path = stack_ops.create_stack(test_repo, "feature-branch", "main")
    metadata_file = stack_path / ".rebase-stack-metadata"

    assert stack_path.exists()
    assert metadata_file.exists()

    stack_ops.cleanup_stack(test_repo, "feature-branch")

    assert not stack_path.exists()
    assert not metadata_file.exists()
