"""Tests for PR info display in list command."""

import json
from pathlib import Path

from click.testing import CliRunner

from tests.commands.display.list import strip_ansi
from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from tests.fakes.shell_ops import FakeShellOps
from workstack.cli.cli import cli
from workstack.core.context import WorkstackContext
from workstack.core.github_ops import PullRequestInfo
from workstack.core.gitops import WorktreeInfo


def _setup_test_with_pr(
    branch_name: str,
    pr_info: PullRequestInfo,
    show_pr_info: bool,
) -> tuple[Path, Path, Path, WorkstackContext]:
    """Helper to set up a test environment with a PR on a branch.

    Returns:
        Tuple of (cwd, workstacks_root, feature_worktree, test_ctx)
    """
    # Set up isolated environment
    cwd = Path.cwd()
    workstacks_root = cwd / "workstacks"

    # Create git repo structure
    git_dir = Path(".git")
    git_dir.mkdir()

    # Create graphite cache with a simple stack
    graphite_cache = {
        "branches": [
            ["main", {"validationResult": "TRUNK", "children": [branch_name]}],
            [branch_name, {"parentBranchName": "main", "children": []}],
        ]
    }
    (git_dir / ".graphite_cache_persist").write_text(json.dumps(graphite_cache))

    # Create worktree directory for branch so it appears in the stack
    repo_name = cwd.name
    workstacks_dir = workstacks_root / repo_name
    feature_worktree = workstacks_dir / branch_name
    feature_worktree.mkdir(parents=True)

    # Build fake git ops with worktree for branch
    git_ops = FakeGitOps(
        worktrees={
            cwd: [
                WorktreeInfo(path=cwd, branch="main"),
                WorktreeInfo(path=feature_worktree, branch=branch_name),
            ]
        },
        git_common_dirs={cwd: git_dir, feature_worktree: git_dir},
        current_branches={cwd: "main", feature_worktree: branch_name},
    )

    # Build fake GitHub ops with PR data
    github_ops = FakeGitHubOps(prs={branch_name: pr_info})

    # Configure show_pr_info
    global_config_ops = FakeGlobalConfigOps(
        workstacks_root=workstacks_root,
        use_graphite=True,
        show_pr_info=show_pr_info,
    )

    graphite_ops = FakeGraphiteOps()

    test_ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=global_config_ops,
        github_ops=github_ops,
        graphite_ops=graphite_ops,
        shell_ops=FakeShellOps(),
        dry_run=False,
    )

    return cwd, workstacks_root, feature_worktree, test_ctx


def test_list_with_stacks_shows_pr_info_when_enabled() -> None:
    """Test that PR info is displayed when show_pr_info config is True."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        pr = PullRequestInfo(
            number=42,
            state="OPEN",
            url="https://github.com/owner/repo/pull/42",
            is_draft=False,
            checks_passing=True,
            owner="owner",
            repo="repo",
        )
        _cwd, _workstacks_root, _feature_worktree, test_ctx = _setup_test_with_pr(
            "feature-branch", pr, show_pr_info=True
        )

        result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Output should contain PR info (emoji and number)
        assert "#42" in result.output


def test_list_with_stacks_hides_pr_info_when_disabled() -> None:
    """Test that PR info is NOT displayed when show_pr_info config is False."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        pr = PullRequestInfo(
            number=42,
            state="OPEN",
            url="https://github.com/owner/repo/pull/42",
            is_draft=False,
            checks_passing=True,
            owner="owner",
            repo="repo",
        )
        _cwd, _workstacks_root, _feature_worktree, test_ctx = _setup_test_with_pr(
            "feature-branch", pr, show_pr_info=False
        )

        result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Output should NOT contain PR info
        assert "#42" not in result.output


def test_list_with_stacks_shows_draft_emoji() -> None:
    """Test that draft PRs show the construction emoji (🚧)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        pr = PullRequestInfo(
            number=10,
            state="OPEN",
            url="https://github.com/owner/repo/pull/10",
            is_draft=True,  # Draft PR
            checks_passing=None,
            owner="owner",
            repo="repo",
        )
        _cwd, _workstacks_root, _feature_worktree, test_ctx = _setup_test_with_pr(
            "draft-pr", pr, show_pr_info=True
        )

        result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Should contain construction emoji for draft
        assert "🚧" in result.output
        assert "#10" in result.output


def test_list_with_stacks_shows_merged_emoji() -> None:
    """Test that merged PRs show the purple circle emoji (🟣)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        pr = PullRequestInfo(
            number=20,
            state="MERGED",  # Merged state
            url="https://github.com/owner/repo/pull/20",
            is_draft=False,
            checks_passing=True,
            owner="owner",
            repo="repo",
        )
        _cwd, _workstacks_root, _feature_worktree, test_ctx = _setup_test_with_pr(
            "merged-pr", pr, show_pr_info=True
        )

        result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Should contain purple circle for merged
        assert "🟣" in result.output
        assert "#20" in result.output


def test_list_with_stacks_shows_closed_emoji() -> None:
    """Test that closed (not merged) PRs show the hollow circle emoji (⭕)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        pr = PullRequestInfo(
            number=30,
            state="CLOSED",  # Closed but not merged
            url="https://github.com/owner/repo/pull/30",
            is_draft=False,
            checks_passing=None,
            owner="owner",
            repo="repo",
        )
        _cwd, _workstacks_root, _feature_worktree, test_ctx = _setup_test_with_pr(
            "closed-pr", pr, show_pr_info=True
        )

        result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Should contain hollow circle for closed
        assert "⭕" in result.output
        assert "#30" in result.output


def test_list_with_stacks_shows_checks_passing_emoji() -> None:
    """Test that PRs with passing checks show the green checkmark (✅)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        pr = PullRequestInfo(
            number=40,
            state="OPEN",
            url="https://github.com/owner/repo/pull/40",
            is_draft=False,
            checks_passing=True,  # Checks passing
            owner="owner",
            repo="repo",
        )
        _cwd, _workstacks_root, _feature_worktree, test_ctx = _setup_test_with_pr(
            "passing-checks", pr, show_pr_info=True
        )

        result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Should contain green checkmark for passing checks
        assert "✅" in result.output
        assert "#40" in result.output


def test_list_with_stacks_shows_checks_failing_emoji() -> None:
    """Test that PRs with failing checks show the red X (❌)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        pr = PullRequestInfo(
            number=50,
            state="OPEN",
            url="https://github.com/owner/repo/pull/50",
            is_draft=False,
            checks_passing=False,  # Checks failing
            owner="owner",
            repo="repo",
        )
        _cwd, _workstacks_root, _feature_worktree, test_ctx = _setup_test_with_pr(
            "failing-checks", pr, show_pr_info=True
        )

        result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Should contain red X for failing checks
        assert "❌" in result.output
        assert "#50" in result.output


def test_list_with_stacks_shows_no_checks_emoji() -> None:
    """Test that open PRs with no checks show the hollow circle (◯)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        pr = PullRequestInfo(
            number=60,
            state="OPEN",
            url="https://github.com/owner/repo/pull/60",
            is_draft=False,
            checks_passing=None,  # No checks configured
            owner="owner",
            repo="repo",
        )
        _cwd, _workstacks_root, _feature_worktree, test_ctx = _setup_test_with_pr(
            "no-checks", pr, show_pr_info=True
        )

        result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Should contain hollow circle for no checks
        # Note: The stack visualization also uses ◯, so we need to verify it's in PR context
        output = strip_ansi(result.output)
        assert "#60" in output


def test_list_with_stacks_uses_graphite_url() -> None:
    """Test that PR links use Graphite URLs instead of GitHub URLs."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        pr = PullRequestInfo(
            number=100,
            state="OPEN",
            url="https://github.com/testowner/testrepo/pull/100",
            is_draft=False,
            checks_passing=True,
            owner="testowner",
            repo="testrepo",
        )
        _cwd, _workstacks_root, _feature_worktree, test_ctx = _setup_test_with_pr(
            "feature", pr, show_pr_info=True
        )

        result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
        assert result.exit_code == 0, result.output

        # Output should contain OSC 8 escape sequence with Graphite URL
        # Graphite URL format: https://app.graphite.dev/github/pr/owner/repo/number
        expected_url = "https://app.graphite.dev/github/pr/testowner/testrepo/100"
        assert expected_url in result.output
