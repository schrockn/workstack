"""Tests for repository operations."""

from pathlib import Path

import pytest

from dot_agent_kit.repos import (
    check_for_updates,
    find_all_repos,
    install_to_repo,
    update_repo,
)


def test_install_to_repo_success(tmp_path: Path) -> None:
    """Test successful installation of .agent/ folder."""
    # Create source .agent/ directory
    source_repo = tmp_path / "source"
    source_repo.mkdir()
    source_agent = source_repo / ".agent"
    source_agent.mkdir()

    (source_agent / "file1.txt").write_text("content1", encoding="utf-8")
    (source_agent / "file2.txt").write_text("content2", encoding="utf-8")

    subdir = source_agent / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("content3", encoding="utf-8")

    # Create target repository
    target_repo = tmp_path / "target"
    target_repo.mkdir()

    # Install
    install_to_repo(source_agent, target_repo)

    # Verify installation
    target_agent = target_repo / ".agent"
    assert target_agent.exists()
    assert (target_agent / "file1.txt").read_text(encoding="utf-8") == "content1"
    assert (target_agent / "file2.txt").read_text(encoding="utf-8") == "content2"
    assert (target_agent / "subdir" / "file3.txt").read_text(encoding="utf-8") == "content3"

    # Verify metadata in README.md
    readme = target_agent / "README.md"
    assert readme.exists()
    content = readme.read_text(encoding="utf-8")
    assert "managed: true" in content
    assert "installed_at:" in content
    assert "original_hash:" in content


def test_install_to_repo_source_not_exist(tmp_path: Path) -> None:
    """Test installation fails when source doesn't exist."""
    nonexistent = tmp_path / "nonexistent" / ".agent"
    target_repo = tmp_path / "target"
    target_repo.mkdir()

    with pytest.raises(ValueError, match="Source path does not exist"):
        install_to_repo(nonexistent, target_repo)


def test_install_to_repo_source_not_agent_dir(tmp_path: Path) -> None:
    """Test installation fails when source is not named .agent."""
    source_dir = tmp_path / "not-agent"
    source_dir.mkdir()

    target_repo = tmp_path / "target"
    target_repo.mkdir()

    with pytest.raises(ValueError, match="Source must be a .agent directory"):
        install_to_repo(source_dir, target_repo)


def test_install_to_repo_target_already_has_agent(tmp_path: Path) -> None:
    """Test installation fails when target already has .agent/."""
    source_agent = tmp_path / "source" / ".agent"
    source_agent.mkdir(parents=True)

    target_repo = tmp_path / "target"
    target_repo.mkdir()
    (target_repo / ".agent").mkdir()

    with pytest.raises(ValueError, match="Target already has .agent/ directory"):
        install_to_repo(source_agent, target_repo)


def test_update_repo_success(tmp_path: Path) -> None:
    """Test successful update of .agent/ folder."""
    # Create and install initial version
    source_repo = tmp_path / "source"
    source_repo.mkdir()
    source_agent = source_repo / ".agent"
    source_agent.mkdir()

    (source_agent / "file1.txt").write_text("version1", encoding="utf-8")

    target_repo = tmp_path / "target"
    target_repo.mkdir()

    install_to_repo(source_agent, target_repo)

    # Modify source
    (source_agent / "file1.txt").write_text("version2", encoding="utf-8")
    (source_agent / "file2.txt").write_text("new file", encoding="utf-8")

    # Update
    result = update_repo(target_repo)

    assert result is True

    target_agent = target_repo / ".agent"
    assert (target_agent / "file1.txt").read_text(encoding="utf-8") == "version2"
    assert (target_agent / "file2.txt").read_text(encoding="utf-8") == "new file"


def test_update_repo_no_changes_needed(tmp_path: Path) -> None:
    """Test update returns False when no changes needed."""
    # Create and install
    source_repo = tmp_path / "source"
    source_repo.mkdir()
    source_agent = source_repo / ".agent"
    source_agent.mkdir()

    (source_agent / "file1.txt").write_text("content", encoding="utf-8")

    target_repo = tmp_path / "target"
    target_repo.mkdir()

    install_to_repo(source_agent, target_repo)

    # Try to update without changes
    result = update_repo(target_repo)

    assert result is False


def test_update_repo_preserves_readme(tmp_path: Path) -> None:
    """Test update preserves README.md with metadata."""
    # Create and install
    source_repo = tmp_path / "source"
    source_repo.mkdir()
    source_agent = source_repo / ".agent"
    source_agent.mkdir()

    (source_agent / "file1.txt").write_text("version1", encoding="utf-8")

    target_repo = tmp_path / "target"
    target_repo.mkdir()

    install_to_repo(source_agent, target_repo)

    # Get original README content
    target_agent = target_repo / ".agent"
    (target_agent / "README.md").read_text(encoding="utf-8")

    # Modify source
    (source_agent / "file1.txt").write_text("version2", encoding="utf-8")

    # Update
    update_repo(target_repo)

    # README should still exist and have metadata
    updated_readme = (target_agent / "README.md").read_text(encoding="utf-8")
    assert "managed: true" in updated_readme
    assert "dot_agent:" in updated_readme


def test_update_repo_not_managed(tmp_path: Path) -> None:
    """Test update fails for unmanaged .agent/ folder."""
    # Create unmanaged .agent/ folder
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    target_agent = target_repo / ".agent"
    target_agent.mkdir()

    readme_content = "# Just a regular README"
    (target_agent / "README.md").write_text(readme_content, encoding="utf-8")

    with pytest.raises(ValueError, match="not managed"):
        update_repo(target_repo)


def test_update_repo_no_agent_dir(tmp_path: Path) -> None:
    """Test update fails when no .agent/ directory."""
    target_repo = tmp_path / "target"
    target_repo.mkdir()

    with pytest.raises(ValueError, match="has no .agent/ folder"):
        update_repo(target_repo)


def test_check_for_updates_available(tmp_path: Path) -> None:
    """Test check_for_updates detects available updates."""
    # Create and install
    source_repo = tmp_path / "source"
    source_repo.mkdir()
    source_agent = source_repo / ".agent"
    source_agent.mkdir()

    (source_agent / "file1.txt").write_text("version1", encoding="utf-8")

    target_repo = tmp_path / "target"
    target_repo.mkdir()

    install_to_repo(source_agent, target_repo)

    # No updates initially
    assert check_for_updates(target_repo) is False

    # Modify source
    (source_agent / "file1.txt").write_text("version2", encoding="utf-8")

    # Updates should be detected
    assert check_for_updates(target_repo) is True


def test_check_for_updates_unmanaged(tmp_path: Path) -> None:
    """Test check_for_updates returns False for unmanaged repos."""
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    target_agent = target_repo / ".agent"
    target_agent.mkdir()

    (target_agent / "README.md").write_text("# Regular README", encoding="utf-8")

    assert check_for_updates(target_repo) is False


def test_check_for_updates_source_missing(tmp_path: Path) -> None:
    """Test check_for_updates returns False when source is missing."""
    # Create and install
    source_repo = tmp_path / "source"
    source_repo.mkdir()
    source_agent = source_repo / ".agent"
    source_agent.mkdir()

    (source_agent / "file1.txt").write_text("content", encoding="utf-8")

    target_repo = tmp_path / "target"
    target_repo.mkdir()

    install_to_repo(source_agent, target_repo)

    # Remove source
    import shutil

    shutil.rmtree(source_repo)

    # Should return False when source is gone
    assert check_for_updates(target_repo) is False


def test_find_all_repos_current_dir(tmp_path: Path) -> None:
    """Test finding repos starting from current directory."""
    # Create repos with .agent/ folders
    repo1 = tmp_path / "repo1"
    repo1.mkdir()
    (repo1 / ".agent").mkdir()

    repo2 = tmp_path / "repo2"
    repo2.mkdir()
    (repo2 / ".agent").mkdir()

    # Create repo without .agent/
    repo3 = tmp_path / "repo3"
    repo3.mkdir()

    # Find from tmp_path
    repos = find_all_repos(tmp_path)

    assert len(repos) >= 2
    assert repo1 in repos
    assert repo2 in repos
    assert repo3 not in repos


def test_find_all_repos_nested(tmp_path: Path) -> None:
    """Test finding nested repos."""
    # Create nested structure
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    (workspace / ".agent").mkdir()  # Workspace itself has .agent

    project = workspace / "project"
    project.mkdir()
    (project / ".agent").mkdir()

    # Find from workspace
    repos = find_all_repos(workspace)

    assert workspace in repos
    assert project in repos


def test_find_all_repos_empty(tmp_path: Path) -> None:
    """Test finding repos when none exist."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    repos = find_all_repos(empty_dir)

    assert repos == []
