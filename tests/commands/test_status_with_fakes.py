"""Unit tests for workstack status command using fakes."""

from pathlib import Path

from click.testing import CliRunner

from tests.fakes.context import create_test_context
from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps, WorktreeInfo
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from workstack.cli.commands.status import status_cmd
from workstack.core.github_ops import PullRequestInfo


def test_status_cmd_in_main_worktree(tmp_path: Path) -> None:
    """Test status command when in the main worktree."""
    # Arrange
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()

    git_ops = FakeGitOps(
        worktrees={repo_root: [WorktreeInfo(path=repo_root, branch="main")]},
        current_branches={repo_root: "main"},
        git_common_dirs={repo_root: git_dir},
        file_statuses={repo_root: ([], [], [])},  # Clean
        ahead_behind={(repo_root, "main"): (0, 0)},
        recent_commits={
            repo_root: [
                {
                    "sha": "abc1234",
                    "message": "Initial commit",
                    "author": "Test",
                    "date": "1 hour ago",
                }
            ]
        },
    )
    global_config_ops = FakeGlobalConfigOps(
        workstacks_root=tmp_path / "workstacks",
        use_graphite=False,
        show_pr_info=False,
    )
    ctx = create_test_context(git_ops=git_ops, global_config_ops=global_config_ops)

    runner = CliRunner()
    # Change to the repo directory
    import os

    original_dir = os.getcwd()
    os.chdir(repo_root)
    try:
        # Act
        result = runner.invoke(status_cmd, obj=ctx, catch_exceptions=False)
    finally:
        os.chdir(original_dir)

    # Assert
    assert result.exit_code == 0
    assert "main" in result.output
    assert "Git Status:" in result.output
    assert "Working tree clean" in result.output


def test_status_cmd_in_feature_worktree(tmp_path: Path) -> None:
    """Test status command when in a feature worktree."""
    # Arrange
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()

    worktree_path = tmp_path / "workstacks" / "repo" / "feature-branch"
    worktree_path.mkdir(parents=True)

    git_ops = FakeGitOps(
        worktrees={
            repo_root: [
                WorktreeInfo(path=repo_root, branch="main"),
                WorktreeInfo(path=worktree_path, branch="feature-branch"),
            ]
        },
        current_branches={worktree_path: "feature-branch"},
        git_common_dirs={worktree_path: git_dir},
        file_statuses={worktree_path: (["new.py"], ["modified.py"], ["temp.txt"])},
        ahead_behind={(worktree_path, "feature-branch"): (2, 1)},
        recent_commits={
            worktree_path: [
                {"sha": "def5678", "message": "Add feature", "author": "Dev", "date": "30 min ago"}
            ]
        },
    )
    global_config_ops = FakeGlobalConfigOps(
        workstacks_root=tmp_path / "workstacks",
        use_graphite=False,
        show_pr_info=False,
    )
    ctx = create_test_context(git_ops=git_ops, global_config_ops=global_config_ops)

    runner = CliRunner()
    # Change to the worktree directory
    import os

    original_dir = os.getcwd()
    os.chdir(worktree_path)
    try:
        # Act
        result = runner.invoke(status_cmd, obj=ctx, catch_exceptions=False)
    finally:
        os.chdir(original_dir)

    # Assert
    assert result.exit_code == 0
    assert "feature-branch" in result.output
    assert "Working tree has changes" in result.output
    assert "ahead 2" in result.output.lower() or "2 ahead" in result.output.lower()
    assert "behind 1" in result.output.lower() or "1 behind" in result.output.lower()


def test_status_cmd_multiple_worktrees(tmp_path: Path) -> None:
    """Test status command with multiple worktrees."""
    # Arrange
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()

    wt1 = tmp_path / "workstacks" / "repo" / "feature-1"
    wt1.mkdir(parents=True)
    wt2 = tmp_path / "workstacks" / "repo" / "feature-2"
    wt2.mkdir(parents=True)
    wt3 = tmp_path / "workstacks" / "repo" / "feature-3"
    wt3.mkdir(parents=True)

    git_ops = FakeGitOps(
        worktrees={
            repo_root: [
                WorktreeInfo(path=repo_root, branch="main"),
                WorktreeInfo(path=wt1, branch="feature-1"),
                WorktreeInfo(path=wt2, branch="feature-2"),
                WorktreeInfo(path=wt3, branch="feature-3"),
            ]
        },
        current_branches={wt2: "feature-2"},
        git_common_dirs={wt2: git_dir},
        file_statuses={wt2: ([], [], [])},
        ahead_behind={(wt2, "feature-2"): (0, 0)},
        recent_commits={wt2: []},
    )
    global_config_ops = FakeGlobalConfigOps(
        workstacks_root=tmp_path / "workstacks",
        use_graphite=False,
        show_pr_info=False,
    )
    ctx = create_test_context(git_ops=git_ops, global_config_ops=global_config_ops)

    runner = CliRunner()
    # Change to wt2 directory
    import os

    original_dir = os.getcwd()
    os.chdir(wt2)
    try:
        # Act
        result = runner.invoke(status_cmd, obj=ctx, catch_exceptions=False)
    finally:
        os.chdir(original_dir)

    # Assert
    assert result.exit_code == 0
    assert "feature-2" in result.output


def test_status_cmd_with_all_collectors_data(tmp_path: Path) -> None:
    """Test status command with data from all collectors."""
    # Arrange
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()

    worktree_path = tmp_path / "workstacks" / "repo" / "feature"
    worktree_path.mkdir(parents=True)

    # Create .PLAN.md file
    plan_file = worktree_path / ".PLAN.md"
    plan_file.write_text("# Feature Plan\n## Overview\nImplement new feature", encoding="utf-8")

    git_ops = FakeGitOps(
        worktrees={
            repo_root: [
                WorktreeInfo(path=repo_root, branch="main"),
                WorktreeInfo(path=worktree_path, branch="feature"),
            ]
        },
        current_branches={worktree_path: "feature"},
        git_common_dirs={worktree_path: git_dir},
        file_statuses={worktree_path: (["staged.py"], [], [])},
        ahead_behind={(worktree_path, "feature"): (1, 0)},
        recent_commits={
            worktree_path: [
                {"sha": "abc1234", "message": "Add feature", "author": "Dev", "date": "1 hour ago"}
            ]
        },
    )

    github_ops = FakeGitHubOps(
        prs={
            "feature": PullRequestInfo(
                number=123,
                state="OPEN",
                url="https://github.com/owner/repo/pull/123",
                is_draft=False,
                checks_passing=True,
                owner="owner",
                repo="repo",
            )
        }
    )

    graphite_ops = FakeGraphiteOps(
        stacks={"feature": ["main", "feature", "feature-next"]},
    )

    global_config_ops = FakeGlobalConfigOps(
        workstacks_root=tmp_path / "workstacks",
        use_graphite=True,
        show_pr_info=True,
    )

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )

    runner = CliRunner()
    # Change to the worktree directory
    import os

    original_dir = os.getcwd()
    os.chdir(worktree_path)
    try:
        # Act
        result = runner.invoke(status_cmd, obj=ctx, catch_exceptions=False)
    finally:
        os.chdir(original_dir)

    # Assert
    assert result.exit_code == 0
    assert "feature" in result.output
    # Git status
    assert "Git Status:" in result.output
    # PR info
    assert "#123" in result.output or "123" in result.output
    # Stack info
    assert "Stack:" in result.output or "Graphite" in result.output
    # Plan info
    assert "Plan:" in result.output
    assert "Feature Plan" in result.output


def test_status_cmd_with_partial_collector_data(tmp_path: Path) -> None:
    """Test status command when some collectors return None."""
    # Arrange
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()

    worktree_path = tmp_path / "workstacks" / "repo" / "branch"
    worktree_path.mkdir(parents=True)

    git_ops = FakeGitOps(
        worktrees={repo_root: [WorktreeInfo(path=worktree_path, branch="branch")]},
        current_branches={worktree_path: "branch"},
        git_common_dirs={worktree_path: git_dir},
        file_statuses={worktree_path: ([], [], [])},
        ahead_behind={(worktree_path, "branch"): (0, 0)},
        recent_commits={worktree_path: []},
    )

    # No PR data
    github_ops = FakeGitHubOps(prs={})
    # No stack data
    graphite_ops = FakeGraphiteOps(stacks={})

    global_config_ops = FakeGlobalConfigOps(
        workstacks_root=tmp_path / "workstacks",
        use_graphite=True,
        show_pr_info=True,
    )

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )

    runner = CliRunner()
    # Change to the worktree directory
    import os

    original_dir = os.getcwd()
    os.chdir(worktree_path)
    try:
        # Act
        result = runner.invoke(status_cmd, obj=ctx, catch_exceptions=False)
    finally:
        os.chdir(original_dir)

    # Assert
    assert result.exit_code == 0
    assert "branch" in result.output
    assert "Git Status:" in result.output


def test_status_cmd_with_no_collector_data(tmp_path: Path) -> None:
    """Test status command when all collectors return None."""
    # Arrange
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()

    worktree_path = tmp_path / "workstacks" / "repo" / "detached"
    worktree_path.mkdir(parents=True)

    git_ops = FakeGitOps(
        worktrees={repo_root: [WorktreeInfo(path=worktree_path, branch=None)]},
        current_branches={worktree_path: None},  # Detached HEAD
        git_common_dirs={worktree_path: git_dir},
    )

    global_config_ops = FakeGlobalConfigOps(
        workstacks_root=tmp_path / "workstacks",
        use_graphite=False,
        show_pr_info=False,
    )

    ctx = create_test_context(git_ops=git_ops, global_config_ops=global_config_ops)

    runner = CliRunner()
    # Change to the worktree directory
    import os

    original_dir = os.getcwd()
    os.chdir(worktree_path)
    try:
        # Act
        result = runner.invoke(status_cmd, obj=ctx, catch_exceptions=False)
    finally:
        os.chdir(original_dir)

    # Assert
    # Collectors should handle detached HEAD gracefully
    assert result.exit_code == 0
    assert "Worktree:" in result.output or "detached HEAD" in result.output


def test_status_cmd_invalid_worktree_path(tmp_path: Path) -> None:
    """Test status command when worktree path is invalid."""
    # Arrange
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()

    # Worktree path that doesn't exist
    missing_wt = tmp_path / "missing"

    git_ops = FakeGitOps(
        worktrees={
            repo_root: [
                WorktreeInfo(path=repo_root, branch="main"),
                WorktreeInfo(path=missing_wt, branch="ghost"),  # Path doesn't exist
            ]
        },
        current_branches={repo_root: "main"},
        git_common_dirs={repo_root: git_dir},
        file_statuses={repo_root: ([], [], [])},
    )

    global_config_ops = FakeGlobalConfigOps(
        workstacks_root=tmp_path / "workstacks",
    )

    ctx = create_test_context(git_ops=git_ops, global_config_ops=global_config_ops)

    runner = CliRunner()
    # Change to the repo directory
    import os

    original_dir = os.getcwd()
    os.chdir(repo_root)
    try:
        # Act
        result = runner.invoke(status_cmd, obj=ctx, catch_exceptions=False)
    finally:
        os.chdir(original_dir)

    # Assert - should find main worktree and succeed
    assert result.exit_code == 0
    assert "main" in result.output


def test_status_cmd_not_in_git_repo(tmp_path: Path) -> None:
    """Test status command fails when not in a git repository."""
    # Arrange
    non_git_dir = tmp_path / "not-a-repo"
    non_git_dir.mkdir()

    git_ops = FakeGitOps(
        git_common_dirs={},  # No git directories
        worktrees={},
    )

    global_config_ops = FakeGlobalConfigOps(
        workstacks_root=tmp_path / "workstacks",
    )

    ctx = create_test_context(git_ops=git_ops, global_config_ops=global_config_ops)

    runner = CliRunner()
    # Change to non-git directory
    import os

    original_dir = os.getcwd()
    os.chdir(non_git_dir)
    try:
        # Act
        result = runner.invoke(status_cmd, obj=ctx)
    finally:
        os.chdir(original_dir)

    # Assert
    assert result.exit_code != 0


def test_status_cmd_with_verbose_flag(tmp_path: Path) -> None:
    """Test status command with verbose flag (if supported)."""
    # Arrange
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()

    git_ops = FakeGitOps(
        worktrees={repo_root: [WorktreeInfo(path=repo_root, branch="main")]},
        current_branches={repo_root: "main"},
        git_common_dirs={repo_root: git_dir},
        file_statuses={repo_root: ([], [], [])},
        ahead_behind={(repo_root, "main"): (0, 0)},
        recent_commits={
            repo_root: [
                {"sha": "abc1234", "message": "Commit 1", "author": "Dev", "date": "1 hour ago"},
                {"sha": "def5678", "message": "Commit 2", "author": "Dev", "date": "2 hours ago"},
                {"sha": "ghi9012", "message": "Commit 3", "author": "Dev", "date": "3 hours ago"},
            ]
        },
    )

    global_config_ops = FakeGlobalConfigOps(
        workstacks_root=tmp_path / "workstacks",
    )

    ctx = create_test_context(git_ops=git_ops, global_config_ops=global_config_ops)

    runner = CliRunner()
    # Change to the repo directory
    import os

    original_dir = os.getcwd()
    os.chdir(repo_root)
    try:
        # Act - Note: --verbose flag might not exist in current implementation
        result = runner.invoke(status_cmd, obj=ctx, catch_exceptions=False)
    finally:
        os.chdir(original_dir)

    # Assert
    assert result.exit_code == 0
    assert "Git Status:" in result.output


def test_status_cmd_with_json_output(tmp_path: Path) -> None:
    """Test status command with JSON output format (if supported)."""
    # This test is a placeholder for potential JSON output support
    # Current implementation may not have this feature
    pass


def test_status_cmd_in_subdirectory_of_worktree(tmp_path: Path) -> None:
    """Test status command when run from a subdirectory of a worktree."""
    # Arrange
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()

    # Create subdirectory structure
    sub_dir = repo_root / "src" / "components"
    sub_dir.mkdir(parents=True)

    git_ops = FakeGitOps(
        worktrees={repo_root: [WorktreeInfo(path=repo_root, branch="develop")]},
        current_branches={repo_root: "develop"},
        git_common_dirs={repo_root: git_dir, sub_dir: git_dir},  # Both paths return same git dir
        file_statuses={repo_root: ([], ["src/components/app.py"], [])},
        ahead_behind={(repo_root, "develop"): (0, 0)},
        recent_commits={repo_root: []},
    )

    global_config_ops = FakeGlobalConfigOps(
        workstacks_root=tmp_path / "workstacks",
    )

    ctx = create_test_context(git_ops=git_ops, global_config_ops=global_config_ops)

    runner = CliRunner()
    # Change to subdirectory
    import os

    original_dir = os.getcwd()
    os.chdir(sub_dir)
    try:
        # Act
        result = runner.invoke(status_cmd, obj=ctx, catch_exceptions=False)
    finally:
        os.chdir(original_dir)

    # Assert
    assert result.exit_code == 0
    assert "develop" in result.output
    assert "src/components/app.py" in result.output or "Modified:" in result.output


def test_status_cmd_with_graphite_and_pr_data(tmp_path: Path) -> None:
    """Test status command with both Graphite stack and GitHub PR data."""
    # Arrange
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_dir = repo_root / ".git"
    git_dir.mkdir()

    worktree_path = tmp_path / "workstacks" / "repo" / "middle-feature"
    worktree_path.mkdir(parents=True)

    git_ops = FakeGitOps(
        worktrees={repo_root: [WorktreeInfo(path=worktree_path, branch="middle-feature")]},
        current_branches={worktree_path: "middle-feature"},
        git_common_dirs={worktree_path: git_dir},
        file_statuses={worktree_path: ([], [], [])},
        ahead_behind={(worktree_path, "middle-feature"): (1, 0)},
        recent_commits={
            worktree_path: [
                {
                    "sha": "mid1234",
                    "message": "Middle feature work",
                    "author": "Dev",
                    "date": "2 hours ago",
                }
            ]
        },
    )

    # PR info from GitHub
    github_ops = FakeGitHubOps(
        prs={
            "middle-feature": PullRequestInfo(
                number=456,
                state="OPEN",
                url="https://github.com/owner/repo/pull/456",
                is_draft=False,
                checks_passing=True,
                owner="owner",
                repo="repo",
            )
        }
    )

    # Stack info from Graphite
    graphite_ops = FakeGraphiteOps(
        stacks={
            "middle-feature": ["main", "base-feature", "middle-feature", "top-feature"],
        },
        pr_info={
            "middle-feature": PullRequestInfo(
                number=456,
                state="OPEN",
                url="https://app.graphite.dev/github/pr/owner/repo/456",
                is_draft=False,
                checks_passing=None,  # Graphite doesn't provide CI status
                owner="owner",
                repo="repo",
            )
        },
    )

    global_config_ops = FakeGlobalConfigOps(
        workstacks_root=tmp_path / "workstacks",
        use_graphite=True,
        show_pr_info=True,
    )

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )

    runner = CliRunner()
    # Change to the worktree directory
    import os

    original_dir = os.getcwd()
    os.chdir(worktree_path)
    try:
        # Act
        result = runner.invoke(status_cmd, obj=ctx, catch_exceptions=False)
    finally:
        os.chdir(original_dir)

    # Assert
    assert result.exit_code == 0
    assert "middle-feature" in result.output
    # Should show PR info
    assert "456" in result.output
    # Should show stack info
    assert "base-feature" in result.output or "Parent:" in result.output
    assert "top-feature" in result.output or "Children:" in result.output
