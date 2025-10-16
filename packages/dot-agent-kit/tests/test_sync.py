from pathlib import Path

from dot_agent_kit.resource_loader import list_available_files, read_resource_file
from dot_agent_kit.sync import (
    collect_statuses,
    detect_status,
    generate_diff,
    sync_all_files,
)


def test_sync_creates_expected_files(tmp_path: Path) -> None:
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    results = sync_all_files(agent_dir, force=False, dry_run=False)

    for relative_path, result in results.items():
        assert result.changed
        assert (agent_dir / "packages" / relative_path).exists()

    statuses = collect_statuses(agent_dir)
    assert all(status == "up-to-date" for status in statuses.values())


def test_sync_dry_run_reports_without_writing(tmp_path: Path) -> None:
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    results = sync_all_files(agent_dir, force=False, dry_run=True)

    assert any(result.changed for result in results.values())
    available_resources = list_available_files()
    for relative_path in available_resources:
        assert not (agent_dir / "packages" / relative_path).exists()


def test_collect_statuses_detects_modified_file(tmp_path: Path) -> None:
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    sync_all_files(agent_dir, force=False, dry_run=False)

    available_resources = list_available_files()
    target = agent_dir / "packages" / available_resources[0]
    target.write_text("modified content", encoding="utf-8")

    statuses = collect_statuses(agent_dir)
    assert "different" in statuses.values()


def test_generate_diff_includes_headers() -> None:
    diff_text = generate_diff(
        "tools/sample.md",
        "old line\n",
        "new line\n",
    )
    assert diff_text.startswith("--- a/tools/sample.md")
    assert "\n+++ b/tools/sample.md" in diff_text


def test_sync_creates_packages_subdirectory(tmp_path: Path) -> None:
    """Verify synced files go to .agent/packages/ not .agent/"""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    results = sync_all_files(agent_dir, force=False, dry_run=False)

    # Verify sync returned results
    assert results

    # Pick a known resource file
    available_files = list_available_files()
    if not available_files:
        return
    test_file = available_files[0]

    # Assert: file should exist in packages/ subdirectory
    correct_path = agent_dir / "packages" / test_file
    assert correct_path.exists(), f"File should be at {correct_path}"

    # Assert: file should NOT exist at wrong location
    wrong_path = agent_dir / test_file
    assert not wrong_path.exists(), f"File should not be at {wrong_path}"

    # Assert: content should match
    resource_content = read_resource_file(test_file)
    synced_content = correct_path.read_text(encoding="utf-8")
    assert synced_content == resource_content


def test_detect_status_reads_from_packages_directory(tmp_path: Path) -> None:
    """Verify status detection reads from correct path"""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    # Pick a known resource file
    available_files = list_available_files()
    if not available_files:
        return
    test_file = available_files[0]
    available_resources = set(available_files)

    # Create file in correct location with correct content
    correct_path = agent_dir / "packages" / test_file
    correct_path.parent.mkdir(parents=True, exist_ok=True)
    resource_content = read_resource_file(test_file)
    correct_path.write_text(resource_content, encoding="utf-8")

    # Verify status is "up-to-date"
    status = detect_status(agent_dir, test_file, available_resources)
    assert status == "up-to-date"

    # Create file in wrong location (should be ignored)
    wrong_path = agent_dir / test_file
    wrong_path.parent.mkdir(parents=True, exist_ok=True)
    wrong_path.write_text(resource_content, encoding="utf-8")

    # Delete the correct location
    correct_path.unlink()

    # Verify status is "missing" (ignores wrong location)
    status = detect_status(agent_dir, test_file, available_resources)
    assert status == "missing"
