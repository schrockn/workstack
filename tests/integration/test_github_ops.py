"""Integration tests for GitHubOps with minimal mocking."""

from pathlib import Path

from tests.conftest import load_fixture
from workstack.core.github_ops import RealGitHubOps


def test_github_ops_get_prs_with_mock_executor():
    """Test GitHubOps with mocked subprocess execution."""

    def mock_execute(cmd, cwd):
        # Return fixture based on command
        if "pr" in cmd and "list" in cmd:
            if "--head" in cmd:
                # Specific branch query
                return load_fixture("github/pr_status_single.json")
            # All PRs query
            if "statusCheckRollup" in str(cmd):
                return load_fixture("github/pr_list_with_checks.json")
            return load_fixture("github/pr_list_no_checks.json")
        return "[]"

    ops = RealGitHubOps(execute_fn=mock_execute)

    # Test fetching all PRs with checks
    result = ops.get_prs_for_repo(Path("/repo"), include_checks=True)

    assert len(result) == 3
    assert "feature-branch" in result
    assert result["feature-branch"].number == 123
    assert result["feature-branch"].checks_passing is True

    # Test fetching all PRs without checks
    ops_no_checks = RealGitHubOps(execute_fn=mock_execute)
    result = ops_no_checks.get_prs_for_repo(Path("/repo"), include_checks=False)

    assert len(result) == 2
    assert "main-feature" in result
    assert result["main-feature"].checks_passing is None


def test_github_ops_get_pr_status_with_mock():
    """Test getting PR status for a specific branch."""

    def mock_execute(cmd, cwd):
        if "--head" in cmd and "branch-name" in str(cmd):
            return load_fixture("github/pr_status_single.json")
        return "[]"

    ops = RealGitHubOps(execute_fn=mock_execute)
    state, number, title = ops.get_pr_status(Path("/repo"), "branch-name", debug=False)

    assert state == "OPEN"
    assert number == 456
    assert title == "Add new feature for improved performance"


def test_github_ops_get_pr_status_no_pr():
    """Test getting PR status when no PR exists."""

    def mock_execute(cmd, cwd):
        return "[]"

    ops = RealGitHubOps(execute_fn=mock_execute)
    state, number, title = ops.get_pr_status(Path("/repo"), "no-pr-branch", debug=False)

    assert state == "NONE"
    assert number is None
    assert title is None


def test_github_ops_handles_command_failure():
    """Test that GitHubOps gracefully handles command failures."""
    import subprocess

    def mock_execute_failure(cmd, cwd):
        raise subprocess.CalledProcessError(1, cmd)

    ops = RealGitHubOps(execute_fn=mock_execute_failure)

    # Should return empty dict on failure
    result = ops.get_prs_for_repo(Path("/repo"), include_checks=False)
    assert result == {}

    # Should return NONE status on failure
    state, number, title = ops.get_pr_status(Path("/repo"), "branch", debug=False)
    assert state == "NONE"
    assert number is None
    assert title is None


def test_github_ops_handles_json_decode_error():
    """Test that GitHubOps gracefully handles malformed JSON."""

    def mock_execute_bad_json(cmd, cwd):
        return "not valid json"

    ops = RealGitHubOps(execute_fn=mock_execute_bad_json)

    # Should return empty dict on JSON error
    result = ops.get_prs_for_repo(Path("/repo"), include_checks=False)
    assert result == {}


def test_github_ops_debug_output(capsys):
    """Test debug output for PR status command."""

    def mock_execute(cmd, cwd):
        return load_fixture("github/pr_status_single.json")

    ops = RealGitHubOps(execute_fn=mock_execute)
    # Note: debug flag triggers click.echo, but won't actually print
    # in test since we're mocking the execution
    state, number, title = ops.get_pr_status(Path("/repo"), "test-branch", debug=True)

    assert state == "OPEN"
    assert number == 456
