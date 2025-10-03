from __future__ import annotations

import re
import subprocess
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from workstack.cli import cli


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


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

        # Mock git worktree list to return branch info
        git_worktree_output = f"""worktree {cwd}
HEAD abc123
branch refs/heads/main

worktree {work_dir / "foo"}
HEAD def456
branch refs/heads/work/foo

worktree {work_dir / "bar"}
HEAD ghi789
branch refs/heads/feature/bar

"""

        # Mock GLOBAL_CONFIG_PATH to use our isolated config
        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            # Create a selective mock that only mocks "git worktree list --porcelain"
            original_run = subprocess.run

            def selective_mock_run(cmd, *args, **kwargs):
                if cmd == ["git", "worktree", "list", "--porcelain"]:
                    mock_result = mock.Mock()
                    mock_result.stdout = git_worktree_output
                    mock_result.returncode = 0
                    return mock_result
                return original_run(cmd, *args, **kwargs)

            with mock.patch("workstack.git.subprocess.run", side_effect=selective_mock_run):
                result = runner.invoke(cli, ["list"])
                assert result.exit_code == 0, result.output
                lines = result.output.strip().splitlines()

                # First line should be root with branch
                assert lines[0].startswith(".")
                assert "[main]" in lines[0]
                assert "root" in lines[0].lower()

                # Remaining lines should be worktrees with branches, sorted
                worktree_lines = sorted(lines[1:])
                expected_foo = work_dir / "foo" / "activate.sh"
                expected_bar = work_dir / "bar" / "activate.sh"
                assert worktree_lines == [
                    f"bar [feature/bar] (source {expected_bar})",
                    f"foo [work/foo] (source {expected_foo})",
                ]
