from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from workstack.cli import cli


def test_rm_force_removes_directory() -> None:
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

        # Create worktree in the location determined by global config
        repo_name = cwd.name
        wt = workstacks_root / repo_name / "foo"
        wt.mkdir(parents=True)
        (wt / "hello.txt").write_text("hello world", encoding="utf-8")

        # Mock GLOBAL_CONFIG_PATH to use our isolated config
        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["rm", "foo", "-f"])
            assert result.exit_code == 0, result.output
            # Should print the removed path
            assert result.output.strip().endswith(str(wt))
            assert not wt.exists()


def test_rm_prompts_and_aborts_on_no() -> None:
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

        # Create worktree in the location determined by global config
        repo_name = cwd.name
        wt = workstacks_root / repo_name / "bar"
        wt.mkdir(parents=True)

        # Mock GLOBAL_CONFIG_PATH to use our isolated config
        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["rm", "bar"], input="n\n")
            assert result.exit_code == 0, result.output
            # Should not remove when user says 'n'
            assert wt.exists()
