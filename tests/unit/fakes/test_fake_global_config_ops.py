"""Consolidated tests for FakeGlobalConfigOps."""

from pathlib import Path

import pytest

from tests.fakes.global_config_ops import FakeGlobalConfigOps


def test_fake_global_config_ops_initial_state() -> None:
    """All getters reflect the constructor-provided state."""
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
    assert ops.exists() is True
    assert ops.get_path() == Path("/cfg.toml")


def test_fake_global_config_ops_set_updates_all_fields() -> None:
    """set() should update all tracked configuration values."""
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


@pytest.mark.parametrize(
    "exists_flag",
    [True, False],
    ids=["exists", "missing"],
)
def test_fake_global_config_ops_exists_flag(exists_flag: bool) -> None:
    """exists() exposes whether the fake config file should be considered present."""
    ops = FakeGlobalConfigOps(exists=exists_flag)
    assert ops.exists() is exists_flag


def test_fake_global_config_ops_missing_file_raises() -> None:
    """Attempting to read paths when the file is absent raises FileNotFoundError."""
    ops = FakeGlobalConfigOps(exists=False)

    with pytest.raises(FileNotFoundError):
        ops.get_workstacks_root()


def test_fake_global_config_ops_set_creates_config() -> None:
    """Calling set() when the config is missing marks it as created."""
    ops = FakeGlobalConfigOps(exists=False)

    ops.set(workstacks_root=Path("/new/ws"))

    assert ops.exists() is True
    assert ops.get_workstacks_root() == Path("/new/ws")
