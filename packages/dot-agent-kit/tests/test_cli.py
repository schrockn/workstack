from pathlib import Path

from click.testing import CliRunner

from dot_agent_kit.cli import main


def test_list_command_shows_known_files() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["list"])
    assert result.exit_code == 0
    assert "tools/gt.md" in result.output


def test_init_creates_agent_directory_structure() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0
        assert Path(".agent/tools/gt.md").exists()


def test_sync_reports_dry_run_changes() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(main, ["init"])
        target = Path(".agent/tools/gt.md")
        target.write_text("outdated", encoding="utf-8")

        result = runner.invoke(main, ["sync", "--dry-run"])
        assert result.exit_code == 0
        assert "Would update" in result.output


def test_extract_requires_force_for_overwrite() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        init_result = runner.invoke(main, ["init"])
        assert init_result.exit_code == 0
        result = runner.invoke(main, ["extract", "tools/gt.md"])
        assert result.exit_code != 0
        assert "already exists" in result.output

        result_force = runner.invoke(main, ["extract", "tools/gt.md", "--force"])
        assert result_force.exit_code == 0
