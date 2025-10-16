from pathlib import Path

from click.testing import CliRunner

from dot_agent_kit.cli import main


def test_list_command_shows_known_files() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["list"])
    assert result.exit_code == 0
    assert "tools/gt/gt.md" in result.output


def test_init_creates_agent_directory_structure() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0
        assert Path(".agent/packages/tools/gt/gt.md").exists()


def test_sync_reports_dry_run_changes() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(main, ["init"])
        target = Path(".agent/packages/tools/gt/gt.md")
        target.write_text("outdated", encoding="utf-8")

        result = runner.invoke(main, ["sync", "--dry-run"])
        assert result.exit_code == 0
        assert "Would update" in result.output
