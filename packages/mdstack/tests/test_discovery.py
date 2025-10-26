import tempfile
from pathlib import Path

from mdstack.discovery import discover_scopes, find_scope_by_path


def test_discover_scopes_finds_all_claude_md_files():
    """Should find all CLAUDE.md files in directory tree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create structure
        (root / "CLAUDE.md").touch()
        (root / "src").mkdir()
        (root / "src" / "CLAUDE.md").touch()
        (root / "tests").mkdir()
        (root / "tests" / "CLAUDE.md").touch()

        scopes = discover_scopes(root)

        assert len(scopes) == 3
        assert any(s.path == root for s in scopes)
        assert any(s.path == root / "src" for s in scopes)
        assert any(s.path == root / "tests" for s in scopes)


def test_parent_scope_relationship():
    """Should correctly identify parent scopes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        (root / "CLAUDE.md").touch()
        (root / "src").mkdir()
        (root / "src" / "commands").mkdir()
        (root / "src" / "commands" / "CLAUDE.md").touch()

        scopes = discover_scopes(root)

        root_scope = next(s for s in scopes if s.path == root)
        child_scope = next(s for s in scopes if s.path == root / "src" / "commands")

        assert child_scope.parent_scope == root_scope
        assert root_scope.parent_scope is None


def test_find_scope_by_path():
    """Should find the most specific scope for a path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        (root / "CLAUDE.md").touch()
        (root / "src").mkdir()
        (root / "src" / "CLAUDE.md").touch()

        scopes = discover_scopes(root)

        # File in src/ should match src scope, not root
        test_file = root / "src" / "test.py"
        scope = find_scope_by_path(test_file, scopes)

        assert scope is not None
        assert scope.path == root / "src"
