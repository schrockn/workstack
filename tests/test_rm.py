from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from workstack.cli import cli


def test_rm_force_removes_directory() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path(".git").mkdir()
        wt = Path(".workstack") / "foo"
        (wt).mkdir(parents=True)
        (wt / "hello.txt").write_text("hello world", encoding="utf-8")

        result = runner.invoke(cli, ["rm", "foo", "-f"])
        assert result.exit_code == 0, result.output
        # Should print the removed path
        assert result.output.strip().endswith(str(wt))
        assert not wt.exists()


def test_rm_prompts_and_aborts_on_no() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path(".git").mkdir()
        wt = Path(".workstack") / "bar"
        (wt).mkdir(parents=True)

        result = runner.invoke(cli, ["rm", "bar"], input="n\n")
        assert result.exit_code == 0, result.output
        # Should not remove when user says 'n'
        assert wt.exists()
