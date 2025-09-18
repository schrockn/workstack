from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from work.cli import cli


def test_list_outputs_names_not_paths() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path(".git").mkdir()
        (Path(".work") / "foo").mkdir(parents=True)
        (Path(".work") / "bar").mkdir(parents=True)

        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0, result.output
        lines = sorted(result.output.strip().splitlines())

        cwd = Path.cwd()
        expected_foo = cwd / ".work" / "foo" / "activate.sh"
        expected_bar = cwd / ".work" / "bar" / "activate.sh"
        assert lines == [
            f"bar (source {expected_bar})",
            f"foo (source {expected_foo})",
        ]
