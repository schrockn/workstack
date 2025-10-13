"""Tests for rebase utilities."""

from pathlib import Path

from tests.fakes.rebaseops import FakeRebaseOps
from workstack.core.rebase_utils import (
    count_commits_between,
    create_rebase_plan,
    is_rebase_needed,
    parse_conflict_markers,
)


def test_parse_conflict_markers() -> None:
    """Test parsing git conflict markers."""
    content = """line 1
<<<<<<< HEAD
our change
=======
their change
>>>>>>> branch
line 2"""

    conflicts = parse_conflict_markers(content)
    assert len(conflicts) == 1
    assert conflicts[0].our_version == "our change"
    assert conflicts[0].their_version == "their change"


def test_parse_multiple_conflicts() -> None:
    """Test parsing multiple conflicts in one file."""
    content = """<<<<<<< HEAD
change 1 ours
=======
change 1 theirs
>>>>>>> branch
middle
<<<<<<< HEAD
change 2 ours
=======
change 2 theirs
>>>>>>> branch"""

    conflicts = parse_conflict_markers(content)
    assert len(conflicts) == 2
    assert conflicts[0].our_version == "change 1 ours"
    assert conflicts[0].their_version == "change 1 theirs"
    assert conflicts[1].our_version == "change 2 ours"
    assert conflicts[1].their_version == "change 2 theirs"


def test_parse_no_conflicts() -> None:
    """Test parsing file with no conflicts."""
    content = """line 1
line 2
line 3"""

    conflicts = parse_conflict_markers(content)
    assert len(conflicts) == 0


def test_create_rebase_plan() -> None:
    """Test creating a rebase plan."""
    cwd = Path("/repo")
    rebase_ops = FakeRebaseOps(
        merge_bases={("feature", "main"): "abc123"},
        commit_ranges={
            ("main", "feature"): [
                {"sha": "def456", "message": "Commit 1", "author": "Test"},
                {"sha": "ghi789", "message": "Commit 2", "author": "Test"},
            ]
        },
    )

    plan = create_rebase_plan(rebase_ops, cwd, "feature", "main")

    assert plan is not None
    assert plan.source_branch == "feature"
    assert plan.target_branch == "main"
    assert plan.merge_base == "abc123"
    assert len(plan.commits_to_rebase) == 2
    assert plan.estimated_conflicts == -1


def test_create_rebase_plan_no_common_ancestor() -> None:
    """Test creating rebase plan with no common ancestor."""
    cwd = Path("/repo")
    rebase_ops = FakeRebaseOps(
        merge_bases={("feature", "main"): None},
    )

    plan = create_rebase_plan(rebase_ops, cwd, "feature", "main")

    assert plan is None


def test_count_commits_between() -> None:
    """Test counting commits in range."""
    cwd = Path("/repo")
    rebase_ops = FakeRebaseOps(
        commit_ranges={
            ("base", "head"): [
                {"sha": "a", "message": "1", "author": "T"},
                {"sha": "b", "message": "2", "author": "T"},
                {"sha": "c", "message": "3", "author": "T"},
            ]
        },
    )

    count = count_commits_between(rebase_ops, cwd, "base", "head")
    assert count == 3


def test_count_commits_between_empty() -> None:
    """Test counting commits when range is empty."""
    cwd = Path("/repo")
    rebase_ops = FakeRebaseOps(
        commit_ranges={("base", "head"): []},
    )

    count = count_commits_between(rebase_ops, cwd, "base", "head")
    assert count == 0


def test_is_rebase_needed() -> None:
    """Test checking if rebase is needed."""
    cwd = Path("/repo")
    rebase_ops = FakeRebaseOps(
        commit_ranges={
            ("feature", "main"): [
                {"sha": "a", "message": "1", "author": "T"},
            ]
        },
    )

    assert is_rebase_needed(rebase_ops, cwd, "feature", "main")


def test_is_rebase_not_needed() -> None:
    """Test checking if rebase is not needed."""
    cwd = Path("/repo")
    rebase_ops = FakeRebaseOps(
        commit_ranges={("feature", "main"): []},
    )

    assert not is_rebase_needed(rebase_ops, cwd, "feature", "main")
