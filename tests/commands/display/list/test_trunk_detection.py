"""CLI tests for trunk branch handling in list command.

This file tests CLI-specific behavior of how trunk branches are displayed
or filtered in the list command output.

The business logic of trunk detection (_is_trunk_branch function) is tested in:
- tests/unit/detection/test_trunk_detection.py

This file trusts that unit layer and only tests CLI integration.
"""

import json
from pathlib import Path

from click.testing import CliRunner

from tests.commands.display.list import strip_ansi
from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps, WorktreeInfo
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from tests.fakes.shell_ops import FakeShellOps
from workstack.cli.cli import cli
from workstack.core.context import WorkstackContext


def test_list_with_main_trunk() -> None:
    """List command handles main trunk branch correctly (CLI layer)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create graphite cache with main as trunk
        graphite_cache = {
            "branches": [
                ["main", {"validationResult": "TRUNK", "children": ["feature"]}],
                ["feature", {"parentBranchName": "main", "children": []}],
            ]
        }
        (git_dir / ".graphite_cache_persist").write_text(
            json.dumps(graphite_cache), encoding="utf-8"
        )

        workstacks_root = cwd / "workstacks"
        feature_dir = workstacks_root / cwd.name / "feature"
        feature_dir.mkdir(parents=True)

        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=feature_dir, branch="feature"),
                ],
            },
            git_common_dirs={cwd: git_dir, feature_dir: git_dir},
            current_branches={cwd: "main", feature_dir: "feature"},
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
            show_pr_info=False,
        )

        ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=FakeGraphiteOps(),
            github_ops=FakeGitHubOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["list", "--stacks"], obj=ctx)

        # Assert - CLI output formatting
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "main" in output or "feature" in output


def test_list_with_master_trunk() -> None:
    """List command handles master trunk branch correctly (CLI layer)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create graphite cache with master as trunk
        graphite_cache = {
            "branches": [
                ["master", {"validationResult": "TRUNK", "children": ["feature"]}],
                ["feature", {"parentBranchName": "master", "children": []}],
            ]
        }
        (git_dir / ".graphite_cache_persist").write_text(
            json.dumps(graphite_cache), encoding="utf-8"
        )

        workstacks_root = cwd / "workstacks"
        feature_dir = workstacks_root / cwd.name / "feature"
        feature_dir.mkdir(parents=True)

        git_ops = FakeGitOps(
            worktrees={
                cwd: [
                    WorktreeInfo(path=cwd, branch="master"),
                    WorktreeInfo(path=feature_dir, branch="feature"),
                ],
            },
            git_common_dirs={cwd: git_dir, feature_dir: git_dir},
            current_branches={cwd: "master", feature_dir: "feature"},
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=True,
            show_pr_info=False,
        )

        ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=FakeGraphiteOps(),
            github_ops=FakeGitHubOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["list", "--stacks"], obj=ctx)

        # Assert - CLI output formatting
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "master" in output or "feature" in output
