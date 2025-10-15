from pathlib import Path

from dot_agent import list_available_files
from dot_agent.config import DotAgentConfig
from dot_agent.sync import _expand_managed_files, collect_statuses, generate_diff, sync_all_files


def test_sync_creates_expected_files(tmp_path: Path) -> None:
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    config = DotAgentConfig.default()
    results = sync_all_files(agent_dir, config, force=False, dry_run=False)

    for relative_path, result in results.items():
        assert result.changed
        assert (agent_dir / relative_path).exists()

    statuses = collect_statuses(agent_dir, config)
    assert all(status == "up-to-date" for status in statuses.values())


def test_sync_dry_run_reports_without_writing(tmp_path: Path) -> None:
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    config = DotAgentConfig.default()
    results = sync_all_files(agent_dir, config, force=False, dry_run=True)

    assert any(result.changed for result in results.values())
    available_resources = set(list_available_files())
    expanded_files = _expand_managed_files(config.managed_files, available_resources)
    for relative_path in expanded_files:
        assert not (agent_dir / relative_path).exists()


def test_collect_statuses_detects_modified_file(tmp_path: Path) -> None:
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    config = DotAgentConfig.default()
    sync_all_files(agent_dir, config, force=False, dry_run=False)

    available_resources = set(list_available_files())
    expanded_files = _expand_managed_files(config.managed_files, available_resources)
    target = agent_dir / next(iter(expanded_files))
    target.write_text("modified content", encoding="utf-8")

    statuses = collect_statuses(agent_dir, config)
    assert "different" in statuses.values()


def test_expand_managed_files_handles_directory_pattern() -> None:
    available_resources = {"tools/gt.md", "tools/gh.md", "tools/workstack.md"}
    managed_files = ("tools/",)

    expanded = _expand_managed_files(managed_files, available_resources)

    assert len(expanded) == 3
    assert "tools/gh.md" in expanded
    assert "tools/gt.md" in expanded
    assert "tools/workstack.md" in expanded


def test_expand_managed_files_preserves_specific_files() -> None:
    available_resources = {"tools/gt.md", "tools/gh.md", "docs/README.md"}
    managed_files = ("tools/", "docs/README.md")

    expanded = _expand_managed_files(managed_files, available_resources)

    assert len(expanded) == 3
    assert "tools/gh.md" in expanded
    assert "tools/gt.md" in expanded
    assert "docs/README.md" in expanded


def test_generate_diff_includes_headers() -> None:
    diff_text = generate_diff(
        "tools/sample.md",
        "old line\n",
        "new line\n",
    )
    assert diff_text.startswith("--- a/tools/sample.md")
    assert "\n+++ b/tools/sample.md" in diff_text
