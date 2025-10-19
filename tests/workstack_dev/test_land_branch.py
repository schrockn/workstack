"""Tests for land-branch command."""

import json
from unittest.mock import Mock, patch

from workstack_dev.commands.land_branch.command import (
    LandBranchError,
    LandBranchSuccess,
    get_branch_metadata,
    get_current_branch,
    get_pr_info,
    land_branch,
    merge_pr,
    navigate_to_child,
)


def test_get_current_branch() -> None:
    """Test getting current branch name."""
    mock_result = Mock()
    mock_result.stdout = "feature-branch\n"

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = get_current_branch()

        mock_run.assert_called_once_with(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
        )
        assert result == "feature-branch"


def test_get_branch_metadata_found() -> None:
    """Test getting branch metadata when branch exists."""
    branches_json = {
        "branches": [
            {"name": "main", "parent": None, "children": ["feature-branch"]},
            {"name": "feature-branch", "parent": "main", "children": []},
        ]
    }
    mock_result = Mock()
    mock_result.stdout = json.dumps(branches_json)

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = get_branch_metadata("feature-branch")

        mock_run.assert_called_once_with(
            ["workstack", "graphite", "branches", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        assert result == {"name": "feature-branch", "parent": "main", "children": []}


def test_get_branch_metadata_not_found() -> None:
    """Test getting branch metadata when branch does not exist."""
    branches_json = {
        "branches": [
            {"name": "main", "parent": None, "children": []},
        ]
    }
    mock_result = Mock()
    mock_result.stdout = json.dumps(branches_json)

    with patch("subprocess.run", return_value=mock_result):
        result = get_branch_metadata("nonexistent-branch")

        assert result is None


def test_get_pr_info_found() -> None:
    """Test getting PR info when PR exists."""
    pr_json = {"number": 123, "state": "OPEN"}
    mock_result = Mock()
    mock_result.stdout = json.dumps(pr_json)
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = get_pr_info()

        mock_run.assert_called_once_with(
            ["gh", "pr", "view", "--json", "state,number"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result == (123, "OPEN")


def test_get_pr_info_not_found() -> None:
    """Test getting PR info when no PR exists."""
    mock_result = Mock()
    mock_result.returncode = 1

    with patch("subprocess.run", return_value=mock_result):
        result = get_pr_info()

        assert result is None


def test_merge_pr_success() -> None:
    """Test successful PR merge."""
    mock_result = Mock()
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = merge_pr()

        mock_run.assert_called_once_with(
            ["gh", "pr", "merge", "-s"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result is True


def test_merge_pr_failure() -> None:
    """Test failed PR merge."""
    mock_result = Mock()
    mock_result.returncode = 1

    with patch("subprocess.run", return_value=mock_result):
        result = merge_pr()

        assert result is False


def test_navigate_to_child_success() -> None:
    """Test successful navigation to child branch."""
    mock_up_result = Mock()
    mock_up_result.returncode = 0

    mock_branch_result = Mock()
    mock_branch_result.stdout = "child-branch\n"

    with (
        patch("subprocess.run") as mock_run,
        patch(
            "workstack_dev.commands.land_branch.command.get_current_branch",
            return_value="child-branch",
        ),
    ):
        mock_run.return_value = mock_up_result
        result = navigate_to_child()

        assert result == "child-branch"


def test_navigate_to_child_failure() -> None:
    """Test failed navigation to child branch."""
    mock_result = Mock()
    mock_result.returncode = 1

    with patch("subprocess.run", return_value=mock_result):
        result = navigate_to_child()

        assert result is None


def test_land_branch_success_no_children() -> None:
    """Test successful branch landing with no child branches."""
    with (
        patch(
            "workstack_dev.commands.land_branch.command.get_current_branch",
            return_value="feature-branch",
        ),
        patch(
            "workstack_dev.commands.land_branch.command.get_branch_metadata",
            return_value={"name": "feature-branch", "parent": "main", "children": []},
        ),
        patch(
            "workstack_dev.commands.land_branch.command.get_pr_info",
            return_value=(123, "OPEN"),
        ),
        patch(
            "workstack_dev.commands.land_branch.command.merge_pr",
            return_value=True,
        ),
    ):
        result = land_branch()

        assert isinstance(result, LandBranchSuccess)
        assert result.success is True
        assert result.pr_number == 123
        assert result.branch_name == "feature-branch"
        assert result.child_branch is None
        assert "Successfully merged PR #123" in result.message


def test_land_branch_success_with_child() -> None:
    """Test successful branch landing with navigation to child."""
    with (
        patch(
            "workstack_dev.commands.land_branch.command.get_current_branch",
            return_value="feature-branch",
        ),
        patch(
            "workstack_dev.commands.land_branch.command.get_branch_metadata",
            return_value={
                "name": "feature-branch",
                "parent": "main",
                "children": ["child-branch"],
            },
        ),
        patch(
            "workstack_dev.commands.land_branch.command.get_pr_info",
            return_value=(123, "OPEN"),
        ),
        patch(
            "workstack_dev.commands.land_branch.command.merge_pr",
            return_value=True,
        ),
        patch(
            "workstack_dev.commands.land_branch.command.navigate_to_child",
            return_value="child-branch",
        ),
    ):
        result = land_branch()

        assert isinstance(result, LandBranchSuccess)
        assert result.success is True
        assert result.pr_number == 123
        assert result.branch_name == "feature-branch"
        assert result.child_branch == "child-branch"


def test_land_branch_error_metadata_not_found() -> None:
    """Test error when branch metadata cannot be found."""
    with (
        patch(
            "workstack_dev.commands.land_branch.command.get_current_branch",
            return_value="feature-branch",
        ),
        patch(
            "workstack_dev.commands.land_branch.command.get_branch_metadata",
            return_value=None,
        ),
    ):
        result = land_branch()

        assert isinstance(result, LandBranchError)
        assert result.success is False
        assert result.error_type == "parent_not_main"
        assert "Could not find branch metadata" in result.message
        assert result.details["current_branch"] == "feature-branch"


def test_land_branch_error_parent_not_main() -> None:
    """Test error when parent branch is not main."""
    with (
        patch(
            "workstack_dev.commands.land_branch.command.get_current_branch",
            return_value="feature-branch",
        ),
        patch(
            "workstack_dev.commands.land_branch.command.get_branch_metadata",
            return_value={
                "name": "feature-branch",
                "parent": "other-branch",
                "children": [],
            },
        ),
    ):
        result = land_branch()

        assert isinstance(result, LandBranchError)
        assert result.success is False
        assert result.error_type == "parent_not_main"
        assert "must be exactly one level up from main" in result.message
        assert result.details["current_branch"] == "feature-branch"
        assert result.details["parent_branch"] == "other-branch"


def test_land_branch_error_no_pr_found() -> None:
    """Test error when no PR exists for the branch."""
    with (
        patch(
            "workstack_dev.commands.land_branch.command.get_current_branch",
            return_value="feature-branch",
        ),
        patch(
            "workstack_dev.commands.land_branch.command.get_branch_metadata",
            return_value={"name": "feature-branch", "parent": "main", "children": []},
        ),
        patch(
            "workstack_dev.commands.land_branch.command.get_pr_info",
            return_value=None,
        ),
    ):
        result = land_branch()

        assert isinstance(result, LandBranchError)
        assert result.success is False
        assert result.error_type == "no_pr_found"
        assert "No pull request found" in result.message
        assert "gt submit" in result.message


def test_land_branch_error_pr_not_open() -> None:
    """Test error when PR exists but is not open."""
    with (
        patch(
            "workstack_dev.commands.land_branch.command.get_current_branch",
            return_value="feature-branch",
        ),
        patch(
            "workstack_dev.commands.land_branch.command.get_branch_metadata",
            return_value={"name": "feature-branch", "parent": "main", "children": []},
        ),
        patch(
            "workstack_dev.commands.land_branch.command.get_pr_info",
            return_value=(123, "MERGED"),
        ),
    ):
        result = land_branch()

        assert isinstance(result, LandBranchError)
        assert result.success is False
        assert result.error_type == "pr_not_open"
        assert "not open" in result.message
        assert result.details["pr_state"] == "MERGED"


def test_land_branch_error_multiple_children() -> None:
    """Test error when branch has multiple children."""
    with (
        patch(
            "workstack_dev.commands.land_branch.command.get_current_branch",
            return_value="feature-branch",
        ),
        patch(
            "workstack_dev.commands.land_branch.command.get_branch_metadata",
            return_value={
                "name": "feature-branch",
                "parent": "main",
                "children": ["child1", "child2"],
            },
        ),
        patch(
            "workstack_dev.commands.land_branch.command.get_pr_info",
            return_value=(123, "OPEN"),
        ),
    ):
        result = land_branch()

        assert isinstance(result, LandBranchError)
        assert result.success is False
        assert result.error_type == "multiple_children"
        assert "multiple children" in result.message
        assert result.details["children"] == ["child1", "child2"]


def test_land_branch_error_merge_failed() -> None:
    """Test error when PR merge fails."""
    with (
        patch(
            "workstack_dev.commands.land_branch.command.get_current_branch",
            return_value="feature-branch",
        ),
        patch(
            "workstack_dev.commands.land_branch.command.get_branch_metadata",
            return_value={"name": "feature-branch", "parent": "main", "children": []},
        ),
        patch(
            "workstack_dev.commands.land_branch.command.get_pr_info",
            return_value=(123, "OPEN"),
        ),
        patch(
            "workstack_dev.commands.land_branch.command.merge_pr",
            return_value=False,
        ),
    ):
        result = land_branch()

        assert isinstance(result, LandBranchError)
        assert result.success is False
        assert result.error_type == "merge_failed"
        assert "Failed to merge PR #123" in result.message
