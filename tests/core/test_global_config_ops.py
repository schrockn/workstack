"""Tests for FakeGlobalConfigOps."""

from pathlib import Path

import pytest

from tests.fakes.global_config_ops import FakeGlobalConfigOps


def test_global_config_ops_get_workstacks_root() -> None:
    """Test getting workstacks_root."""
    ops = FakeGlobalConfigOps(workstacks_root=Path("/tmp/ws"))
    assert ops.get_workstacks_root() == Path("/tmp/ws")


def test_global_config_ops_get_use_graphite() -> None:
    """Test getting use_graphite setting."""
    ops = FakeGlobalConfigOps(use_graphite=True, workstacks_root=Path("/tmp"))
    assert ops.get_use_graphite() is True


def test_global_config_ops_get_show_pr_info() -> None:
    """Test getting show_pr_info setting."""
    ops = FakeGlobalConfigOps(show_pr_info=False, workstacks_root=Path("/tmp"))
    assert ops.get_show_pr_info() is False


def test_global_config_ops_get_show_pr_checks() -> None:
    """Test getting show_pr_checks setting."""
    ops = FakeGlobalConfigOps(show_pr_checks=True, workstacks_root=Path("/tmp"))
    assert ops.get_show_pr_checks() is True


def test_global_config_ops_get_shell_setup_complete() -> None:
    """Test getting shell_setup_complete setting."""
    ops = FakeGlobalConfigOps(shell_setup_complete=True, workstacks_root=Path("/tmp"))
    assert ops.get_shell_setup_complete() is True


def test_global_config_ops_set_updates_config() -> None:
    """Test that set() updates config values."""
    ops = FakeGlobalConfigOps(workstacks_root=Path("/tmp"), use_graphite=False)

    ops.set(use_graphite=True)

    assert ops.get_use_graphite() is True


def test_global_config_ops_exists() -> None:
    """Test config existence check."""
    ops = FakeGlobalConfigOps(exists=True, workstacks_root=Path("/tmp"))
    assert ops.exists() is True

    ops2 = FakeGlobalConfigOps(exists=False)
    assert ops2.exists() is False


def test_global_config_ops_get_path() -> None:
    """Test getting config path."""
    ops = FakeGlobalConfigOps(workstacks_root=Path("/tmp"), config_path=Path("/test/config.toml"))
    assert ops.get_path() == Path("/test/config.toml")


def test_global_config_ops_missing_file_raises() -> None:
    """Test that accessing non-existent config raises."""
    ops = FakeGlobalConfigOps(exists=False)

    with pytest.raises(FileNotFoundError):
        ops.get_workstacks_root()


def test_global_config_ops_set_creates_config() -> None:
    """Test that set() creates config if it doesn't exist."""
    ops = FakeGlobalConfigOps(exists=False)

    ops.set(workstacks_root=Path("/new/ws"))

    assert ops.exists()
    assert ops.get_workstacks_root() == Path("/new/ws")


def test_fake_global_config_ops_constructor_state() -> None:
    """Test FakeGlobalConfigOps accepts all parameters."""
    ops = FakeGlobalConfigOps(
        workstacks_root=Path("/ws"),
        use_graphite=True,
        shell_setup_complete=True,
        show_pr_info=False,
        show_pr_checks=True,
        exists=True,
        config_path=Path("/cfg.toml"),
    )

    assert ops.get_workstacks_root() == Path("/ws")
    assert ops.get_use_graphite() is True
    assert ops.get_shell_setup_complete() is True
    assert ops.get_show_pr_info() is False
    assert ops.get_show_pr_checks() is True
    assert ops.exists()
    assert ops.get_path() == Path("/cfg.toml")


def test_fake_global_config_ops_set_updates_state() -> None:
    """Test that set() properly updates all fields."""
    ops = FakeGlobalConfigOps(workstacks_root=Path("/tmp"), use_graphite=False)

    ops.set(
        workstacks_root=Path("/new"),
        use_graphite=True,
        shell_setup_complete=True,
        show_pr_info=False,
        show_pr_checks=True,
    )

    assert ops.get_workstacks_root() == Path("/new")
    assert ops.get_use_graphite() is True
    assert ops.get_shell_setup_complete() is True
    assert ops.get_show_pr_info() is False
    assert ops.get_show_pr_checks() is True
