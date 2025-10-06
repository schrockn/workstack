import json
import re
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from tests.builders.gitops import GitOpsBuilder
from workstack.cli import cli
from workstack.context import WorkstackContext
from workstack.gitops import WorktreeInfo


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
        (work_dir / "bar").mkdir(parents=True)

        # Build fake git ops with worktree info
        git_ops = (
            GitOpsBuilder()
            .with_worktrees(
                cwd,
                [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=work_dir / "foo", branch="foo"),
                    WorktreeInfo(path=work_dir / "bar", branch="feature/bar"),
                ],
            )
            .with_git_common_dir(cwd, cwd / ".git")
            .build()
        )

        test_ctx = WorkstackContext(git_ops=git_ops)

        # Mock GLOBAL_CONFIG_PATH and pass context through Click
        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["list"], obj=test_ctx)
            assert result.exit_code == 0, result.output

            # Strip ANSI codes for easier comparison
            output = strip_ansi(result.output)
            lines = output.strip().splitlines()

            # First line should be root with branch
            assert lines[0].startswith("root")
            assert "[main]" in lines[0]

            # Remaining lines should be worktrees with branches, sorted
            worktree_lines = sorted(lines[1:])
            assert worktree_lines == [
                "bar [feature/bar]",
                "foo [foo]",
            ]


def test_list_with_stacks_flag() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        global_config_dir = cwd / ".workstack_config"
        global_config_dir.mkdir()
        workstacks_root = cwd / "workstacks"
        (global_config_dir / "config.toml").write_text(
            f'workstacks_root = "{workstacks_root}"\nuse_graphite = true\n'
        )

        # Create git repo structure
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create graphite cache persist file with a linear stack
        # AND a sibling branch to verify it's NOT included
        graphite_cache = {
            "branches": [
                [
                    "main",
                    {
                        "validationResult": "TRUNK",
                        "children": ["schrockn/ts-phase-1", "sibling-branch"],
                    },
                ],
                [
                    "schrockn/ts-phase-1",
                    {"parentBranchName": "main", "children": ["schrockn/ts-phase-2"]},
                ],
                [
                    "schrockn/ts-phase-2",
                    {
                        "parentBranchName": "schrockn/ts-phase-1",
                        "children": ["schrockn/ts-phase-3"],
                    },
                ],
                [
                    "schrockn/ts-phase-3",
                    {"parentBranchName": "schrockn/ts-phase-2", "children": []},
                ],
                ["sibling-branch", {"parentBranchName": "main", "children": []}],
            ]
        }
        (git_dir / ".graphite_cache_persist").write_text(json.dumps(graphite_cache))

        # Create worktrees
        repo_name = cwd.name
        work_dir = workstacks_root / repo_name
        (work_dir / "ts").mkdir(parents=True)

        # Build fake git ops
        git_ops = (
            GitOpsBuilder()
            .with_worktrees(
                cwd,
                [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=work_dir / "ts", branch="schrockn/ts-phase-2"),
                ],
            )
            .with_git_common_dir(cwd, git_dir)
            .with_git_common_dir(work_dir / "ts", git_dir)
            .with_current_branch(cwd, "main")
            .with_current_branch(work_dir / "ts", "schrockn/ts-phase-2")
            .build()
        )

        test_ctx = WorkstackContext(git_ops=git_ops)

        # Mock GLOBAL_CONFIG_PATH and pass context through Click
        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
            assert result.exit_code == 0, result.output

            # Strip ANSI codes for easier assertion
            output = strip_ansi(result.output)
            lines = output.strip().splitlines()

            # Find the root section and ts section
            root_section_start = None
            ts_section_start = None
            for i, line in enumerate(lines):
                if "root [main]" in line:
                    root_section_start = i
                if "ts [schrockn/ts-phase-2]" in line:
                    ts_section_start = i

            assert root_section_start is not None
            assert ts_section_start is not None

            # Get the ts section (from ts header to end)
            ts_section = lines[ts_section_start:]
            ts_section_text = "\n".join(ts_section)

            # Check ts worktree stack shows linear chain in reversed order
            # (descendants at top, trunk at bottom)
            assert "ts [schrockn/ts-phase-2]" in ts_section_text
            assert "◯  schrockn/ts-phase-3" in ts_section_text
            assert "◉  schrockn/ts-phase-2" in ts_section_text
            assert "◯  schrockn/ts-phase-1" in ts_section_text
            assert "◯  main" in ts_section_text

            # Verify sibling branch is NOT shown (regression test)
            assert "sibling-branch" not in output

            # Verify order within ts section: phase-3 before phase-2, phase-2 before phase-1, etc.
            # Use the marked versions to avoid matching the header
            phase_3_idx = ts_section_text.index("◯  schrockn/ts-phase-3")
            phase_2_idx = ts_section_text.index("◉  schrockn/ts-phase-2")
            phase_1_idx = ts_section_text.index("◯  schrockn/ts-phase-1")
            main_in_stack_idx = ts_section_text.index("◯  main")

            assert phase_3_idx < phase_2_idx < phase_1_idx < main_in_stack_idx


def test_list_with_stacks_graphite_disabled() -> None:
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

        # Build fake git ops
        git_ops = (
            GitOpsBuilder()
            .with_worktrees(cwd, [WorktreeInfo(path=cwd, branch="main")])
            .with_git_common_dir(cwd, cwd / ".git")
            .build()
        )

        test_ctx = WorkstackContext(git_ops=git_ops)

        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
            assert result.exit_code == 1
            assert "Error: --stacks requires graphite to be enabled" in result.output


def test_list_with_stacks_no_graphite_cache() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        global_config_dir = cwd / ".workstack_config"
        global_config_dir.mkdir()
        workstacks_root = cwd / "workstacks"
        (global_config_dir / "config.toml").write_text(
            f'workstacks_root = "{workstacks_root}"\nuse_graphite = true\n'
        )

        # Create git repo but no graphite cache file
        git_dir = Path(".git")
        git_dir.mkdir()

        # Build fake git ops
        git_ops = (
            GitOpsBuilder()
            .with_worktrees(cwd, [WorktreeInfo(path=cwd, branch="main")])
            .with_git_common_dir(cwd, git_dir)
            .build()
        )

        test_ctx = WorkstackContext(git_ops=git_ops)

        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            # Should succeed but not show stack info (graceful degradation)
            result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
            assert result.exit_code == 0, result.output
            output = strip_ansi(result.output)
            # Should show worktree but no stack visualization
            assert "root [main]" in output
            # Should not have any circle markers
            assert "◉" not in output
            assert "◯" not in output


def test_list_with_stacks_highlights_current_branch_not_worktree_branch() -> None:
    """
    Regression test for bug where the worktree's checkout branch was highlighted
    instead of the current working directory's checked-out branch.

    When running `workstack ls --stacks` from a worktree that has switched branches
    (e.g., temporal-stack worktree is on ts-phase-4, but current directory is on ts-phase-3),
    the highlighted marker (◉) should show ts-phase-3, not ts-phase-4.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        global_config_dir = cwd / ".workstack_config"
        global_config_dir.mkdir()
        workstacks_root = cwd / "workstacks"
        (global_config_dir / "config.toml").write_text(
            f'workstacks_root = "{workstacks_root}"\nuse_graphite = true\n'
        )

        # Create git repo structure
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create graphite cache with a linear stack
        graphite_cache = {
            "branches": [
                [
                    "main",
                    {
                        "validationResult": "TRUNK",
                        "children": ["schrockn/ts-phase-1"],
                    },
                ],
                [
                    "schrockn/ts-phase-1",
                    {"parentBranchName": "main", "children": ["schrockn/ts-phase-2"]},
                ],
                [
                    "schrockn/ts-phase-2",
                    {
                        "parentBranchName": "schrockn/ts-phase-1",
                        "children": ["schrockn/ts-phase-3"],
                    },
                ],
                [
                    "schrockn/ts-phase-3",
                    {
                        "parentBranchName": "schrockn/ts-phase-2",
                        "children": ["schrockn/ts-phase-4"],
                    },
                ],
                [
                    "schrockn/ts-phase-4",
                    {"parentBranchName": "schrockn/ts-phase-3", "children": []},
                ],
            ]
        }
        (git_dir / ".graphite_cache_persist").write_text(json.dumps(graphite_cache))

        # Create worktree
        repo_name = cwd.name
        work_dir = workstacks_root / repo_name
        temporal_stack_dir = work_dir / "temporal-stack"
        temporal_stack_dir.mkdir(parents=True)

        # Build fake git ops
        # Key setup: The worktree is registered with ts-phase-4, but currently checked out to ts-phase-3
        git_ops = (
            GitOpsBuilder()
            .with_worktrees(
                cwd,
                [
                    WorktreeInfo(path=cwd, branch="main"),
                    WorktreeInfo(path=temporal_stack_dir, branch="schrockn/ts-phase-4"),
                ],
            )
            .with_git_common_dir(cwd, git_dir)
            .with_git_common_dir(temporal_stack_dir, git_dir)
            .with_current_branch(cwd, "main")
            .with_current_branch(temporal_stack_dir, "schrockn/ts-phase-3")  # Actually on phase-3
            .build()
        )

        test_ctx = WorkstackContext(git_ops=git_ops)

        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
            assert result.exit_code == 0, result.output

            # Strip ANSI codes for easier assertion
            output = strip_ansi(result.output)

            # The stack visualization should highlight ts-phase-3 (actual current branch)
            # NOT ts-phase-4 (the worktree's registered branch from git worktree list)
            lines = output.splitlines()

            # Find the stack visualization lines
            phase_3_line = None
            phase_4_line = None
            for line in lines:
                if "schrockn/ts-phase-3" in line and line.strip().startswith("◉"):
                    phase_3_line = line
                if "schrockn/ts-phase-4" in line and line.strip().startswith("◉"):
                    phase_4_line = line

            # FIXED: ts-phase-3 should be highlighted because that's the actual checked-out branch
            assert phase_3_line is not None, (
                "Expected ts-phase-3 to be highlighted with ◉, "
                f"but it wasn't found in output:\n{output}"
            )

            # ts-phase-4 should NOT be highlighted
            assert phase_4_line is None, (
                "ts-phase-4 should NOT be highlighted with ◉ "
                "because it's only the registered branch, not the actual checked-out branch. "
                f"Output:\n{output}"
            )


def test_list_with_stacks_root_repo_does_not_duplicate_branch() -> None:
    """
    Regression test: Root repo should be displayed as "root", not the branch name.

    For example, if on "master" branch with stack [foo, master]:
    WRONG:
        master [master]
          ◯  foo
          ◉  master   <- duplicate!

    CORRECT:
        root [master]
          ◯  foo
          ◉  master
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        global_config_dir = cwd / ".workstack_config"
        global_config_dir.mkdir()
        workstacks_root = cwd / "workstacks"
        (global_config_dir / "config.toml").write_text(
            f'workstacks_root = "{workstacks_root}"\nuse_graphite = true\n'
        )

        # Create git repo structure
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create graphite cache with master as parent of foo
        graphite_cache = {
            "branches": [
                ["master", {"validationResult": "TRUNK", "children": ["foo"]}],
                ["foo", {"parentBranchName": "master", "children": []}],
            ]
        }
        (git_dir / ".graphite_cache_persist").write_text(json.dumps(graphite_cache))

        # Build fake git ops - only root repo on master
        git_ops = (
            GitOpsBuilder()
            .with_worktrees(cwd, [WorktreeInfo(path=cwd, branch="master")])
            .with_git_common_dir(cwd, git_dir)
            .with_current_branch(cwd, "master")
            .build()
        )

        test_ctx = WorkstackContext(git_ops=git_ops)

        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
            assert result.exit_code == 0, result.output

            # Strip ANSI codes for easier assertion
            output = strip_ansi(result.output)
            lines = output.strip().splitlines()

            # Should have header line with "root" as the name
            assert "root [master]" in lines[0]

            # Verify the full stack is shown
            assert "◯  foo" in output
            assert "◉  master" in output


def test_list_with_stacks_filters_branches_in_other_worktrees() -> None:
    """
    Regression test: Branches checked out in other worktrees should not appear in root's stack.

    When root is on master with stack [master, foo] and there's a foo worktree:

    WRONG:
        root [master]
          ◯  foo       <- foo shouldn't appear here
          ◉  master

        foo [foo]
          ◉  foo
          ◯  master

    CORRECT:
        root [master]
          ◉  master    <- only master shown, foo filtered out

        foo [foo]
          ◉  foo
          ◯  master
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        global_config_dir = cwd / ".workstack_config"
        global_config_dir.mkdir()
        workstacks_root = cwd / "workstacks"
        (global_config_dir / "config.toml").write_text(
            f'workstacks_root = "{workstacks_root}"\nuse_graphite = true\n'
        )

        # Create git repo structure
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create graphite cache with master as parent of foo
        graphite_cache = {
            "branches": [
                ["master", {"validationResult": "TRUNK", "children": ["foo"]}],
                ["foo", {"parentBranchName": "master", "children": []}],
            ]
        }
        (git_dir / ".graphite_cache_persist").write_text(json.dumps(graphite_cache))

        # Create foo worktree
        repo_name = cwd.name
        work_dir = workstacks_root / repo_name
        foo_worktree_dir = work_dir / "foo"
        foo_worktree_dir.mkdir(parents=True)

        # Build fake git ops - root on master, foo worktree on foo branch
        git_ops = (
            GitOpsBuilder()
            .with_worktrees(
                cwd,
                [
                    WorktreeInfo(path=cwd, branch="master"),
                    WorktreeInfo(path=foo_worktree_dir, branch="foo"),
                ],
            )
            .with_git_common_dir(cwd, git_dir)
            .with_git_common_dir(foo_worktree_dir, git_dir)
            .with_current_branch(cwd, "master")
            .with_current_branch(foo_worktree_dir, "foo")
            .build()
        )

        test_ctx = WorkstackContext(git_ops=git_ops)

        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            result = runner.invoke(cli, ["list", "--stacks"], obj=test_ctx)
            assert result.exit_code == 0, result.output

            # Strip ANSI codes for easier assertion
            output = strip_ansi(result.output)
            lines = output.strip().splitlines()

            # Find the root section and foo section
            root_section_start = None
            foo_section_start = None
            for i, line in enumerate(lines):
                if "root [master]" in line:
                    root_section_start = i
                if "foo [foo]" in line:
                    foo_section_start = i

            assert root_section_start is not None, "Should have root section"
            assert foo_section_start is not None, "Should have foo worktree section"

            # Get root section lines (from root header to foo header)
            root_section = lines[root_section_start:foo_section_start]

            # Root section should ONLY show master, NOT foo
            root_section_text = "\n".join(root_section)
            assert "◉  master" in root_section_text, "Root should show master"
            assert "foo" not in root_section_text, (
                "Root section should NOT contain foo branch since it's checked out "
                f"in a different worktree. Root section:\n{root_section_text}"
            )

            # Get foo section lines (from foo header to end)
            foo_section = lines[foo_section_start:]
            foo_section_text = "\n".join(foo_section)

            # Foo section should show both foo (highlighted) and master
            assert "◉  foo" in foo_section_text, "Foo worktree should highlight foo branch"
            assert "◯  master" in foo_section_text, "Foo worktree should show master in stack"
