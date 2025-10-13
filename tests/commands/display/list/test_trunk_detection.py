import json
from pathlib import Path

from click.testing import CliRunner

from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from tests.fakes.shell_ops import FakeShellOps
from workstack.cli.commands.list import _is_trunk_branch
from workstack.core.context import WorkstackContext


def test_trunk_branch_with_validation_result_trunk() -> None:
    """Branch with validationResult == "TRUNK" returns True."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        repo_root = Path.cwd()
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create graphite cache with main marked as TRUNK
        graphite_cache = {
            "branches": [
                ["main", {"validationResult": "TRUNK", "children": ["feature-1"]}],
                ["feature-1", {"parentBranchName": "main", "children": []}],
            ]
        }
        (git_dir / ".graphite_cache_persist").write_text(json.dumps(graphite_cache))

        git_ops = FakeGitOps(git_common_dirs={repo_root: git_dir})
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=Path("/tmp/workstacks"),
            use_graphite=True,
        )
        graphite_ops = FakeGraphiteOps()
        ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=FakeGitHubOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        assert _is_trunk_branch(ctx, repo_root, "main") is True


def test_non_trunk_branch_with_no_parent() -> None:
    """Branch with parentBranchName: None but no TRUNK marker returns True."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        repo_root = Path.cwd()
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create graphite cache with orphan branch (no parent, but not marked TRUNK)
        graphite_cache = {
            "branches": [
                ["orphan", {"parentBranchName": None, "children": ["feature-1"]}],
                ["feature-1", {"parentBranchName": "orphan", "children": []}],
            ]
        }
        (git_dir / ".graphite_cache_persist").write_text(json.dumps(graphite_cache))

        git_ops = FakeGitOps(git_common_dirs={repo_root: git_dir})
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=Path("/tmp/workstacks"),
            use_graphite=True,
        )
        graphite_ops = FakeGraphiteOps()
        ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=FakeGitHubOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        assert _is_trunk_branch(ctx, repo_root, "orphan") is True


def test_branch_with_parent() -> None:
    """Branch with parentBranchName: "main" returns False."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        repo_root = Path.cwd()
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create graphite cache with feature-1 having main as parent
        graphite_cache = {
            "branches": [
                ["main", {"validationResult": "TRUNK", "children": ["feature-1"]}],
                ["feature-1", {"parentBranchName": "main", "children": []}],
            ]
        }
        (git_dir / ".graphite_cache_persist").write_text(json.dumps(graphite_cache))

        git_ops = FakeGitOps(git_common_dirs={repo_root: git_dir})
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=Path("/tmp/workstacks"),
            use_graphite=True,
        )
        graphite_ops = FakeGraphiteOps()
        ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=FakeGitHubOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        assert _is_trunk_branch(ctx, repo_root, "feature-1") is False


def test_branch_not_in_cache() -> None:
    """Unknown branch name returns False."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        repo_root = Path.cwd()
        git_dir = Path(".git")
        git_dir.mkdir()

        # Create graphite cache without "unknown-branch"
        graphite_cache = {
            "branches": [
                ["main", {"validationResult": "TRUNK", "children": []}],
            ]
        }
        (git_dir / ".graphite_cache_persist").write_text(json.dumps(graphite_cache))

        git_ops = FakeGitOps(git_common_dirs={repo_root: git_dir})
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=Path("/tmp/workstacks"),
            use_graphite=True,
        )
        graphite_ops = FakeGraphiteOps()
        ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=FakeGitHubOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        assert _is_trunk_branch(ctx, repo_root, "unknown-branch") is False


def test_missing_git_directory() -> None:
    """get_git_common_dir returns None, function returns False."""
    repo_root = Path.cwd()

    # FakeGitOps with no git_common_dirs configured
    git_ops = FakeGitOps(git_common_dirs={})
    global_config_ops = FakeGlobalConfigOps(
        workstacks_root=Path("/tmp/workstacks"),
        use_graphite=True,
    )
    graphite_ops = FakeGraphiteOps()
    ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=global_config_ops,
        graphite_ops=graphite_ops,
        github_ops=FakeGitHubOps(),
        shell_ops=FakeShellOps(),
        dry_run=False,
    )

    assert _is_trunk_branch(ctx, repo_root, "main") is False


def test_missing_cache_file() -> None:
    """.graphite_cache_persist doesn't exist, function returns False."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        repo_root = Path.cwd()
        git_dir = Path(".git")
        git_dir.mkdir()

        # No cache file created

        git_ops = FakeGitOps(git_common_dirs={repo_root: git_dir})
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=Path("/tmp/workstacks"),
            use_graphite=True,
        )
        graphite_ops = FakeGraphiteOps()
        ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            graphite_ops=graphite_ops,
            github_ops=FakeGitHubOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        assert _is_trunk_branch(ctx, repo_root, "main") is False


def test_cache_data_optimization() -> None:
    """When cache_data is provided, function uses it instead of loading from disk."""
    repo_root = Path.cwd()

    # No git_dir setup - should fail if function tries to load from disk
    git_ops = FakeGitOps(git_common_dirs={})
    global_config_ops = FakeGlobalConfigOps(
        workstacks_root=Path("/tmp/workstacks"),
        use_graphite=True,
    )
    graphite_ops = FakeGraphiteOps()
    ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=global_config_ops,
        graphite_ops=graphite_ops,
        github_ops=FakeGitHubOps(),
        shell_ops=FakeShellOps(),
        dry_run=False,
    )

    # Pre-loaded cache data
    cache_data = {
        "branches": [
            ["main", {"validationResult": "TRUNK", "children": ["feature-1"]}],
            ["feature-1", {"parentBranchName": "main", "children": []}],
        ]
    }

    # Should use provided cache_data instead of trying to load from disk
    assert _is_trunk_branch(ctx, repo_root, "main", cache_data) is True
    assert _is_trunk_branch(ctx, repo_root, "feature-1", cache_data) is False
