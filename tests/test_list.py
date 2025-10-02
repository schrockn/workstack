from __future__ import annotations

from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from workstack.cli import cli


def test_list_outputs_names_not_paths() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        global_config_dir = cwd / ".workstack_config"
        global_config_dir.mkdir()
        workstacks_root = cwd / "workstacks"
        (global_config_dir / "config.toml").write_text(
            f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
        )

        # Create git repo
        Path(".git").mkdir()

        # Create worktrees in the location determined by global config
        repo_name = cwd.name
        work_dir = workstacks_root / repo_name
        (work_dir / "foo").mkdir(parents=True)
        (work_dir / "foo" / "activate.sh").write_text("#!/bin/bash\n", encoding="utf-8")
        (work_dir / "bar").mkdir(parents=True)
        (work_dir / "bar" / "activate.sh").write_text("#!/bin/bash\n", encoding="utf-8")

        # Mock GLOBAL_CONFIG_PATH to use our isolated config
        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["list"])
            assert result.exit_code == 0, result.output
            lines = result.output.strip().splitlines()

            # First line should be root
            assert lines[0].startswith(".")
            assert "root" in lines[0].lower()

            # Remaining lines should be worktrees, sorted
            worktree_lines = sorted(lines[1:])
            expected_foo = work_dir / "foo" / "activate.sh"
            expected_bar = work_dir / "bar" / "activate.sh"
            assert worktree_lines == [
                f"bar (source {expected_bar})",
                f"foo (source {expected_foo})",
            ]
