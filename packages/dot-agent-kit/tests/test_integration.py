"""Integration tests for complete .agent/ folder management workflow."""

from pathlib import Path

from dot_agent_kit.repo_metadata import get_repo_metadata
from dot_agent_kit.repos import (
    check_for_updates,
    find_all_repos,
    install_to_repo,
    update_repo,
)


def test_full_workflow_install_update(tmp_path: Path) -> None:
    """Test complete workflow: install, modify, update."""
    # Setup: Create source .agent/ directory with content
    source_repo = tmp_path / "source"
    source_repo.mkdir()
    source_agent = source_repo / ".agent"
    source_agent.mkdir()

    (source_agent / "tool1.md").write_text("# Tool 1\nVersion 1", encoding="utf-8")
    (source_agent / "tool2.md").write_text("# Tool 2\nVersion 1", encoding="utf-8")

    docs_dir = source_agent / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text("# Guide\nVersion 1", encoding="utf-8")

    # Step 1: Install to target repository
    target_repo = tmp_path / "target"
    target_repo.mkdir()

    install_to_repo(source_agent, target_repo)

    # Verify installation
    target_agent = target_repo / ".agent"
    assert target_agent.exists()
    assert (target_agent / "tool1.md").read_text(encoding="utf-8") == "# Tool 1\nVersion 1"
    assert (target_agent / "docs" / "guide.md").read_text(encoding="utf-8") == "# Guide\nVersion 1"

    metadata = get_repo_metadata(target_repo)
    assert metadata is not None
    assert metadata.managed is True
    assert metadata.installed_at is not None
    assert metadata.source_url is not None

    # Step 2: Check for updates (should be none)
    assert check_for_updates(target_repo) is False

    # Step 3: Modify source (simulate template update)
    (source_agent / "tool1.md").write_text("# Tool 1\nVersion 2 - Updated!", encoding="utf-8")
    (source_agent / "tool3.md").write_text("# Tool 3\nNew tool!", encoding="utf-8")

    # Step 4: Check for updates (should detect changes)
    assert check_for_updates(target_repo) is True

    # Step 5: Update target
    result = update_repo(target_repo)
    assert result is True

    # Verify update
    assert (target_agent / "tool1.md").read_text(
        encoding="utf-8"
    ) == "# Tool 1\nVersion 2 - Updated!"
    assert (target_agent / "tool3.md").read_text(encoding="utf-8") == "# Tool 3\nNew tool!"
    assert (target_agent / "tool2.md").read_text(encoding="utf-8") == "# Tool 2\nVersion 1"

    # README.md should still exist with updated metadata
    assert (target_agent / "README.md").exists()
    readme_content = (target_agent / "README.md").read_text(encoding="utf-8")
    assert "managed: true" in readme_content

    # Step 6: Check for updates again (should be none)
    assert check_for_updates(target_repo) is False


def test_find_repos_discovers_managed_and_unmanaged(tmp_path: Path) -> None:
    """Test finding both managed and unmanaged repositories."""
    # Create managed repo
    source_agent = tmp_path / "source" / ".agent"
    source_agent.mkdir(parents=True)
    (source_agent / "file.txt").write_text("content", encoding="utf-8")

    managed_repo = tmp_path / "managed"
    managed_repo.mkdir()
    install_to_repo(source_agent, managed_repo)

    # Create unmanaged repo
    unmanaged_repo = tmp_path / "unmanaged"
    unmanaged_repo.mkdir()
    unmanaged_agent = unmanaged_repo / ".agent"
    unmanaged_agent.mkdir()
    (unmanaged_agent / "README.md").write_text("# Unmanaged", encoding="utf-8")

    # Find all repos
    repos = find_all_repos(tmp_path)

    assert len(repos) >= 2
    assert managed_repo in repos
    assert unmanaged_repo in repos

    # Verify managed status
    managed_metadata = get_repo_metadata(managed_repo)
    assert managed_metadata is not None
    assert managed_metadata.managed is True

    unmanaged_metadata = get_repo_metadata(unmanaged_repo)
    assert unmanaged_metadata is not None
    assert unmanaged_metadata.managed is False


def test_update_preserves_readme_customizations(tmp_path: Path) -> None:
    """Test that updates preserve custom README.md content."""
    # Setup source
    source_agent = tmp_path / "source" / ".agent"
    source_agent.mkdir(parents=True)
    (source_agent / "file.txt").write_text("v1", encoding="utf-8")

    # Install
    target_repo = tmp_path / "target"
    target_repo.mkdir()
    install_to_repo(source_agent, target_repo)

    # Customize README.md
    target_agent = target_repo / ".agent"
    readme_path = target_agent / "README.md"
    original_content = readme_path.read_text(encoding="utf-8")

    # Add custom section (preserving frontmatter)
    custom_content = original_content + "\n\n## Custom Section\n\nMy custom notes here.\n"
    readme_path.write_text(custom_content, encoding="utf-8")

    # Update source
    (source_agent / "file.txt").write_text("v2", encoding="utf-8")

    # Update target
    update_repo(target_repo)

    # Verify custom content is preserved
    updated_content = readme_path.read_text(encoding="utf-8")
    assert "Custom Section" in updated_content
    assert "My custom notes here" in updated_content
    assert "managed: true" in updated_content
