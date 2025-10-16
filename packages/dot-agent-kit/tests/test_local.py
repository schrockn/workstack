from pathlib import Path

import pytest

from dot_agent_kit.local import LocalFile, LocalFileDiscovery


def test_local_file_dataclass() -> None:
    """Test LocalFile dataclass properties."""
    local_file = LocalFile(
        relative_path="docs/test.md",
        full_path=Path("/agent/.agent/docs/test.md"),
        size=1024,
        modified_time=1234567890.0,
        file_type="md",
    )

    assert local_file.relative_path == "docs/test.md"
    assert local_file.size == 1024
    assert local_file.file_type == "md"
    assert local_file.is_directory is False


def test_local_file_directory() -> None:
    """Test LocalFile representing a directory."""
    local_file = LocalFile(
        relative_path="docs",
        full_path=Path("/agent/.agent/docs"),
        size=0,
        modified_time=1234567890.0,
        file_type="directory",
    )

    assert local_file.is_directory is True


def test_discover_empty_directory(tmp_path: Path) -> None:
    """Test discovery in an empty .agent directory."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    discovery = LocalFileDiscovery(agent_dir)
    files = discovery.discover_local_files()

    assert files == []


def test_discover_nonexistent_directory(tmp_path: Path) -> None:
    """Test discovery when .agent directory doesn't exist."""
    agent_dir = tmp_path / ".agent"

    discovery = LocalFileDiscovery(agent_dir)
    files = discovery.discover_local_files()

    assert files == []


def test_discover_root_files(tmp_path: Path) -> None:
    """Test discovery of files in .agent root."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    (agent_dir / "README.md").write_text("# README", encoding="utf-8")
    (agent_dir / "ARCHITECTURE.md").write_text("# Architecture", encoding="utf-8")

    discovery = LocalFileDiscovery(agent_dir)
    files = discovery.discover_local_files()

    assert len(files) == 2
    assert files[0].relative_path == "ARCHITECTURE.md"
    assert files[1].relative_path == "README.md"
    assert files[0].file_type == "md"
    assert files[0].size > 0


def test_discover_subdirectory_files(tmp_path: Path) -> None:
    """Test discovery of files in subdirectories."""
    agent_dir = tmp_path / ".agent"
    docs_dir = agent_dir / "docs"
    docs_dir.mkdir(parents=True)

    (docs_dir / "guide.md").write_text("# Guide", encoding="utf-8")
    (docs_dir / "tutorial.md").write_text("# Tutorial", encoding="utf-8")

    discovery = LocalFileDiscovery(agent_dir)
    files = discovery.discover_local_files()

    assert len(files) == 2
    assert files[0].relative_path == "docs/guide.md"
    assert files[1].relative_path == "docs/tutorial.md"


def test_discover_excludes_packages(tmp_path: Path) -> None:
    """Test that packages/ directory is excluded from discovery."""
    agent_dir = tmp_path / ".agent"
    packages_dir = agent_dir / "packages"
    packages_dir.mkdir(parents=True)

    (agent_dir / "README.md").write_text("# README", encoding="utf-8")
    (packages_dir / "installed.md").write_text("# Installed", encoding="utf-8")

    discovery = LocalFileDiscovery(agent_dir)
    files = discovery.discover_local_files()

    assert len(files) == 1
    assert files[0].relative_path == "README.md"


def test_discover_excludes_hidden_files(tmp_path: Path) -> None:
    """Test that hidden files (starting with .) are excluded."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    (agent_dir / "README.md").write_text("# README", encoding="utf-8")
    (agent_dir / ".hidden.md").write_text("# Hidden", encoding="utf-8")

    hidden_dir = agent_dir / ".hidden_dir"
    hidden_dir.mkdir()
    (hidden_dir / "file.md").write_text("# File", encoding="utf-8")

    discovery = LocalFileDiscovery(agent_dir)
    files = discovery.discover_local_files()

    assert len(files) == 1
    assert files[0].relative_path == "README.md"


def test_discover_with_pattern(tmp_path: Path) -> None:
    """Test discovery with glob pattern filtering."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    (agent_dir / "README.md").write_text("# README", encoding="utf-8")
    (agent_dir / "config.yml").write_text("config: value", encoding="utf-8")

    docs_dir = agent_dir / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text("# Guide", encoding="utf-8")

    discovery = LocalFileDiscovery(agent_dir)

    # Filter for markdown files (matches all .md files recursively)
    md_files = discovery.discover_local_files(pattern="*.md")
    assert len(md_files) == 2
    assert md_files[0].relative_path == "README.md"
    assert md_files[1].relative_path == "docs/guide.md"

    # Filter for docs directory
    docs_files = discovery.discover_local_files(pattern="docs/*")
    assert len(docs_files) == 1
    assert docs_files[0].relative_path == "docs/guide.md"

    # Filter for config files
    config_files = discovery.discover_local_files(pattern="*.yml")
    assert len(config_files) == 1
    assert config_files[0].relative_path == "config.yml"


def test_discover_with_directories(tmp_path: Path) -> None:
    """Test discovery including directories."""
    agent_dir = tmp_path / ".agent"
    docs_dir = agent_dir / "docs"
    docs_dir.mkdir(parents=True)

    (docs_dir / "guide.md").write_text("# Guide", encoding="utf-8")

    discovery = LocalFileDiscovery(agent_dir)
    files = discovery.discover_local_files(include_directories=True)

    assert len(files) == 2
    assert files[0].relative_path == "docs"
    assert files[0].is_directory is True
    assert files[1].relative_path == "docs/guide.md"
    assert files[1].is_directory is False


def test_get_file(tmp_path: Path) -> None:
    """Test getting a specific file by relative path."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    (agent_dir / "README.md").write_text("# README", encoding="utf-8")

    discovery = LocalFileDiscovery(agent_dir)
    file = discovery.get_file("README.md")

    if file is None:
        msg = "Expected file to be found"
        raise AssertionError(msg)

    assert file.relative_path == "README.md"
    assert file.file_type == "md"


def test_get_file_nonexistent(tmp_path: Path) -> None:
    """Test getting a file that doesn't exist."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    discovery = LocalFileDiscovery(agent_dir)
    file = discovery.get_file("nonexistent.md")

    assert file is None


def test_get_file_in_packages(tmp_path: Path) -> None:
    """Test that get_file returns None for files in packages/."""
    agent_dir = tmp_path / ".agent"
    packages_dir = agent_dir / "packages"
    packages_dir.mkdir(parents=True)

    (packages_dir / "installed.md").write_text("# Installed", encoding="utf-8")

    discovery = LocalFileDiscovery(agent_dir)
    file = discovery.get_file("packages/installed.md")

    assert file is None


def test_read_file(tmp_path: Path) -> None:
    """Test reading file contents."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    content = "# README\n\nThis is a test."
    (agent_dir / "README.md").write_text(content, encoding="utf-8")

    discovery = LocalFileDiscovery(agent_dir)
    read_content = discovery.read_file("README.md")

    assert read_content == content


def test_read_file_nonexistent(tmp_path: Path) -> None:
    """Test reading a file that doesn't exist."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    discovery = LocalFileDiscovery(agent_dir)

    with pytest.raises(FileNotFoundError, match="File not found: nonexistent.md"):
        discovery.read_file("nonexistent.md")


def test_read_file_in_packages(tmp_path: Path) -> None:
    """Test that reading files in packages/ raises ValueError."""
    agent_dir = tmp_path / ".agent"
    packages_dir = agent_dir / "packages"
    packages_dir.mkdir(parents=True)

    (packages_dir / "installed.md").write_text("# Installed", encoding="utf-8")

    discovery = LocalFileDiscovery(agent_dir)

    with pytest.raises(ValueError, match="Cannot read installed package file"):
        discovery.read_file("packages/installed.md")


def test_read_directory(tmp_path: Path) -> None:
    """Test that reading a directory raises IsADirectoryError."""
    agent_dir = tmp_path / ".agent"
    docs_dir = agent_dir / "docs"
    docs_dir.mkdir(parents=True)

    discovery = LocalFileDiscovery(agent_dir)

    with pytest.raises(IsADirectoryError, match="Path is a directory: docs"):
        discovery.read_file("docs")


def test_categorize_files(tmp_path: Path) -> None:
    """Test categorizing files by directory."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    (agent_dir / "README.md").write_text("# README", encoding="utf-8")
    (agent_dir / "ARCHITECTURE.md").write_text("# Architecture", encoding="utf-8")

    docs_dir = agent_dir / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text("# Guide", encoding="utf-8")

    tools_dir = agent_dir / "tools"
    tools_dir.mkdir()
    (tools_dir / "tool1.md").write_text("# Tool 1", encoding="utf-8")
    (tools_dir / "tool2.md").write_text("# Tool 2", encoding="utf-8")

    discovery = LocalFileDiscovery(agent_dir)
    files = discovery.discover_local_files()
    categories = discovery.categorize_files(files)

    assert len(categories) == 3
    assert "root" in categories
    assert "docs" in categories
    assert "tools" in categories

    assert len(categories["root"]) == 2
    assert len(categories["docs"]) == 1
    assert len(categories["tools"]) == 2

    assert categories["root"][0].relative_path == "ARCHITECTURE.md"
    assert categories["docs"][0].relative_path == "docs/guide.md"


def test_categorize_empty_list(tmp_path: Path) -> None:
    """Test categorizing an empty list of files."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    discovery = LocalFileDiscovery(agent_dir)
    categories = discovery.categorize_files([])

    assert categories == {}


def test_file_with_no_extension(tmp_path: Path) -> None:
    """Test handling files with no extension."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    (agent_dir / "Makefile").write_text("all:\n\techo 'test'", encoding="utf-8")

    discovery = LocalFileDiscovery(agent_dir)
    files = discovery.discover_local_files()

    assert len(files) == 1
    assert files[0].relative_path == "Makefile"
    assert files[0].file_type == "no-extension"


def test_deeply_nested_files(tmp_path: Path) -> None:
    """Test discovery of deeply nested files."""
    agent_dir = tmp_path / ".agent"
    deep_dir = agent_dir / "a" / "b" / "c" / "d"
    deep_dir.mkdir(parents=True)

    (deep_dir / "deep.md").write_text("# Deep", encoding="utf-8")

    discovery = LocalFileDiscovery(agent_dir)
    files = discovery.discover_local_files()

    assert len(files) == 1
    assert files[0].relative_path == "a/b/c/d/deep.md"


def test_mixed_content(tmp_path: Path) -> None:
    """Test discovery with a mix of files, directories, and excluded content."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    # Root files
    (agent_dir / "README.md").write_text("# README", encoding="utf-8")
    (agent_dir / ".gitignore").write_text("*.pyc", encoding="utf-8")

    # Docs directory
    docs_dir = agent_dir / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text("# Guide", encoding="utf-8")

    # Packages directory (should be excluded)
    packages_dir = agent_dir / "packages"
    packages_dir.mkdir()
    (packages_dir / "installed.md").write_text("# Installed", encoding="utf-8")

    # Hidden directory (should be excluded)
    hidden_dir = agent_dir / ".cache"
    hidden_dir.mkdir()
    (hidden_dir / "cache.txt").write_text("cache", encoding="utf-8")

    discovery = LocalFileDiscovery(agent_dir)
    files = discovery.discover_local_files()

    # Should only find README.md and docs/guide.md
    assert len(files) == 2
    assert files[0].relative_path == "README.md"
    assert files[1].relative_path == "docs/guide.md"
