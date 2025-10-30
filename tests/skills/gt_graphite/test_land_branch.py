"""Tests for land_branch.py script."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add script to path
SCRIPT_DIR = Path(__file__).parent.parent.parent.parent / ".claude/skills/gt-graphite/scripts"
sys.path.insert(0, str(SCRIPT_DIR))

# Import after path modification - noqa suppresses E402 (module import not at top)
from land_branch import (  # noqa: E402
    LandBranchError,
    LandBranchSuccess,
    get_children_branches,
    get_current_branch,
    get_parent_branch,
    get_pr_info,
    land_branch,
    merge_pr,
    navigate_to_child,
)


class TestGetCurrentBranch:
    """Tests for get_current_branch()."""

    def test_returns_branch_name(self) -> None:
        """Test getting current branch name."""
        mock_result = Mock()
        mock_result.stdout = "feature-branch\n"

        with patch("land_branch.subprocess.run", return_value=mock_result) as mock_run:
            result = get_current_branch()

            mock_run.assert_called_once_with(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            )
            assert result == "feature-branch"

    def test_strips_whitespace(self) -> None:
        """Test that whitespace is stripped from branch name."""
        mock_result = Mock()
        mock_result.stdout = "  feature-branch  \n"

        with patch("land_branch.subprocess.run", return_value=mock_result):
            result = get_current_branch()

            assert result == "feature-branch"


class TestGetParentBranch:
    """Tests for get_parent_branch()."""

    def test_returns_parent_when_exists(self) -> None:
        """Test getting parent branch."""
        mock_result = Mock()
        mock_result.stdout = "main\n"
        mock_result.returncode = 0

        with patch("land_branch.subprocess.run", return_value=mock_result) as mock_run:
            result = get_parent_branch()

            mock_run.assert_called_once_with(
                ["gt", "parent"],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result == "main"

    def test_returns_none_when_command_fails(self) -> None:
        """Test returns None when gt parent fails."""
        mock_result = Mock()
        mock_result.returncode = 1

        with patch("land_branch.subprocess.run", return_value=mock_result):
            result = get_parent_branch()

            assert result is None

    def test_strips_whitespace(self) -> None:
        """Test that whitespace is stripped from parent name."""
        mock_result = Mock()
        mock_result.stdout = "  main  \n"
        mock_result.returncode = 0

        with patch("land_branch.subprocess.run", return_value=mock_result):
            result = get_parent_branch()

            assert result == "main"


class TestGetChildrenBranches:
    """Tests for get_children_branches()."""

    def test_returns_empty_list_when_no_children(self) -> None:
        """Test returns empty list when branch has no children."""
        mock_result = Mock()
        mock_result.stdout = "\n"
        mock_result.returncode = 0

        with patch("land_branch.subprocess.run", return_value=mock_result):
            result = get_children_branches()

            assert result == []

    def test_returns_empty_list_when_output_is_empty_string(self) -> None:
        """Test returns empty list when output is completely empty."""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.returncode = 0

        with patch("land_branch.subprocess.run", return_value=mock_result):
            result = get_children_branches()

            assert result == []

    def test_returns_children_list(self) -> None:
        """Test returns list of child branches."""
        mock_result = Mock()
        mock_result.stdout = "child1\nchild2\n"
        mock_result.returncode = 0

        with patch("land_branch.subprocess.run", return_value=mock_result) as mock_run:
            result = get_children_branches()

            mock_run.assert_called_once_with(
                ["gt", "children"],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result == ["child1", "child2"]

    def test_returns_single_child(self) -> None:
        """Test returns list with single child."""
        mock_result = Mock()
        mock_result.stdout = "child1\n"
        mock_result.returncode = 0

        with patch("land_branch.subprocess.run", return_value=mock_result):
            result = get_children_branches()

            assert result == ["child1"]

    def test_returns_empty_list_when_command_fails(self) -> None:
        """Test returns empty list when gt children fails."""
        mock_result = Mock()
        mock_result.returncode = 1

        with patch("land_branch.subprocess.run", return_value=mock_result):
            result = get_children_branches()

            assert result == []

    def test_strips_whitespace_from_children(self) -> None:
        """Test that whitespace is stripped from child names."""
        mock_result = Mock()
        mock_result.stdout = "  child1  \n  child2  \n"
        mock_result.returncode = 0

        with patch("land_branch.subprocess.run", return_value=mock_result):
            result = get_children_branches()

            assert result == ["child1", "child2"]


class TestGetPrInfo:
    """Tests for get_pr_info()."""

    def test_returns_pr_info_when_exists(self) -> None:
        """Test getting PR info when PR exists."""
        mock_result = Mock()
        mock_result.stdout = json.dumps({"number": 123, "state": "OPEN"})
        mock_result.returncode = 0

        with patch("land_branch.subprocess.run", return_value=mock_result) as mock_run:
            result = get_pr_info()

            mock_run.assert_called_once_with(
                ["gh", "pr", "view", "--json", "state,number"],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result == (123, "OPEN")

    def test_returns_none_when_no_pr(self) -> None:
        """Test returns None when no PR exists."""
        mock_result = Mock()
        mock_result.returncode = 1

        with patch("land_branch.subprocess.run", return_value=mock_result):
            result = get_pr_info()

            assert result is None

    def test_parses_merged_pr(self) -> None:
        """Test parsing PR in MERGED state."""
        mock_result = Mock()
        mock_result.stdout = json.dumps({"number": 456, "state": "MERGED"})
        mock_result.returncode = 0

        with patch("land_branch.subprocess.run", return_value=mock_result):
            result = get_pr_info()

            assert result == (456, "MERGED")

    def test_parses_closed_pr(self) -> None:
        """Test parsing PR in CLOSED state."""
        mock_result = Mock()
        mock_result.stdout = json.dumps({"number": 789, "state": "CLOSED"})
        mock_result.returncode = 0

        with patch("land_branch.subprocess.run", return_value=mock_result):
            result = get_pr_info()

            assert result == (789, "CLOSED")


class TestMergePr:
    """Tests for merge_pr()."""

    def test_returns_true_on_success(self) -> None:
        """Test successful PR merge."""
        mock_result = Mock()
        mock_result.returncode = 0

        with patch("land_branch.subprocess.run", return_value=mock_result) as mock_run:
            result = merge_pr()

            mock_run.assert_called_once_with(
                ["gh", "pr", "merge", "-s"],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result is True

    def test_returns_false_on_failure(self) -> None:
        """Test failed PR merge."""
        mock_result = Mock()
        mock_result.returncode = 1

        with patch("land_branch.subprocess.run", return_value=mock_result):
            result = merge_pr()

            assert result is False


class TestNavigateToChild:
    """Tests for navigate_to_child()."""

    def test_returns_true_on_success(self) -> None:
        """Test successful navigation to child."""
        mock_result = Mock()
        mock_result.returncode = 0

        with patch("land_branch.subprocess.run", return_value=mock_result) as mock_run:
            result = navigate_to_child("child-branch")

            mock_run.assert_called_once_with(
                ["gt", "up"],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result is True

    def test_returns_false_on_failure(self) -> None:
        """Test failed navigation."""
        mock_result = Mock()
        mock_result.returncode = 1

        with patch("land_branch.subprocess.run", return_value=mock_result):
            result = navigate_to_child("child-branch")

            assert result is False


class TestLandBranch:
    """Integration tests for land_branch() function."""

    def test_success_no_children(self) -> None:
        """Test successful branch landing with no children."""
        with (
            patch("land_branch.get_current_branch", return_value="feature-branch"),
            patch("land_branch.get_parent_branch", return_value="main"),
            patch("land_branch.get_pr_info", return_value=(123, "OPEN")),
            patch("land_branch.get_children_branches", return_value=[]),
            patch("land_branch.merge_pr", return_value=True),
        ):
            result = land_branch()

            assert isinstance(result, LandBranchSuccess)
            assert result.success is True
            assert result.pr_number == 123
            assert result.branch_name == "feature-branch"
            assert result.child_branch is None
            assert "Successfully merged PR #123" in result.message
            assert "feature-branch" in result.message

    def test_success_with_child(self) -> None:
        """Test successful branch landing with child navigation."""
        with (
            patch("land_branch.get_current_branch", return_value="feature-branch"),
            patch("land_branch.get_parent_branch", return_value="main"),
            patch("land_branch.get_pr_info", return_value=(123, "OPEN")),
            patch("land_branch.get_children_branches", return_value=["child-branch"]),
            patch("land_branch.merge_pr", return_value=True),
            patch("land_branch.navigate_to_child", return_value=True),
        ):
            result = land_branch()

            assert isinstance(result, LandBranchSuccess)
            assert result.success is True
            assert result.child_branch == "child-branch"

    def test_success_with_child_navigation_fails(self) -> None:
        """Test successful merge but failed navigation to child."""
        with (
            patch("land_branch.get_current_branch", return_value="feature-branch"),
            patch("land_branch.get_parent_branch", return_value="main"),
            patch("land_branch.get_pr_info", return_value=(123, "OPEN")),
            patch("land_branch.get_children_branches", return_value=["child-branch"]),
            patch("land_branch.merge_pr", return_value=True),
            patch("land_branch.navigate_to_child", return_value=False),
        ):
            result = land_branch()

            assert isinstance(result, LandBranchSuccess)
            assert result.success is True
            assert result.child_branch is None  # Navigation failed

    def test_error_parent_not_found(self) -> None:
        """Test error when parent cannot be determined."""
        with (
            patch("land_branch.get_current_branch", return_value="feature-branch"),
            patch("land_branch.get_parent_branch", return_value=None),
        ):
            result = land_branch()

            assert isinstance(result, LandBranchError)
            assert result.success is False
            assert result.error_type == "parent_not_main"
            assert "Could not determine parent branch" in result.message
            assert result.details["current_branch"] == "feature-branch"

    def test_error_parent_not_main(self) -> None:
        """Test error when parent is not main."""
        with (
            patch("land_branch.get_current_branch", return_value="feature-branch"),
            patch("land_branch.get_parent_branch", return_value="other-branch"),
        ):
            result = land_branch()

            assert isinstance(result, LandBranchError)
            assert result.success is False
            assert result.error_type == "parent_not_main"
            assert "must be exactly one level up from main" in result.message
            assert result.details["current_branch"] == "feature-branch"
            assert result.details["parent_branch"] == "other-branch"

    def test_error_no_pr(self) -> None:
        """Test error when no PR exists."""
        with (
            patch("land_branch.get_current_branch", return_value="feature-branch"),
            patch("land_branch.get_parent_branch", return_value="main"),
            patch("land_branch.get_pr_info", return_value=None),
        ):
            result = land_branch()

            assert isinstance(result, LandBranchError)
            assert result.success is False
            assert result.error_type == "no_pr_found"
            assert "No pull request found" in result.message
            assert result.details["current_branch"] == "feature-branch"

    def test_error_pr_not_open(self) -> None:
        """Test error when PR is not open."""
        with (
            patch("land_branch.get_current_branch", return_value="feature-branch"),
            patch("land_branch.get_parent_branch", return_value="main"),
            patch("land_branch.get_pr_info", return_value=(123, "MERGED")),
        ):
            result = land_branch()

            assert isinstance(result, LandBranchError)
            assert result.success is False
            assert result.error_type == "pr_not_open"
            assert "not open" in result.message
            assert result.details["pr_number"] == 123
            assert result.details["pr_state"] == "MERGED"

    def test_error_pr_closed(self) -> None:
        """Test error when PR is closed."""
        with (
            patch("land_branch.get_current_branch", return_value="feature-branch"),
            patch("land_branch.get_parent_branch", return_value="main"),
            patch("land_branch.get_pr_info", return_value=(456, "CLOSED")),
        ):
            result = land_branch()

            assert isinstance(result, LandBranchError)
            assert result.error_type == "pr_not_open"
            assert result.details["pr_state"] == "CLOSED"

    def test_error_multiple_children(self) -> None:
        """Test error when branch has multiple children."""
        with (
            patch("land_branch.get_current_branch", return_value="feature-branch"),
            patch("land_branch.get_parent_branch", return_value="main"),
            patch("land_branch.get_pr_info", return_value=(123, "OPEN")),
            patch("land_branch.get_children_branches", return_value=["child1", "child2"]),
        ):
            result = land_branch()

            assert isinstance(result, LandBranchError)
            assert result.success is False
            assert result.error_type == "multiple_children"
            assert "multiple children" in result.message
            assert result.details["current_branch"] == "feature-branch"
            assert result.details["children"] == ["child1", "child2"]

    def test_error_multiple_children_with_three(self) -> None:
        """Test error when branch has three children."""
        with (
            patch("land_branch.get_current_branch", return_value="feature-branch"),
            patch("land_branch.get_parent_branch", return_value="main"),
            patch("land_branch.get_pr_info", return_value=(123, "OPEN")),
            patch("land_branch.get_children_branches", return_value=["child1", "child2", "child3"]),
        ):
            result = land_branch()

            assert isinstance(result, LandBranchError)
            assert result.error_type == "multiple_children"
            assert len(result.details["children"]) == 3

    def test_error_merge_failed(self) -> None:
        """Test error when merge fails."""
        with (
            patch("land_branch.get_current_branch", return_value="feature-branch"),
            patch("land_branch.get_parent_branch", return_value="main"),
            patch("land_branch.get_pr_info", return_value=(123, "OPEN")),
            patch("land_branch.get_children_branches", return_value=[]),
            patch("land_branch.merge_pr", return_value=False),
        ):
            result = land_branch()

            assert isinstance(result, LandBranchError)
            assert result.success is False
            assert result.error_type == "merge_failed"
            assert "Failed to merge PR #123" in result.message
            assert result.details["current_branch"] == "feature-branch"
            assert result.details["pr_number"] == 123
