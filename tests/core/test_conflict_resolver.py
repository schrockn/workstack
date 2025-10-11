"""Tests for conflict resolution."""

from pathlib import Path

from tests.fakes.gitops import FakeGitOps
from workstack.core.conflict_resolver import ConflictResolver, Resolution


def test_resolve_keep_ours() -> None:
    """Test resolving conflicts by keeping 'ours' version."""
    git_ops = FakeGitOps()
    resolver = ConflictResolver(git_ops)

    content = """line 1
<<<<<<< HEAD
our change
=======
their change
>>>>>>> branch
line 2"""

    resolved = resolver._resolve_keep_ours(content)

    assert (
        resolved
        == """line 1
our change
line 2"""
    )


def test_resolve_keep_theirs() -> None:
    """Test resolving conflicts by keeping 'theirs' version."""
    git_ops = FakeGitOps()
    resolver = ConflictResolver(git_ops)

    content = """line 1
<<<<<<< HEAD
our change
=======
their change
>>>>>>> branch
line 2"""

    resolved = resolver._resolve_keep_theirs(content)

    assert (
        resolved
        == """line 1
their change
line 2"""
    )


def test_resolve_multiple_conflicts_ours() -> None:
    """Test resolving multiple conflicts keeping 'ours'."""
    git_ops = FakeGitOps()
    resolver = ConflictResolver(git_ops)

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

    resolved = resolver._resolve_keep_ours(content)

    assert (
        resolved
        == """change 1 ours
middle
change 2 ours"""
    )


def test_resolve_multiple_conflicts_theirs() -> None:
    """Test resolving multiple conflicts keeping 'theirs'."""
    git_ops = FakeGitOps()
    resolver = ConflictResolver(git_ops)

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

    resolved = resolver._resolve_keep_theirs(content)

    assert (
        resolved
        == """change 1 theirs
middle
change 2 theirs"""
    )


def test_check_resolution_complete_resolved() -> None:
    """Test checking if resolution is complete when all markers removed."""
    git_ops = FakeGitOps()
    resolver = ConflictResolver(git_ops)

    tmp_file = Path("/tmp/test_file.txt")
    tmp_file.write_text("line 1\nline 2\nline 3", encoding="utf-8")

    result = resolver._check_resolution_complete(tmp_file)

    assert result is True

    # Cleanup
    if tmp_file.exists():
        tmp_file.unlink()


def test_check_resolution_complete_unresolved() -> None:
    """Test checking if resolution is complete with remaining markers."""
    git_ops = FakeGitOps()
    resolver = ConflictResolver(git_ops)

    tmp_file = Path("/tmp/test_file_conflict.txt")
    tmp_file.write_text("line 1\n<<<<<<< HEAD\nours\n", encoding="utf-8")

    result = resolver._check_resolution_complete(tmp_file)

    assert result is False

    # Cleanup
    if tmp_file.exists():
        tmp_file.unlink()


def test_apply_resolution_with_content(tmp_path: Path) -> None:
    """Test applying resolution with resolved content."""
    git_ops = FakeGitOps()
    resolver = ConflictResolver(git_ops)

    stack_path = tmp_path / "stack"
    stack_path.mkdir()
    file_path = stack_path / "test.txt"
    file_path.write_text("original content", encoding="utf-8")

    resolution = Resolution(
        file_path="test.txt",
        strategy="ours",
        resolved_content="resolved content",
    )

    # Note: This will fail git add since it's not a real git repo
    # But we can test the file writing part
    try:
        resolver.apply_resolution(stack_path, resolution)
    except Exception:
        # Git add will fail, but we can still check the file was written
        pass

    assert file_path.read_text(encoding="utf-8") == "resolved content"


def test_resolution_dataclass_immutable() -> None:
    """Test that Resolution is immutable."""
    resolution = Resolution(
        file_path="test.txt",
        strategy="ours",
        resolved_content="content",
    )

    # Verify frozen dataclass prevents modification
    try:
        resolution.strategy = "theirs"  # type: ignore
        raise AssertionError("Should not be able to modify frozen dataclass")
    except AttributeError:
        pass  # Expected


def test_resolve_keep_ours_multiline_conflict() -> None:
    """Test resolving multiline conflict keeping 'ours'."""
    git_ops = FakeGitOps()
    resolver = ConflictResolver(git_ops)

    content = """function foo() {
<<<<<<< HEAD
  return 1;
  return 2;
=======
  return 3;
  return 4;
>>>>>>> branch
}"""

    resolved = resolver._resolve_keep_ours(content)

    expected = """function foo() {
  return 1;
  return 2;
}"""

    assert resolved == expected


def test_resolve_keep_theirs_multiline_conflict() -> None:
    """Test resolving multiline conflict keeping 'theirs'."""
    git_ops = FakeGitOps()
    resolver = ConflictResolver(git_ops)

    content = """function foo() {
<<<<<<< HEAD
  return 1;
  return 2;
=======
  return 3;
  return 4;
>>>>>>> branch
}"""

    resolved = resolver._resolve_keep_theirs(content)

    expected = """function foo() {
  return 3;
  return 4;
}"""

    assert resolved == expected


def test_resolve_empty_ours_section() -> None:
    """Test resolving when 'ours' section is empty."""
    git_ops = FakeGitOps()
    resolver = ConflictResolver(git_ops)

    content = """line 1
<<<<<<< HEAD
=======
their change
>>>>>>> branch
line 2"""

    resolved = resolver._resolve_keep_ours(content)

    # When ours section is empty, there's no content between HEAD and ===
    # So no blank line is added
    assert (
        resolved
        == """line 1
line 2"""
    )


def test_resolve_empty_theirs_section() -> None:
    """Test resolving when 'theirs' section is empty."""
    git_ops = FakeGitOps()
    resolver = ConflictResolver(git_ops)

    content = """line 1
<<<<<<< HEAD
our change
=======
>>>>>>> branch
line 2"""

    resolved = resolver._resolve_keep_theirs(content)

    # When theirs section is empty, there's no content between === and >>>
    # So no blank line is added
    assert (
        resolved
        == """line 1
line 2"""
    )


def test_resolve_adjacent_conflicts() -> None:
    """Test resolving adjacent conflicts with no content between them."""
    git_ops = FakeGitOps()
    resolver = ConflictResolver(git_ops)

    content = """<<<<<<< HEAD
conflict 1 ours
=======
conflict 1 theirs
>>>>>>> branch
<<<<<<< HEAD
conflict 2 ours
=======
conflict 2 theirs
>>>>>>> branch"""

    resolved = resolver._resolve_keep_ours(content)

    assert (
        resolved
        == """conflict 1 ours
conflict 2 ours"""
    )
