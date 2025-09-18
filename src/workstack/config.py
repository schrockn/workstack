from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import tomllib


@dataclass(frozen=True)
class LoadedConfig:
    """In-memory representation of `.workstack/config.toml`."""

    env: Dict[str, str]
    post_create_commands: List[str]
    post_create_shell: Optional[str]


def load_config(repo_root: Path) -> LoadedConfig:
    """Load `.workstack/config.toml` if present; otherwise return defaults.

    Example config:
      [env]
      DAGSTER_GIT_REPO_DIR = "{worktree_path}"

      [post_create]
      shell = "bash"
      commands = [
        "uv venv",
        "uv run make dev_install",
      ]
    """

    cfg_path = repo_root / ".workstack" / "config.toml"
    if not cfg_path.exists():
        return LoadedConfig(env={}, post_create_commands=[], post_create_shell=None)

    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    env = {str(k): str(v) for k, v in data.get("env", {}).items()}
    post = data.get("post_create", {})
    commands = [str(x) for x in post.get("commands", [])]
    shell = post.get("shell")
    if shell is not None:
        shell = str(shell)
    return LoadedConfig(env=env, post_create_commands=commands, post_create_shell=shell)


def render_config_template(preset: Optional[str] = None) -> str:
    """Return default config TOML content, optionally using a preset.

    Presets:
      - "dagster": sets DAGSTER_GIT_REPO_DIR and sensible post-create commands.
    """

    header = f"""# work config for this repository
# Available template variables: {{worktree_path}}, {{repo_root}}, {{name}}
"""

    if preset == "dagster":
        body = f"""
[env]
DAGSTER_GIT_REPO_DIR = "{{worktree_path}}"

[post_create]
shell = "bash"
commands = [
  "uv venv",
  "uv run make dev_install",
]
"""
    else:
        body = f"""
[env]
# EXAMPLE_KEY = "{{worktree_path}}"

[post_create]
# shell = "bash"
# commands = [
#   "uv venv",
#   "uv run make dev_install",
# ]
"""

    return header + "\n" + body.lstrip("\n")
