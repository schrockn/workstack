from pathlib import Path

from click.testing import CliRunner

from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from workstack.cli import cli
from workstack.context import WorkstackContext


def test_rm_force_removes_directory() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create worktree in the location determined by global config
        repo_name = cwd.name
        wt = workstacks_root / repo_name / "foo"
        wt.mkdir(parents=True)
        (wt / "hello.txt").write_text("hello world", encoding="utf-8")

        # Build fake git ops
        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})

        # Build fake global config ops
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(git_ops=git_ops, global_config_ops=global_config_ops)

        result = runner.invoke(cli, ["rm", "foo", "-f"], obj=test_ctx)
        assert result.exit_code == 0, result.output
        # Should print the removed path
        assert result.output.strip().endswith(str(wt))
        assert not wt.exists()


def test_rm_prompts_and_aborts_on_no() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Set up isolated environment
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Create git repo
        git_dir = cwd / ".git"
        git_dir.mkdir()

        # Create worktree in the location determined by global config
        repo_name = cwd.name
        wt = workstacks_root / repo_name / "bar"
        wt.mkdir(parents=True)

        # Build fake git ops
        git_ops = FakeGitOps(git_common_dirs={cwd: git_dir})

        # Build fake global config ops
        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        test_ctx = WorkstackContext(git_ops=git_ops, global_config_ops=global_config_ops)

        result = runner.invoke(cli, ["rm", "bar"], input="n\n", obj=test_ctx)
        assert result.exit_code == 0, result.output
        # Should not remove when user says 'n'
        assert wt.exists()
