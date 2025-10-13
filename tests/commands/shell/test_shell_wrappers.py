"""Integration-style tests for bash/zsh/fish wrappers."""

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER_DIR = REPO_ROOT / "src" / "workstack" / "cli" / "shell_integration"


STUB_WORKSTACK_SCRIPT = """#!/usr/bin/env bash
set -e

cmd="$1"
shift || true

case "$cmd" in
  "__shell")
    shell="${WORKSTACK_SHELL:-bash}"
    script_path="$WORKSTACK_TEST_SCRIPT"
    mkdir -p "$(dirname "$script_path")"
    if [ "$shell" = "fish" ]; then
      cat <<'FISH' >"$script_path"
command workstack sync
set __workstack_exit $status
if not test -d "$PWD"
    cd "$WORKSTACK_TEST_TARGET"
end
return $__workstack_exit
FISH
    else
      cat <<'POSIX' >"$script_path"
command workstack sync
__workstack_exit=$?
if [ ! -d "$PWD" ]; then
  cd "$WORKSTACK_TEST_TARGET"
fi
return $__workstack_exit
POSIX
    fi
    chmod +x "$script_path"
    printf %s "$script_path"
    exit 0
    ;;
  "sync")
    rm -rf "$PWD"
    exit "${WORKSTACK_TEST_EXIT_CODE:-0}"
    ;;
esac

exit 0
"""


def _prepare_environment(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, str]]:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    worktree = repo_root / "feature"
    worktree.mkdir()

    passthrough_script = tmp_path / "passthrough.sh"

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub_path = bin_dir / "workstack"
    stub_path.write_text(STUB_WORKSTACK_SCRIPT, encoding="utf-8")
    stub_path.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    env["HOME"] = str(tmp_path)
    env["ZDOTDIR"] = str(tmp_path)
    env["XDG_CONFIG_HOME"] = str(tmp_path)
    env["WORKSTACK_TEST_TARGET"] = str(repo_root)
    env["WORKSTACK_TEST_EXIT_CODE"] = "19"
    env["WORKSTACK_TEST_SCRIPT"] = str(passthrough_script)

    return repo_root, worktree, passthrough_script, env


@pytest.mark.parametrize(
    ("shell", "wrapper_name", "command_template", "extra_args"),
    [
        (
            "bash",
            "bash_wrapper.sh",
            textwrap.dedent(
                """
                source "{wrapper}"
                workstack sync
                rc=$?
                pwd
                echo EXIT:$rc
                exit $rc
                """
            ),
            ["--noprofile", "--norc"],
        ),
        (
            "zsh",
            "zsh_wrapper.sh",
            textwrap.dedent(
                """
                source "{wrapper}"
                workstack sync
                rc=$?
                pwd
                echo EXIT:$rc
                exit $rc
                """
            ),
            ["-f"],
        ),
        (
            "fish",
            "fish_wrapper.fish",
            textwrap.dedent(
                """
                source "{wrapper}"
                workstack sync
                set rc $status
                pwd
                printf "EXIT:%s\\n" $rc
                exit $rc
                """
            ),
            [],
        ),
    ],
)
def test_shell_wrapper_recovers_deleted_directory(
    shell: str, wrapper_name: str, command_template: str, extra_args: list[str], tmp_path: Path
) -> None:
    """Each shell wrapper should recover when the worktree directory vanishes."""
    if shutil.which(shell) is None:
        pytest.skip(f"{shell} is not available on this system")

    repo_root, worktree, passthrough_script, env = _prepare_environment(tmp_path)
    wrapper_path = WRAPPER_DIR / wrapper_name

    command = command_template.format(wrapper=wrapper_path)

    args = [shell, *extra_args, "-c", command]

    result = subprocess.run(
        args,
        cwd=worktree,
        env=env,
        capture_output=True,
        text=True,
    )

    # Shell exits with the passthrough command's exit code
    assert result.returncode == 19

    stdout_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert len(stdout_lines) >= 2
    assert stdout_lines[-2] == str(repo_root)
    assert stdout_lines[-1] == "EXIT:19"

    # The recovery script should be cleaned up when not needed anymore
    assert not passthrough_script.exists()
