import subprocess
from pathlib import Path
from unittest import mock

import pytest

from workstack.git import detect_default_branch


def test_detect_default_branch_uses_remote_head_master() -> None:
    """When remote HEAD points to master, should return master even if main exists."""
    repo_root = Path("/fake/repo")

    def mock_run(cmd: list[str], *args: object, **kwargs: object) -> mock.Mock:
        if cmd == ["git", "symbolic-ref", "refs/remotes/origin/HEAD"]:
            result = mock.Mock()
            result.returncode = 0
            result.stdout = "refs/remotes/origin/master\n"
            return result
        # Should not reach the fallback checks
        raise AssertionError(f"Unexpected command: {cmd}")

    with mock.patch("workstack.git.subprocess.run", side_effect=mock_run):
        assert detect_default_branch(repo_root) == "master"


def test_detect_default_branch_uses_remote_head_main() -> None:
    """When remote HEAD points to main, should return main even if master exists."""
    repo_root = Path("/fake/repo")

    def mock_run(cmd: list[str], *args: object, **kwargs: object) -> mock.Mock:
        if cmd == ["git", "symbolic-ref", "refs/remotes/origin/HEAD"]:
            result = mock.Mock()
            result.returncode = 0
            result.stdout = "refs/remotes/origin/main\n"
            return result
        # Should not reach the fallback checks
        raise AssertionError(f"Unexpected command: {cmd}")

    with mock.patch("workstack.git.subprocess.run", side_effect=mock_run):
        assert detect_default_branch(repo_root) == "main"


def test_detect_default_branch_fallback_to_main() -> None:
    """When no remote HEAD, falls back to checking if main exists."""
    repo_root = Path("/fake/repo")

    def mock_run(cmd: list[str], *args: object, **kwargs: object) -> mock.Mock:
        if cmd == ["git", "symbolic-ref", "refs/remotes/origin/HEAD"]:
            result = mock.Mock()
            result.returncode = 1  # No remote HEAD
            return result
        if cmd == ["git", "rev-parse", "--verify", "main"]:
            result = mock.Mock()
            result.returncode = 0
            return result
        raise AssertionError(f"Unexpected command: {cmd}")

    with mock.patch("workstack.git.subprocess.run", side_effect=mock_run):
        assert detect_default_branch(repo_root) == "main"


def test_detect_default_branch_fallback_to_master() -> None:
    """When no remote HEAD and no main, falls back to checking if master exists."""
    repo_root = Path("/fake/repo")

    def mock_run(cmd: list[str], *args: object, **kwargs: object) -> mock.Mock:
        if cmd == ["git", "symbolic-ref", "refs/remotes/origin/HEAD"]:
            result = mock.Mock()
            result.returncode = 1  # No remote HEAD
            return result
        if cmd == ["git", "rev-parse", "--verify", "main"]:
            result = mock.Mock()
            result.returncode = 1  # main doesn't exist
            return result
        if cmd == ["git", "rev-parse", "--verify", "master"]:
            result = mock.Mock()
            result.returncode = 0
            return result
        raise AssertionError(f"Unexpected command: {cmd}")

    with mock.patch("workstack.git.subprocess.run", side_effect=mock_run):
        assert detect_default_branch(repo_root) == "master"


def test_detect_default_branch_neither_exists() -> None:
    """When neither main nor master exist, should raise SystemExit."""
    repo_root = Path("/fake/repo")

    def mock_run(cmd: list[str], *args: object, **kwargs: object) -> mock.Mock:
        result = mock.Mock()
        result.returncode = 1
        result.stdout = ""
        return result

    with mock.patch("workstack.git.subprocess.run", side_effect=mock_run):
        with pytest.raises(SystemExit):
            detect_default_branch(repo_root)
