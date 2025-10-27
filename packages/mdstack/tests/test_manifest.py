import tempfile
from pathlib import Path

from mdstack.manifest import is_stale, load_manifest, save_manifest
from mdstack.models import Manifest, Scope


def test_save_and_load_manifest():
    """Should save and load manifest correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "CLAUDE.md").touch()

        scope = Scope.create(
            path=root,
            claude_md_path=root / "CLAUDE.md",
            mdstack_dir=root / ".mdstack",
        )

        manifest = Manifest.create(
            content_hash="abc123",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            generator_version="0.1.0",
            tests_hash="def456",
            lookup_hash="ghi789",
            architecture_hash="jkl012",
        )

        save_manifest(scope, manifest)
        loaded = load_manifest(scope)

        assert loaded is not None
        assert loaded.content_hash == "abc123"
        assert loaded.llm_provider == "anthropic"


def test_is_stale_when_no_manifest():
    """Should be stale when no manifest exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "CLAUDE.md").touch()

        scope = Scope.create(
            path=root,
            claude_md_path=root / "CLAUDE.md",
            mdstack_dir=root / ".mdstack",
        )

        assert is_stale(scope) is True


def test_is_stale_when_files_missing():
    """Should be stale when generated files missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "CLAUDE.md").touch()

        scope = Scope.create(
            path=root,
            claude_md_path=root / "CLAUDE.md",
            mdstack_dir=root / ".mdstack",
        )

        manifest = Manifest.create(
            content_hash="abc123",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            generator_version="0.1.0",
            tests_hash="def456",
            lookup_hash="ghi789",
            architecture_hash="jkl012",
        )

        save_manifest(scope, manifest)

        # Manifest exists but TESTS.md doesn't
        assert is_stale(scope) is True
