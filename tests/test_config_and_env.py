from pathlib import Path
from unittest import mock

import pytest

from workstack.commands.create import make_env_content
from workstack.commands.init import create_global_config, discover_presets
from workstack.config import load_config, load_global_config


def test_load_config_defaults(tmp_path: Path) -> None:
    cfg = load_config(tmp_path)
    assert cfg.env == {}
    assert cfg.post_create_commands == []
    assert cfg.post_create_shell is None


def test_env_rendering(tmp_path: Path) -> None:
    # Write a config
    config_dir = tmp_path / "config_dir"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        """
        [env]
        DAGSTER_GIT_REPO_DIR = "{worktree_path}"
        CUSTOM_NAME = "{name}"

        [post_create]
        shell = "bash"
        commands = ["echo hi"]
        """.strip()
    )

    cfg = load_config(config_dir)
    wt_path = tmp_path / "worktrees" / "foo"
    repo_root = tmp_path
    content = make_env_content(cfg, worktree_path=wt_path, repo_root=repo_root, name="foo")

    assert 'DAGSTER_GIT_REPO_DIR="' + str(wt_path) + '"' in content
    assert 'CUSTOM_NAME="foo"' in content
    assert 'WORKTREE_PATH="' + str(wt_path) + '"' in content
    assert 'REPO_ROOT="' + str(repo_root) + '"' in content
    assert 'WORKTREE_NAME="foo"' in content


def test_load_global_config_valid(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    workstacks_root = tmp_path / "workstacks"
    config_file.write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = true\n', encoding="utf-8"
    )

    with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", config_file):
        cfg = load_global_config()
        assert cfg.workstacks_root == workstacks_root.resolve()
        assert cfg.use_graphite is True


def test_load_global_config_missing_file(tmp_path: Path) -> None:
    config_file = tmp_path / "nonexistent.toml"

    with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", config_file):
        with pytest.raises(FileNotFoundError, match="Global config not found"):
            load_global_config()


def test_load_global_config_missing_workstacks_root(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text("use_graphite = true\n", encoding="utf-8")

    with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", config_file):
        with pytest.raises(ValueError, match="Missing 'workstacks_root'"):
            load_global_config()


def test_load_global_config_use_graphite_defaults_false(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    workstacks_root = tmp_path / "workstacks"
    config_file.write_text(f'workstacks_root = "{workstacks_root}"\n', encoding="utf-8")

    with mock.patch("workstack.config.GLOBAL_CONFIG_PATH", config_file):
        cfg = load_global_config()
        assert cfg.workstacks_root == workstacks_root.resolve()
        assert cfg.use_graphite is False


def test_create_global_config_creates_file(tmp_path: Path) -> None:
    config_file = tmp_path / ".workstack" / "config.toml"

    with mock.patch("workstack.commands.init.GLOBAL_CONFIG_PATH", config_file):
        with mock.patch("workstack.commands.init.detect_graphite", return_value=False):
            create_global_config(Path("/tmp/workstacks"))

    assert config_file.exists()
    content = config_file.read_text(encoding="utf-8")
    assert 'workstacks_root = "/tmp/workstacks"' in content
    assert "use_graphite = false" in content


def test_create_global_config_creates_parent_directory(tmp_path: Path) -> None:
    config_file = tmp_path / ".workstack" / "config.toml"
    assert not config_file.parent.exists()

    with mock.patch("workstack.commands.init.GLOBAL_CONFIG_PATH", config_file):
        with mock.patch("workstack.commands.init.detect_graphite", return_value=False):
            create_global_config(Path("/tmp/workstacks"))

    assert config_file.parent.exists()
    assert config_file.exists()


def test_create_global_config_detects_graphite(tmp_path: Path) -> None:
    config_file = tmp_path / ".workstack" / "config.toml"

    with mock.patch("workstack.commands.init.GLOBAL_CONFIG_PATH", config_file):
        with mock.patch("workstack.commands.init.detect_graphite", return_value=True):
            create_global_config(Path("/tmp/workstacks"))

    content = config_file.read_text(encoding="utf-8")
    assert "use_graphite = true" in content


def test_discover_presets(tmp_path: Path) -> None:
    # Create structure: tmp_path/commands/init.py (mocked) and tmp_path/presets/*.toml
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()
    presets_dir = tmp_path / "presets"
    presets_dir.mkdir()
    (presets_dir / "generic.toml").write_text("# generic preset\n", encoding="utf-8")
    (presets_dir / "dagster.toml").write_text("# dagster preset\n", encoding="utf-8")
    (presets_dir / "custom.toml").write_text("# custom preset\n", encoding="utf-8")
    (presets_dir / "README.md").write_text("# readme\n", encoding="utf-8")
    (presets_dir / "subdir").mkdir()

    with mock.patch("workstack.commands.init.__file__", str(commands_dir / "init.py")):
        presets = discover_presets()

    assert presets == ["custom", "dagster", "generic"]


def test_discover_presets_missing_directory(tmp_path: Path) -> None:
    # Create structure: tmp_path/commands/init.py (mocked) but no presets directory
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    with mock.patch("workstack.commands.init.__file__", str(commands_dir / "init.py")):
        presets = discover_presets()

    assert presets == []


def test_load_config_with_post_create_commands(tmp_path: Path) -> None:
    config_dir = tmp_path / "config_dir"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        """
        [env]
        FOO = "bar"

        [post_create]
        shell = "bash"
        commands = [
            "uv venv",
            "uv run make dev_install",
            "echo 'setup complete'"
        ]
        """.strip(),
        encoding="utf-8",
    )

    cfg = load_config(config_dir)
    assert cfg.env == {"FOO": "bar"}
    assert cfg.post_create_shell == "bash"
    assert cfg.post_create_commands == [
        "uv venv",
        "uv run make dev_install",
        "echo 'setup complete'",
    ]


def test_load_config_with_partial_post_create(tmp_path: Path) -> None:
    config_dir = tmp_path / "config_dir"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        """
        [post_create]
        commands = ["echo 'hello'"]
        """.strip(),
        encoding="utf-8",
    )

    cfg = load_config(config_dir)
    assert cfg.env == {}
    assert cfg.post_create_shell is None
    assert cfg.post_create_commands == ["echo 'hello'"]
