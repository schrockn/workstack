from __future__ import annotations

from pathlib import Path

from workstack.config import load_config
from workstack.core import make_env_content


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
