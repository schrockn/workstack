import tempfile
from pathlib import Path

import pytest

from mdstack.hashing import compute_hash
from mdstack.manifest import save_manifest
from mdstack.models import Manifest, Scope
from mdstack.validation import (
    TamperDetectionError,
    check_all_scopes,
    validate_no_tampering,
)


def test_validate_no_tampering_passes_when_hashes_match():
    """Should pass when file hashes match manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "CLAUDE.md").touch()

        scope = Scope.create(
            path=root,
            claude_md_path=root / "CLAUDE.md",
            mdstack_dir=root / ".mdstack",
        )

        # Create files
        scope.mdstack_dir.mkdir(exist_ok=True)
        tests_content = "# Tests\nSome content"
        lookup_content = "# Lookup\nSome content"

        (scope.mdstack_dir / "TESTS.md").write_text(tests_content)
        (scope.mdstack_dir / "LOOKUP.md").write_text(lookup_content)

        # Save manifest with matching hashes
        manifest = Manifest.create(
            content_hash="abc",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            generator_version="0.1.0",
            tests_hash=compute_hash(tests_content),
            lookup_hash=compute_hash(lookup_content),
            architecture_hash="arch123",
        )
        save_manifest(scope, manifest)

        # Should not raise
        validate_no_tampering(scope)


def test_validate_no_tampering_raises_when_tests_modified():
    """Should raise when TESTS.md has been manually edited."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "CLAUDE.md").touch()

        scope = Scope.create(
            path=root,
            claude_md_path=root / "CLAUDE.md",
            mdstack_dir=root / ".mdstack",
        )

        # Create files
        scope.mdstack_dir.mkdir(exist_ok=True)
        original_tests = "# Tests\nOriginal content"
        lookup_content = "# Lookup\nSome content"

        (scope.mdstack_dir / "TESTS.md").write_text(original_tests)
        (scope.mdstack_dir / "LOOKUP.md").write_text(lookup_content)

        # Save manifest with original hashes
        manifest = Manifest.create(
            content_hash="abc",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            generator_version="0.1.0",
            tests_hash=compute_hash(original_tests),
            lookup_hash=compute_hash(lookup_content),
            architecture_hash="arch123",
        )
        save_manifest(scope, manifest)

        # Manually edit TESTS.md
        (scope.mdstack_dir / "TESTS.md").write_text("# Tests\nModified content")

        # Should raise
        with pytest.raises(TamperDetectionError, match="TESTS.md has been manually edited"):
            validate_no_tampering(scope)


def test_check_all_scopes():
    """Should check all scopes and return tampered ones."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create two scopes
        (root / "scope1").mkdir()
        (root / "scope1" / "CLAUDE.md").touch()
        (root / "scope2").mkdir()
        (root / "scope2" / "CLAUDE.md").touch()

        scope1 = Scope.create(
            path=root / "scope1",
            claude_md_path=root / "scope1" / "CLAUDE.md",
            mdstack_dir=root / "scope1" / ".mdstack",
        )

        scope2 = Scope.create(
            path=root / "scope2",
            claude_md_path=root / "scope2" / "CLAUDE.md",
            mdstack_dir=root / "scope2" / ".mdstack",
        )

        # Setup scope1 (valid)
        scope1.mdstack_dir.mkdir(exist_ok=True)
        tests1 = "# Tests 1"
        (scope1.mdstack_dir / "TESTS.md").write_text(tests1)
        (scope1.mdstack_dir / "LOOKUP.md").write_text("# Lookup 1")
        manifest1 = Manifest.create(
            content_hash="abc",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            generator_version="0.1.0",
            tests_hash=compute_hash(tests1),
            lookup_hash=compute_hash("# Lookup 1"),
            architecture_hash="arch123",
        )
        save_manifest(scope1, manifest1)

        # Setup scope2 (tampered)
        scope2.mdstack_dir.mkdir(exist_ok=True)
        original_tests2 = "# Tests 2 original"
        (scope2.mdstack_dir / "TESTS.md").write_text(original_tests2)
        (scope2.mdstack_dir / "LOOKUP.md").write_text("# Lookup 2")
        manifest2 = Manifest.create(
            content_hash="def",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            generator_version="0.1.0",
            tests_hash=compute_hash(original_tests2),
            lookup_hash=compute_hash("# Lookup 2"),
            architecture_hash="arch123",
        )
        save_manifest(scope2, manifest2)

        # Tamper with scope2
        (scope2.mdstack_dir / "TESTS.md").write_text("# Tests 2 modified")

        # Check all scopes
        tampered = check_all_scopes([scope1, scope2])

        assert len(tampered) == 1
        assert tampered[0][0] == scope2
