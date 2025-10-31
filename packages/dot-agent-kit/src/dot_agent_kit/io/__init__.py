"""I/O operations for dot-agent-kit."""

from dot_agent_kit.io.discovery import (
    discover_all_artifacts,
    discover_installed_artifacts,
)
from dot_agent_kit.io.frontmatter import (
    add_frontmatter,
    parse_frontmatter,
    validate_frontmatter,
)
from dot_agent_kit.io.manifest import load_kit_manifest
from dot_agent_kit.io.registry import load_registry
from dot_agent_kit.io.state import (
    create_default_config,
    load_project_config,
    save_project_config,
)
from dot_agent_kit.io.user_config import (
    create_default_user_config,
    get_user_claude_dir,
    get_user_config_path,
    load_user_config,
    save_user_config,
)

__all__ = [
    "add_frontmatter",
    "create_default_config",
    "create_default_user_config",
    "discover_all_artifacts",
    "discover_installed_artifacts",
    "get_user_claude_dir",
    "get_user_config_path",
    "load_kit_manifest",
    "load_project_config",
    "load_registry",
    "load_user_config",
    "parse_frontmatter",
    "save_project_config",
    "save_user_config",
    "validate_frontmatter",
]
