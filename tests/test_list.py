from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from workstack.cli import cli


def test_list_outputs_names_not_paths() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path(".git").mkdir()
        (Path(".workstack") / "foo").mkdir(parents=True)
        (Path(".workstack") / "bar").mkdir(parents=True)

        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0, result.output
        lines = result.output.strip().splitlines()

        cwd = Path.cwd()
        # First line should be root
        assert lines[0].startswith(".")
        assert "root" in lines[0].lower()

        # Remaining lines should be worktrees, sorted
        worktree_lines = sorted(lines[1:])
        expected_foo = cwd / ".workstack" / "foo" / "activate.sh"
        expected_bar = cwd / ".workstack" / "bar" / "activate.sh"
        assert worktree_lines == [
            f"bar (source {expected_bar})",
            f"foo (source {expected_foo})",
        ]
