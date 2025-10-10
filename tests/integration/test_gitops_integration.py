"""Integration tests for RealGitOps.

These tests verify that RealGitOps correctly interacts with real git commands,
complementing the unit tests that use FakeGitOps.
"""

import subprocess
from pathlib import Path

import pytest

from workstack.core.gitops import RealGitOps


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


def test_list_worktrees_single_repo(tmp_path: Path) -> None:
    """Test listing worktrees returns only main repository when no worktrees exist."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    git_ops = RealGitOps()
    worktrees = git_ops.list_worktrees(repo)

    assert len(worktrees) == 1
    assert worktrees[0].path == repo
    assert worktrees[0].branch == "main"


def test_list_worktrees_multiple(tmp_path: Path) -> None:
    """Test listing worktrees with multiple worktrees."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create worktrees
    wt1 = tmp_path / "wt1"
    wt2 = tmp_path / "wt2"

    subprocess.run(
        ["git", "worktree", "add", "-b", "feature-1", str(wt1)],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "worktree", "add", "-b", "feature-2", str(wt2)],
        cwd=repo,
        check=True,
    )

    git_ops = RealGitOps()
    worktrees = git_ops.list_worktrees(repo)

    assert len(worktrees) == 3

    # Find each worktree
    main_wt = next(wt for wt in worktrees if wt.branch == "main")
    feat1_wt = next(wt for wt in worktrees if wt.branch == "feature-1")
    feat2_wt = next(wt for wt in worktrees if wt.branch == "feature-2")

    assert main_wt.path == repo
    assert feat1_wt.path == wt1
    assert feat2_wt.path == wt2


def test_list_worktrees_detached_head(tmp_path: Path) -> None:
    """Test listing worktrees includes detached HEAD worktree with None branch."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create detached worktree
    wt_detached = tmp_path / "detached"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(wt_detached)],
        cwd=repo,
        check=True,
    )

    git_ops = RealGitOps()
    worktrees = git_ops.list_worktrees(repo)

    assert len(worktrees) == 2
    detached_wt = next(wt for wt in worktrees if wt.path == wt_detached)
    assert detached_wt.branch is None


def test_get_current_branch_normal(tmp_path: Path) -> None:
    """Test getting current branch in normal checkout."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    git_ops = RealGitOps()
    branch = git_ops.get_current_branch(repo)

    assert branch == "main"


def test_get_current_branch_after_checkout(tmp_path: Path) -> None:
    """Test getting current branch after checking out a different branch."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create and checkout new branch
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=repo, check=True)

    git_ops = RealGitOps()
    branch = git_ops.get_current_branch(repo)

    assert branch == "feature"


def test_get_current_branch_detached_head(tmp_path: Path) -> None:
    """Test getting current branch in detached HEAD state returns None."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Get commit hash and checkout in detached state
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    commit_hash = result.stdout.strip()
    subprocess.run(["git", "checkout", commit_hash], cwd=repo, check=True)

    git_ops = RealGitOps()
    branch = git_ops.get_current_branch(repo)

    assert branch is None


def test_get_current_branch_non_git_directory(tmp_path: Path) -> None:
    """Test getting current branch in non-git directory returns None."""
    non_git = tmp_path / "not-a-repo"
    non_git.mkdir()

    git_ops = RealGitOps()
    branch = git_ops.get_current_branch(non_git)

    assert branch is None


def test_detect_default_branch_main(tmp_path: Path) -> None:
    """Test detecting default branch when it's main."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    git_ops = RealGitOps()
    default_branch = git_ops.detect_default_branch(repo)

    assert default_branch == "main"


def test_detect_default_branch_master(tmp_path: Path) -> None:
    """Test detecting default branch when it's master."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "master")

    git_ops = RealGitOps()
    default_branch = git_ops.detect_default_branch(repo)

    assert default_branch == "master"


def test_detect_default_branch_with_remote_head(tmp_path: Path) -> None:
    """Test detecting default branch using remote HEAD."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Set up remote HEAD manually
    subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main"],
        cwd=repo,
        check=True,
    )

    git_ops = RealGitOps()
    default_branch = git_ops.detect_default_branch(repo)

    assert default_branch == "main"


def test_detect_default_branch_neither_exists(tmp_path: Path) -> None:
    """Test detecting default branch when neither main nor master exist raises SystemExit."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "trunk")

    # Delete the trunk branch we just created (keep the commit)
    subprocess.run(["git", "checkout", "--detach"], cwd=repo, check=True)
    subprocess.run(["git", "branch", "-D", "trunk"], cwd=repo, check=True)

    git_ops = RealGitOps()

    with pytest.raises(SystemExit):
        git_ops.detect_default_branch(repo)


def test_get_git_common_dir_from_main_repo(tmp_path: Path) -> None:
    """Test getting git common dir from main repository."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    git_ops = RealGitOps()
    git_dir = git_ops.get_git_common_dir(repo)

    assert git_dir is not None
    assert git_dir == repo / ".git"


def test_get_git_common_dir_from_worktree(tmp_path: Path) -> None:
    """Test getting git common dir from worktree returns shared .git directory."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create worktree
    wt = tmp_path / "wt"
    subprocess.run(
        ["git", "worktree", "add", "-b", "feature", str(wt)],
        cwd=repo,
        check=True,
    )

    git_ops = RealGitOps()
    git_dir = git_ops.get_git_common_dir(wt)

    assert git_dir is not None
    assert git_dir == repo / ".git"


def test_get_git_common_dir_non_git_directory(tmp_path: Path) -> None:
    """Test getting git common dir in non-git directory returns None."""
    non_git = tmp_path / "not-a-repo"
    non_git.mkdir()

    git_ops = RealGitOps()
    git_dir = git_ops.get_git_common_dir(non_git)

    assert git_dir is None


def test_add_worktree_with_existing_branch(tmp_path: Path) -> None:
    """Test adding worktree with existing branch."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create a branch
    subprocess.run(["git", "branch", "feature"], cwd=repo, check=True)

    wt = tmp_path / "wt"
    git_ops = RealGitOps()
    git_ops.add_worktree(repo, wt, branch="feature", ref=None, create_branch=False)

    assert wt.exists()
    assert (wt / "README.md").exists()

    # Verify branch is checked out
    branch = git_ops.get_current_branch(wt)
    assert branch == "feature"


def test_add_worktree_create_new_branch(tmp_path: Path) -> None:
    """Test adding worktree with new branch creation."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    wt = tmp_path / "wt"
    git_ops = RealGitOps()
    git_ops.add_worktree(repo, wt, branch="new-feature", ref=None, create_branch=True)

    assert wt.exists()
    assert (wt / "README.md").exists()

    # Verify new branch is checked out
    branch = git_ops.get_current_branch(wt)
    assert branch == "new-feature"


def test_add_worktree_from_specific_ref(tmp_path: Path) -> None:
    """Test adding worktree from specific ref."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create another commit on main
    (repo / "file.txt").write_text("content\n", encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Add file"], cwd=repo, check=True)

    # Create branch at main
    subprocess.run(["git", "branch", "old-main", "HEAD~1"], cwd=repo, check=True)

    wt = tmp_path / "wt"
    git_ops = RealGitOps()
    git_ops.add_worktree(repo, wt, branch="test-branch", ref="old-main", create_branch=True)

    assert wt.exists()
    assert (wt / "README.md").exists()
    # file.txt should not exist because we branched from HEAD~1
    assert not (wt / "file.txt").exists()


def test_add_worktree_detached(tmp_path: Path) -> None:
    """Test adding detached worktree."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    wt = tmp_path / "wt"
    git_ops = RealGitOps()
    git_ops.add_worktree(repo, wt, branch=None, ref="HEAD", create_branch=False)

    assert wt.exists()
    assert (wt / "README.md").exists()

    # Verify it's in detached HEAD state
    branch = git_ops.get_current_branch(wt)
    assert branch is None


def test_move_worktree(tmp_path: Path) -> None:
    """Test moving worktree to new location."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create worktree
    old_path = tmp_path / "old"
    subprocess.run(
        ["git", "worktree", "add", "-b", "feature", str(old_path)],
        cwd=repo,
        check=True,
    )

    # Move worktree
    new_path = tmp_path / "new"
    git_ops = RealGitOps()
    git_ops.move_worktree(repo, old_path, new_path)

    # Verify old path doesn't exist and new path does
    assert not old_path.exists()
    assert new_path.exists()
    assert (new_path / "README.md").exists()

    # Verify git still tracks it correctly
    worktrees = git_ops.list_worktrees(repo)
    moved_wt = next(wt for wt in worktrees if wt.branch == "feature")
    assert moved_wt.path == new_path


def test_remove_worktree(tmp_path: Path) -> None:
    """Test removing worktree."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create worktree
    wt = tmp_path / "wt"
    subprocess.run(
        ["git", "worktree", "add", "-b", "feature", str(wt)],
        cwd=repo,
        check=True,
    )

    # Remove worktree
    git_ops = RealGitOps()
    git_ops.remove_worktree(repo, wt, force=False)

    # Verify it's removed
    worktrees = git_ops.list_worktrees(repo)
    assert len(worktrees) == 1
    assert worktrees[0].branch == "main"


def test_remove_worktree_with_force(tmp_path: Path) -> None:
    """Test removing worktree with force flag."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create worktree
    wt = tmp_path / "wt"
    subprocess.run(
        ["git", "worktree", "add", "-b", "feature", str(wt)],
        cwd=repo,
        check=True,
    )

    # Add uncommitted changes
    (wt / "dirty.txt").write_text("uncommitted\n", encoding="utf-8")

    # Remove with force
    git_ops = RealGitOps()
    git_ops.remove_worktree(repo, wt, force=True)

    # Verify it's removed
    worktrees = git_ops.list_worktrees(repo)
    assert len(worktrees) == 1
    assert worktrees[0].branch == "main"


def test_checkout_branch(tmp_path: Path) -> None:
    """Test checking out a branch."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create a new branch
    subprocess.run(["git", "branch", "feature"], cwd=repo, check=True)

    # Checkout the branch
    git_ops = RealGitOps()
    git_ops.checkout_branch(repo, "feature")

    # Verify branch is checked out
    branch = git_ops.get_current_branch(repo)
    assert branch == "feature"


def test_checkout_branch_in_worktree(tmp_path: Path) -> None:
    """Test checking out a branch within a worktree."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create worktree with feature-1
    wt = tmp_path / "wt"
    subprocess.run(
        ["git", "worktree", "add", "-b", "feature-1", str(wt)],
        cwd=repo,
        check=True,
    )

    # Create another branch from the worktree
    subprocess.run(["git", "branch", "feature-2"], cwd=wt, check=True)

    # Checkout feature-2 in the worktree
    git_ops = RealGitOps()
    git_ops.checkout_branch(wt, "feature-2")

    # Verify branch is checked out
    branch = git_ops.get_current_branch(wt)
    assert branch == "feature-2"
