from __future__ import annotations

import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path

GLOBAL_CONFIG_PATH = Path.home() / ".workstack" / "config.toml"


def detect_graphite() -> bool:
    """Detect if Graphite (gt) is installed and available in PATH."""
    return shutil.which("gt") is not None


@dataclass(frozen=True)
class GlobalConfig:
    """Global workstack configuration."""

    workstacks_root: Path
    use_graphite: bool


def load_global_config() -> GlobalConfig:
    """Load global config from ~/.workstack/config.toml.

    Raises FileNotFoundError if the config doesn't exist.
    """
    if not GLOBAL_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Global config not found at {GLOBAL_CONFIG_PATH}")

    data = tomllib.loads(GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))
    root = data.get("workstacks_root")
    if not root:
        raise ValueError(f"Missing 'workstacks_root' in {GLOBAL_CONFIG_PATH}")

    # Default to False for backward compatibility with existing configs
    use_graphite = data.get("use_graphite", False)

    return GlobalConfig(
        workstacks_root=Path(root).expanduser().resolve(),
        use_graphite=bool(use_graphite),
    )


def create_global_config(workstacks_root: Path) -> None:
    """Create global config at ~/.workstack/config.toml."""
    GLOBAL_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    use_graphite = detect_graphite()
    content = f"""# Global workstack configuration
workstacks_root = "{workstacks_root}"
use_graphite = {str(use_graphite).lower()}
"""
    GLOBAL_CONFIG_PATH.write_text(content, encoding="utf-8")


@dataclass(frozen=True)
class LoadedConfig:
    """In-memory representation of `.workstack/config.toml`."""

    env: dict[str, str]
    post_create_commands: list[str]
    post_create_shell: str | None


def load_config(config_dir: Path) -> LoadedConfig:
    """Load config.toml from the given directory if present; otherwise return defaults.

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

    cfg_path = config_dir / "config.toml"
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


def render_config_template(preset: str | None = None) -> str:
    """Return default config TOML content, optionally using a preset.

    Presets:
      - "dagster": sets DAGSTER_GIT_REPO_DIR and sensible post-create commands.
    """

    header = """# work config for this repository
# Available template variables: {worktree_path}, {repo_root}, {name}
"""

    if preset == "dagster":
        body = """
[env]
DAGSTER_GIT_REPO_DIR = "{worktree_path}"

[post_create]
shell = "bash"
commands = [
  "uv venv",
  "uv run make dev_install",
]
"""
    else:
        body = """
[env]
# EXAMPLE_KEY = "{worktree_path}"

[post_create]
# shell = "bash"
# commands = [
#   "uv venv",
#   "uv run make dev_install",
# ]
"""

    return header + "\n" + body.lstrip("\n")
