import tomllib
from dataclasses import dataclass
from pathlib import Path

GLOBAL_CONFIG_PATH = Path.home() / ".workstack" / "config.toml"


@dataclass(frozen=True)
class GlobalConfig:
    """Global workstack configuration."""

    workstacks_root: Path
    use_graphite: bool
    shell_setup_complete: bool


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
    shell_setup_complete = data.get("shell_setup_complete", False)

    return GlobalConfig(
        workstacks_root=Path(root).expanduser().resolve(),
        use_graphite=bool(use_graphite),
        shell_setup_complete=bool(shell_setup_complete),
    )


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
