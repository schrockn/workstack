import tempfile
from pathlib import Path

import pytest

from mdstack.models import Manifest, Scope


def test_scope_create_validates_paths():
    """Scope.create should validate that paths exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        claude_md = root / "CLAUDE.md"
        claude_md.touch()

        scope = Scope.create(path=root, claude_md_path=claude_md, mdstack_dir=root / ".mdstack")

        assert scope.path == root
        assert scope.claude_md_path == claude_md


def test_scope_create_raises_on_missing_claude_md():
    """Should raise error if CLAUDE.md doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        with pytest.raises(ValueError, match="CLAUDE.md does not exist"):
            Scope.create(
                path=root,
                claude_md_path=root / "CLAUDE.md",
                mdstack_dir=root / ".mdstack",
            )


def test_manifest_create():
    """Should create manifest with all fields."""
    manifest = Manifest.create(
        content_hash="abc123",
        llm_provider="anthropic",
        llm_model="claude-3-5-sonnet-20241022",
        generator_version="0.1.0",
        tests_hash="def456",
        lookup_hash="ghi789",
        architecture_hash="jkl012",
    )

    assert manifest.content_hash == "abc123"
    assert manifest.llm_provider == "anthropic"
    assert manifest.generated_at is not None
