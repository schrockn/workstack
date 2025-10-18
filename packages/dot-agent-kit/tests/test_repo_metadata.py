"""Tests for repository metadata management."""

from pathlib import Path

from dot_agent_kit.repo_metadata import (
    calculate_folder_hash,
    get_repo_metadata,
    parse_agent_frontmatter,
    update_agent_frontmatter,
    write_repo_metadata,
)


def test_calculate_folder_hash_empty_directory(tmp_path: Path) -> None:
    """Test hash calculation for empty directory."""
    test_dir = tmp_path / "empty"
    test_dir.mkdir()

    hash_result = calculate_folder_hash(test_dir)
    assert hash_result.startswith("sha256:")


def test_calculate_folder_hash_with_files(tmp_path: Path) -> None:
    """Test hash calculation with files."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    (test_dir / "file1.txt").write_text("content1", encoding="utf-8")
    (test_dir / "file2.txt").write_text("content2", encoding="utf-8")

    hash_result = calculate_folder_hash(test_dir)
    assert hash_result.startswith("sha256:")
    assert len(hash_result) > 10


def test_calculate_folder_hash_excludes_readme(tmp_path: Path) -> None:
    """Test that README.md is excluded from hash calculation."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    (test_dir / "file1.txt").write_text("content1", encoding="utf-8")

    hash1 = calculate_folder_hash(test_dir)

    # Add README.md
    (test_dir / "README.md").write_text("readme content", encoding="utf-8")

    hash2 = calculate_folder_hash(test_dir)

    # Hashes should be the same since README.md is excluded
    assert hash1 == hash2


def test_calculate_folder_hash_nonexistent(tmp_path: Path) -> None:
    """Test hash calculation for nonexistent directory."""
    nonexistent = tmp_path / "nonexistent"
    hash_result = calculate_folder_hash(nonexistent)
    assert hash_result == ""


def test_parse_agent_frontmatter_valid() -> None:
    """Test parsing valid dot_agent frontmatter."""
    content = """---
dot_agent:
  managed: true
  installed_at: "2024-01-15T10:30:00Z"
  original_hash: "sha256:abc123"
---

# Content
"""
    frontmatter = parse_agent_frontmatter(content)

    assert frontmatter["managed"] is True
    assert frontmatter["installed_at"] == "2024-01-15T10:30:00Z"
    assert frontmatter["original_hash"] == "sha256:abc123"


def test_parse_agent_frontmatter_no_frontmatter() -> None:
    """Test parsing content without frontmatter."""
    content = "# Just content\n\nNo frontmatter here."
    frontmatter = parse_agent_frontmatter(content)

    assert frontmatter == {}


def test_parse_agent_frontmatter_no_dot_agent_section() -> None:
    """Test parsing frontmatter without dot_agent section."""
    content = """---
other_field: value
---

# Content
"""
    frontmatter = parse_agent_frontmatter(content)

    assert frontmatter == {}


def test_update_agent_frontmatter_new() -> None:
    """Test adding frontmatter to content without it."""
    content = "# My Content\n\nSome text."
    metadata = {"managed": True, "installed_at": "2024-01-15T10:30:00Z"}

    updated = update_agent_frontmatter(content, metadata)

    assert updated.startswith("---\n")
    assert "dot_agent:" in updated
    assert "managed: true" in updated
    assert "# My Content" in updated


def test_update_agent_frontmatter_existing() -> None:
    """Test updating existing frontmatter."""
    content = """---
dot_agent:
  managed: false
other_field: preserve_me
---

# Content
"""
    metadata = {"managed": True, "installed_at": "2024-01-15T10:30:00Z"}

    updated = update_agent_frontmatter(content, metadata)

    assert "dot_agent:" in updated
    assert "managed: true" in updated
    assert "installed_at:" in updated
    assert "other_field: preserve_me" in updated


def test_get_repo_metadata_no_agent_dir(tmp_path: Path) -> None:
    """Test getting metadata when no .agent/ directory exists."""
    result = get_repo_metadata(tmp_path)
    assert result is None


def test_get_repo_metadata_no_readme(tmp_path: Path) -> None:
    """Test getting metadata when .agent/ exists but no README.md."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    result = get_repo_metadata(tmp_path)
    assert result is None


def test_get_repo_metadata_with_metadata(tmp_path: Path) -> None:
    """Test getting metadata from existing .agent/README.md."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    readme_content = """---
dot_agent:
  managed: true
  installed_at: "2024-01-15T10:30:00+00:00"
  original_hash: "sha256:abc123"
  current_hash: "sha256:def456"
  source_url: "/path/to/source"
---

# .agent/ Directory
"""
    (agent_dir / "README.md").write_text(readme_content, encoding="utf-8")

    metadata = get_repo_metadata(tmp_path)

    assert metadata is not None
    assert metadata.managed is True
    assert metadata.installed_at is not None
    assert metadata.original_hash == "sha256:abc123"
    assert metadata.source_url == "/path/to/source"


def test_get_repo_metadata_unmanaged(tmp_path: Path) -> None:
    """Test getting metadata for unmanaged .agent/ folder."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    readme_content = """# .agent/ Directory

Just a regular README without frontmatter.
"""
    (agent_dir / "README.md").write_text(readme_content, encoding="utf-8")

    metadata = get_repo_metadata(tmp_path)

    assert metadata is not None
    assert metadata.managed is False
    assert metadata.installed_at is None


def test_write_repo_metadata_creates_readme(tmp_path: Path) -> None:
    """Test writing metadata creates README.md if missing."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    metadata = {
        "managed": True,
        "installed_at": "2024-01-15T10:30:00Z",
    }

    write_repo_metadata(tmp_path, metadata)

    readme_path = agent_dir / "README.md"
    assert readme_path.exists()

    content = readme_path.read_text(encoding="utf-8")
    assert "dot_agent:" in content
    assert "managed: true" in content


def test_write_repo_metadata_updates_existing(tmp_path: Path) -> None:
    """Test writing metadata updates existing README.md."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    # Create initial README
    initial_content = """---
dot_agent:
  managed: false
---

# My Custom Content

This should be preserved.
"""
    readme_path = agent_dir / "README.md"
    readme_path.write_text(initial_content, encoding="utf-8")

    # Update metadata
    metadata = {
        "managed": True,
        "installed_at": "2024-01-15T10:30:00Z",
    }

    write_repo_metadata(tmp_path, metadata)

    # Check updated content
    content = readme_path.read_text(encoding="utf-8")
    assert "managed: true" in content
    assert "installed_at:" in content
    assert "My Custom Content" in content
    assert "This should be preserved" in content


def test_write_repo_metadata_no_agent_dir(tmp_path: Path) -> None:
    """Test writing metadata when .agent/ doesn't exist does nothing."""
    metadata = {"managed": True}

    # Should not raise, just do nothing
    write_repo_metadata(tmp_path, metadata)

    assert not (tmp_path / ".agent" / "README.md").exists()
