"""Tests for the __prepare_cwd_recovery hidden command."""

import os
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

from workstack.cli.commands.prepare_cwd_recovery import prepare_cwd_recovery_cmd
from workstack.core.context import WorkstackContext


class StubGitOps:
    """GitOps stub that returns a fixed repo root."""

    def __init__(self, repo_root: Path | None) -> None:
        self._repo_root = repo_root

    def get_git_common_dir(self, _cwd: Path) -> Path | None:
        if self._repo_root is None:
            return None

        git_dir = self._repo_root / ".git"
        if not git_dir.exists():
            return None
        return git_dir


class StubGlobalConfigOps:
    """GlobalConfigOps stub that exposes a fixed workstacks root."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def get_workstacks_root(self) -> Path:
        return self._root


def build_ctx(repo_root: Path | None, workstacks_root: Path) -> WorkstackContext:
    """Create a WorkstackContext with stubbed dependencies."""
    git_ops = StubGitOps(repo_root)
    global_config_ops = StubGlobalConfigOps(workstacks_root)
    dummy = SimpleNamespace()
    return WorkstackContext(
        git_ops=git_ops,
        global_config_ops=global_config_ops,
        github_ops=dummy,
        graphite_ops=dummy,
        dry_run=False,
    )


def test_prepare_cwd_recovery_outputs_script(tmp_path: Path) -> None:
    """Command should emit a script path when inside a repo."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    workstacks_root = tmp_path / "workstacks"
    workstacks_root.mkdir()

    ctx = build_ctx(repo, workstacks_root)

    runner = CliRunner()

    original_cwd = os.getcwd()
    try:
        os.chdir(repo)
        result = runner.invoke(prepare_cwd_recovery_cmd, obj=ctx)
    finally:
        os.chdir(original_cwd)

    assert result.exit_code == 0
    script_path = Path(result.output.strip())
    assert script_path.exists()
    script_path.unlink(missing_ok=True)


def test_prepare_cwd_recovery_no_repo(tmp_path: Path) -> None:
    """Command should emit nothing outside a repository."""
    workstacks_root = tmp_path / "workstacks"
    workstacks_root.mkdir()

    ctx = build_ctx(None, workstacks_root)

    runner = CliRunner()

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = runner.invoke(prepare_cwd_recovery_cmd, obj=ctx)
    finally:
        os.chdir(original_cwd)

    assert result.exit_code == 0
    assert result.output == ""


def test_prepare_cwd_recovery_missing_cwd(tmp_path: Path) -> None:
    """Command should handle missing cwd gracefully."""
    ctx = build_ctx(None, tmp_path)

    broken_dir = tmp_path / "vanish"
    broken_dir.mkdir()

    runner = CliRunner()

    original_cwd = os.getcwd()
    try:
        os.chdir(broken_dir)
        broken_dir.rmdir()
        result = runner.invoke(prepare_cwd_recovery_cmd, obj=ctx)
    finally:
        os.chdir(original_cwd)

    assert result.exit_code == 0
    assert result.output == ""
