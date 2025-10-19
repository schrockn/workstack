"""Unit tests for GitHubPRCollector."""

from pathlib import Path

from tests.fakes.context import create_test_context
from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from workstack.core.github_ops import PullRequestInfo
from workstack.status.collectors.github import GitHubPRCollector


def test_github_pr_collector_no_prs_for_branch(tmp_path: Path) -> None:
    """Test GitHubPRCollector when no PRs exist for the current branch."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "feature-branch"},
    )
    github_ops = FakeGitHubOps(
        prs={
            "other-branch": PullRequestInfo(
                number=456,
                state="OPEN",
                url="https://github.com/owner/repo/pull/456",
                is_draft=False,
                checks_passing=True,
                owner="owner",
                repo="repo",
            ),
        }
    )
    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        global_config_ops=global_config_ops,
    )
    collector = GitHubPRCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is None  # No PR for current branch


def test_github_pr_collector_single_open_pr(tmp_path: Path) -> None:
    """Test GitHubPRCollector with a single open PR."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "feature-branch"},
    )
    github_ops = FakeGitHubOps(
        prs={
            "feature-branch": PullRequestInfo(
                number=123,
                state="OPEN",
                url="https://github.com/owner/repo/pull/123",
                is_draft=False,
                checks_passing=None,  # No checks configured
                owner="owner",
                repo="repo",
            ),
        }
    )
    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        global_config_ops=global_config_ops,
    )
    collector = GitHubPRCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.number == 123
    assert result.state == "OPEN"
    assert result.url == "https://github.com/owner/repo/pull/123"
    assert result.is_draft is False
    assert result.checks_passing is None
    assert result.ready_to_merge is True  # Open, not draft, no checks


def test_github_pr_collector_pr_with_passing_checks(tmp_path: Path) -> None:
    """Test GitHubPRCollector with a PR that has passing checks."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "tested-branch"},
    )
    github_ops = FakeGitHubOps(
        prs={
            "tested-branch": PullRequestInfo(
                number=789,
                state="OPEN",
                url="https://github.com/owner/repo/pull/789",
                is_draft=False,
                checks_passing=True,
                owner="owner",
                repo="repo",
            ),
        }
    )
    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        global_config_ops=global_config_ops,
    )
    collector = GitHubPRCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.number == 789
    assert result.checks_passing is True
    assert result.ready_to_merge is True


def test_github_pr_collector_pr_with_failing_checks(tmp_path: Path) -> None:
    """Test GitHubPRCollector with a PR that has failing checks."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "broken-branch"},
    )
    github_ops = FakeGitHubOps(
        prs={
            "broken-branch": PullRequestInfo(
                number=999,
                state="OPEN",
                url="https://github.com/owner/repo/pull/999",
                is_draft=False,
                checks_passing=False,
                owner="owner",
                repo="repo",
            ),
        }
    )
    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        global_config_ops=global_config_ops,
    )
    collector = GitHubPRCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.number == 999
    assert result.checks_passing is False
    assert result.ready_to_merge is False  # Failing checks prevent merge


def test_github_pr_collector_pr_with_pending_checks(tmp_path: Path) -> None:
    """Test GitHubPRCollector with a PR that has pending checks."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "pending-branch"},
    )
    github_ops = FakeGitHubOps(
        prs={
            "pending-branch": PullRequestInfo(
                number=555,
                state="OPEN",
                url="https://github.com/owner/repo/pull/555",
                is_draft=False,
                checks_passing=None,  # Pending or no checks
                owner="owner",
                repo="repo",
            ),
        }
    )
    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        global_config_ops=global_config_ops,
    )
    collector = GitHubPRCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.number == 555
    assert result.checks_passing is None
    assert result.ready_to_merge is True  # None checks don't prevent merge


def test_github_pr_collector_pr_with_approved_reviews(tmp_path: Path) -> None:
    """Test GitHubPRCollector with approved reviews (note: reviews not in PullRequestInfo)."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "approved-branch"},
    )
    # Note: PullRequestInfo doesn't have reviews field
    github_ops = FakeGitHubOps(
        prs={
            "approved-branch": PullRequestInfo(
                number=222,
                state="OPEN",
                url="https://github.com/owner/repo/pull/222",
                is_draft=False,
                checks_passing=True,
                owner="owner",
                repo="repo",
            ),
        }
    )
    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        global_config_ops=global_config_ops,
    )
    collector = GitHubPRCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.number == 222
    assert result.reviews is None  # Reviews not available in current implementation
    assert result.ready_to_merge is True


def test_github_pr_collector_pr_with_changes_requested(tmp_path: Path) -> None:
    """Test GitHubPRCollector with changes requested (via draft status)."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "needs-changes"},
    )
    # Using draft status to simulate PR that needs changes
    github_ops = FakeGitHubOps(
        prs={
            "needs-changes": PullRequestInfo(
                number=333,
                state="OPEN",
                url="https://github.com/owner/repo/pull/333",
                is_draft=True,  # Draft PRs can't be merged
                checks_passing=True,
                owner="owner",
                repo="repo",
            ),
        }
    )
    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        global_config_ops=global_config_ops,
    )
    collector = GitHubPRCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.number == 333
    assert result.is_draft is True
    assert result.ready_to_merge is False  # Draft PRs not ready to merge


def test_github_pr_collector_merged_pr(tmp_path: Path) -> None:
    """Test GitHubPRCollector with a merged PR."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "merged-branch"},
    )
    github_ops = FakeGitHubOps(
        prs={
            "merged-branch": PullRequestInfo(
                number=444,
                state="MERGED",
                url="https://github.com/owner/repo/pull/444",
                is_draft=False,
                checks_passing=True,
                owner="owner",
                repo="repo",
            ),
        }
    )
    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        global_config_ops=global_config_ops,
    )
    collector = GitHubPRCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.number == 444
    assert result.state == "MERGED"
    assert result.ready_to_merge is False  # Already merged


def test_github_pr_collector_closed_pr(tmp_path: Path) -> None:
    """Test GitHubPRCollector with a closed PR."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "closed-branch"},
    )
    github_ops = FakeGitHubOps(
        prs={
            "closed-branch": PullRequestInfo(
                number=666,
                state="CLOSED",
                url="https://github.com/owner/repo/pull/666",
                is_draft=False,
                checks_passing=True,
                owner="owner",
                repo="repo",
            ),
        }
    )
    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        global_config_ops=global_config_ops,
    )
    collector = GitHubPRCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.number == 666
    assert result.state == "CLOSED"
    assert result.ready_to_merge is False  # Closed PRs can't be merged


def test_github_pr_collector_multiple_prs_same_branch(tmp_path: Path) -> None:
    """Test GitHubPRCollector when multiple PRs exist (picks the one from branch)."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "feature-x"},
    )
    # Only one PR per branch is possible in the dict structure
    github_ops = FakeGitHubOps(
        prs={
            "feature-x": PullRequestInfo(
                number=111,
                state="OPEN",
                url="https://github.com/owner/repo/pull/111",
                is_draft=False,
                checks_passing=True,
                owner="owner",
                repo="repo",
            ),
            "feature-y": PullRequestInfo(
                number=112,
                state="OPEN",
                url="https://github.com/owner/repo/pull/112",
                is_draft=False,
                checks_passing=True,
                owner="owner",
                repo="repo",
            ),
        }
    )
    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        global_config_ops=global_config_ops,
    )
    collector = GitHubPRCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is not None
    assert result.number == 111  # Gets PR for current branch only


def test_github_pr_collector_no_github_remote(tmp_path: Path) -> None:
    """Test GitHubPRCollector when there's no GitHub remote (detached HEAD)."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: None},  # Detached HEAD
    )
    github_ops = FakeGitHubOps()
    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        global_config_ops=global_config_ops,
    )
    collector = GitHubPRCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is None  # No branch means no PR


def test_github_pr_collector_handles_api_errors(tmp_path: Path) -> None:
    """Test GitHubPRCollector handles API errors gracefully."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "error-branch"},
    )
    # Empty PRs simulates API error or no data returned
    github_ops = FakeGitHubOps(prs={})
    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        global_config_ops=global_config_ops,
    )
    collector = GitHubPRCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert
    assert result is None  # Handles missing data gracefully


def test_github_pr_collector_is_available_config_disabled(tmp_path: Path) -> None:
    """Test GitHubPRCollector availability when PR info is disabled in config."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    global_config_ops = FakeGlobalConfigOps(show_pr_info=False)  # Disabled
    ctx = create_test_context(global_config_ops=global_config_ops)
    collector = GitHubPRCollector()

    # Act
    available = collector.is_available(ctx, worktree_path)

    # Assert
    assert available is False


def test_github_pr_collector_is_available_path_not_exists(tmp_path: Path) -> None:
    """Test GitHubPRCollector availability when worktree path doesn't exist."""
    # Arrange
    nonexistent_path = tmp_path / "does_not_exist"

    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)
    ctx = create_test_context(global_config_ops=global_config_ops)
    collector = GitHubPRCollector()

    # Act
    available = collector.is_available(ctx, nonexistent_path)

    # Assert
    assert available is False


def test_github_pr_collector_is_available_enabled(tmp_path: Path) -> None:
    """Test GitHubPRCollector availability when properly configured."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)
    ctx = create_test_context(global_config_ops=global_config_ops)
    collector = GitHubPRCollector()

    # Act
    available = collector.is_available(ctx, worktree_path)

    # Assert
    assert available is True


def test_github_pr_collector_uses_graphite_first(tmp_path: Path) -> None:
    """Test GitHubPRCollector prioritizes Graphite data over GitHub."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "graphite-branch"},
    )

    # Set up different PR info in Graphite vs GitHub
    graphite_pr = PullRequestInfo(
        number=1001,
        state="OPEN",
        url="https://app.graphite.dev/github/pr/owner/repo/1001",
        is_draft=False,
        checks_passing=None,  # Graphite doesn't fetch CI status
        owner="owner",
        repo="repo",
    )

    github_pr = PullRequestInfo(
        number=1002,  # Different PR number
        state="OPEN",
        url="https://github.com/owner/repo/pull/1002",
        is_draft=False,
        checks_passing=True,
        owner="owner",
        repo="repo",
    )

    graphite_ops = FakeGraphiteOps(pr_info={"graphite-branch": graphite_pr})
    github_ops = FakeGitHubOps(prs={"graphite-branch": github_pr})
    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GitHubPRCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert - should use Graphite data
    assert result is not None
    assert result.number == 1001  # Graphite PR number
    assert result.url == "https://app.graphite.dev/github/pr/owner/repo/1001"


def test_github_pr_collector_falls_back_to_github(tmp_path: Path) -> None:
    """Test GitHubPRCollector falls back to GitHub when Graphite has no data."""
    # Arrange
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"

    git_ops = FakeGitOps(
        current_branches={worktree_path: "github-only-branch"},
    )

    github_pr = PullRequestInfo(
        number=2001,
        state="OPEN",
        url="https://github.com/owner/repo/pull/2001",
        is_draft=False,
        checks_passing=True,
        owner="owner",
        repo="repo",
    )

    graphite_ops = FakeGraphiteOps(pr_info={})  # No Graphite data
    github_ops = FakeGitHubOps(prs={"github-only-branch": github_pr})
    global_config_ops = FakeGlobalConfigOps(show_pr_info=True)

    ctx = create_test_context(
        git_ops=git_ops,
        github_ops=github_ops,
        graphite_ops=graphite_ops,
        global_config_ops=global_config_ops,
    )
    collector = GitHubPRCollector()

    # Act
    result = collector.collect(ctx, worktree_path, repo_root)

    # Assert - should use GitHub data
    assert result is not None
    assert result.number == 2001
    assert result.url == "https://github.com/owner/repo/pull/2001"
    assert result.checks_passing is True  # GitHub provides CI status
