import json
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
        (work_dir / "bar").mkdir(parents=True)

        # Mock git worktree list to return branch info
        git_worktree_output = f"""worktree {cwd}
HEAD abc123
branch refs/heads/main

worktree {work_dir / "foo"}
HEAD def456
branch refs/heads/foo

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
                assert lines[0].startswith("main")
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

        # Mock git worktree list
        git_worktree_output = f"""worktree {cwd}
HEAD abc123
branch refs/heads/main

worktree {work_dir / "ts"}
HEAD def456
branch refs/heads/schrockn/ts-phase-2

"""

        # Mock GLOBAL_CONFIG_PATH
        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            original_run = subprocess.run

            def selective_mock_run(cmd, *args, **kwargs):
                if cmd == ["git", "worktree", "list", "--porcelain"]:
                    mock_result = mock.Mock()
                    mock_result.stdout = git_worktree_output
                    mock_result.returncode = 0
                    return mock_result
                if cmd == ["git", "rev-parse", "--git-common-dir"]:
                    mock_result = mock.Mock()
                    mock_result.stdout = str(git_dir) + "\n"
                    mock_result.returncode = 0
                    return mock_result
                return original_run(cmd, *args, **kwargs)

            with mock.patch("workstack.git.subprocess.run", side_effect=selective_mock_run):
                result = runner.invoke(cli, ["list", "--stacks"])
                assert result.exit_code == 0, result.output

                # Strip ANSI codes for easier assertion
                output = strip_ansi(result.output)

                # Check ts worktree stack shows linear chain in reversed order
                # (descendants at top, trunk at bottom)
                assert "ts [schrockn/ts-phase-2]" in output
                assert "◯  schrockn/ts-phase-3" in output
                assert "◉  schrockn/ts-phase-2" in output
                assert "◯  schrockn/ts-phase-1" in output
                assert "◯  main" in output

                # Verify sibling branch is NOT shown (regression test)
                assert "sibling-branch" not in output

                # Verify order: phase-3 should appear before phase-2, phase-2 before phase-1, etc.
                phase_3_idx = output.index("schrockn/ts-phase-3")
                phase_2_idx = output.index("schrockn/ts-phase-2")
                phase_1_idx = output.index("schrockn/ts-phase-1")
                main_in_stack_idx = output.rindex(
                    "◯  main"
                )  # Last occurrence (in stack, not header)

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

        # Mock git worktree list
        git_worktree_output = f"""worktree {cwd}
HEAD abc123
branch refs/heads/main

"""

        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            original_run = subprocess.run

            def selective_mock_run(cmd, *args, **kwargs):
                if cmd == ["git", "worktree", "list", "--porcelain"]:
                    mock_result = mock.Mock()
                    mock_result.stdout = git_worktree_output
                    mock_result.returncode = 0
                    return mock_result
                return original_run(cmd, *args, **kwargs)

            with mock.patch("workstack.git.subprocess.run", side_effect=selective_mock_run):
                result = runner.invoke(cli, ["list", "--stacks"])
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

        # Mock git worktree list
        git_worktree_output = f"""worktree {cwd}
HEAD abc123
branch refs/heads/main

"""

        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            original_run = subprocess.run

            def selective_mock_run(cmd, *args, **kwargs):
                if cmd == ["git", "worktree", "list", "--porcelain"]:
                    mock_result = mock.Mock()
                    mock_result.stdout = git_worktree_output
                    mock_result.returncode = 0
                    return mock_result
                if cmd == ["git", "rev-parse", "--git-common-dir"]:
                    mock_result = mock.Mock()
                    mock_result.stdout = str(git_dir) + "\n"
                    mock_result.returncode = 0
                    return mock_result
                return original_run(cmd, *args, **kwargs)

            with mock.patch("workstack.git.subprocess.run", side_effect=selective_mock_run):
                # Should succeed but not show stack info (graceful degradation)
                result = runner.invoke(cli, ["list", "--stacks"])
                assert result.exit_code == 0, result.output
                output = strip_ansi(result.output)
                # Should show worktree but no stack visualization
                assert "main [main]" in output
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

        # Key setup: The worktree directory is checked out to ts-phase-4,
        # but we'll simulate running the command from ts-phase-3
        git_worktree_output = f"""worktree {cwd}
HEAD abc123
branch refs/heads/main

worktree {temporal_stack_dir}
HEAD def456
branch refs/heads/schrockn/ts-phase-4

"""

        with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", global_config_dir / "config.toml"):
            original_run = subprocess.run

            def selective_mock_run(cmd, *args, **kwargs):
                if cmd == ["git", "worktree", "list", "--porcelain"]:
                    mock_result = mock.Mock()
                    mock_result.stdout = git_worktree_output
                    mock_result.returncode = 0
                    return mock_result
                if cmd == ["git", "rev-parse", "--git-common-dir"]:
                    mock_result = mock.Mock()
                    mock_result.stdout = str(git_dir) + "\n"
                    mock_result.returncode = 0
                    return mock_result
                return original_run(cmd, *args, **kwargs)

            # Mock get_current_branch to simulate the worktree being on ts-phase-3
            # even though git worktree list shows ts-phase-4
            def mock_get_current_branch(cwd):
                # When called with the temporal-stack worktree path, return the actual checked-out branch
                if cwd == temporal_stack_dir:
                    return "schrockn/ts-phase-3"
                # For the main repo, return main
                if cwd == cwd.parent:  # This won't match in practice, but needed for completeness
                    return "main"
                return None

            with mock.patch("workstack.git.subprocess.run", side_effect=selective_mock_run):
                # Patch get_current_branch in the commands.list module where it's imported
                with mock.patch(
                    "workstack.commands.list.get_current_branch",
                    side_effect=mock_get_current_branch,
                ):
                    result = runner.invoke(cli, ["list", "--stacks"])
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
