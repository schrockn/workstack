import re
import shutil
import tomllib
from pathlib import Path

import click

from ..config import GLOBAL_CONFIG_PATH
from ..core import discover_repo_context, ensure_work_dir


def detect_root_project_name(repo_root: Path) -> str | None:
    """Return the declared project name at the repo root, if any.

    Checks root `pyproject.toml`'s `[project].name`. If absent, tries to heuristically
    extract from `setup.py` by matching `name="..."` or `name='...'`.
    """

    root_pyproject = repo_root / "pyproject.toml"
    if root_pyproject.exists():
        data = tomllib.loads(root_pyproject.read_text(encoding="utf-8"))
        project = data.get("project") or {}
        name = project.get("name")
        if isinstance(name, str) and name:
            return name

    setup_py = repo_root / "setup.py"
    if setup_py.exists():
        text = setup_py.read_text(encoding="utf-8")
        m = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", text)
        if m:
            return m.group(1)

    return None


def is_repo_named(repo_root: Path, expected_name: str) -> bool:
    """Return True if the root project name matches `expected_name` (case-insensitive)."""
    name = detect_root_project_name(repo_root)
    return (name or "").lower() == expected_name.lower()


def detect_graphite() -> bool:
    """Detect if Graphite (gt) is installed and available in PATH."""
    return shutil.which("gt") is not None


def create_global_config(workstacks_root: Path) -> None:
    """Create global config at ~/.workstack/config.toml."""
    GLOBAL_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    use_graphite = detect_graphite()
    content = f"""# Global workstack configuration
workstacks_root = "{workstacks_root}"
use_graphite = {str(use_graphite).lower()}
"""
    GLOBAL_CONFIG_PATH.write_text(content, encoding="utf-8")


def discover_presets() -> list[str]:
    """Discover available preset names by scanning the presets directory.

    Returns a list of preset names (without .toml extension).
    """
    presets_dir = Path(__file__).parent.parent / "presets"
    if not presets_dir.exists():
        return []

    return sorted(p.stem for p in presets_dir.glob("*.toml") if p.is_file())


def render_config_template(preset: str | None = None) -> str:
    """Return default config TOML content, optionally using a preset.

    If preset is None, uses the "generic" preset by default.
    Preset files are loaded from src/workstack/presets/<preset>.toml
    """
    preset_name = preset if preset is not None else "generic"
    presets_dir = Path(__file__).parent.parent / "presets"
    preset_file = presets_dir / f"{preset_name}.toml"

    if not preset_file.exists():
        raise ValueError(f"Preset '{preset_name}' not found at {preset_file}")

    return preset_file.read_text(encoding="utf-8")


@click.command("init")
@click.option("--force", is_flag=True, help="Overwrite existing repo config if present.")
@click.option(
    "--preset",
    type=str,
    default="auto",
    help=(
        "Config template to use. 'auto' detects preset based on repo characteristics. "
        f"Available: auto, {', '.join(discover_presets())}."
    ),
)
@click.option(
    "--list-presets",
    is_flag=True,
    help="List available presets and exit.",
)
@click.option(
    "--repo",
    is_flag=True,
    help="Initialize repository-level config only (skip global config setup).",
)
def init_cmd(force: bool, preset: str, list_presets: bool, repo: bool) -> None:
    """Initialize workstack for this repo and scaffold config.toml."""

    # Discover available presets on demand
    available_presets = discover_presets()
    valid_choices = ["auto"] + available_presets

    # Handle --list-presets flag
    if list_presets:
        click.echo("Available presets:")
        for p in available_presets:
            click.echo(f"  - {p}")
        return

    # Validate preset choice
    if preset not in valid_choices:
        click.echo(f"Invalid preset '{preset}'. Available options: {', '.join(valid_choices)}")
        raise SystemExit(1)

    # Check for global config first (unless --repo flag is set)
    if not repo and not GLOBAL_CONFIG_PATH.exists():
        click.echo(f"Global config not found at {GLOBAL_CONFIG_PATH}")
        click.echo("Please provide the path where you want to store all worktrees.")
        click.echo("(This directory will contain subdirectories for each repository)")
        workstacks_root = click.prompt("Worktrees root directory", type=Path)
        workstacks_root = workstacks_root.expanduser().resolve()
        create_global_config(workstacks_root)
        click.echo(f"Created global config at {GLOBAL_CONFIG_PATH}")
        # Show graphite status on first init
        has_graphite = detect_graphite()
        if has_graphite:
            click.echo("Graphite (gt) detected - will use 'gt create' for new branches")
        else:
            click.echo("Graphite (gt) not detected - will use 'git' for branch creation")

    # When --repo is set, verify that global config exists
    if repo and not GLOBAL_CONFIG_PATH.exists():
        click.echo(f"Global config not found at {GLOBAL_CONFIG_PATH}", err=True)
        click.echo("Run 'workstack init' without --repo to create global config first.", err=True)
        raise SystemExit(1)

    # Now proceed with repo-specific setup
    repo_context = discover_repo_context(Path.cwd())

    # Determine config path based on --repo flag
    if repo:
        # Repository-level config goes in repo root
        cfg_path = repo_context.root / "config.toml"
    else:
        # Worktree-level config goes in work_dir
        work_dir = ensure_work_dir(repo_context)
        cfg_path = work_dir / "config.toml"

    if cfg_path.exists() and not force:
        click.echo(f"Config already exists: {cfg_path}. Use --force to overwrite.")
        raise SystemExit(1)

    effective_preset: str | None
    choice = preset.lower()
    if choice == "auto":
        effective_preset = "dagster" if is_repo_named(repo_context.root, "dagster") else "generic"
    else:
        effective_preset = choice

    content = render_config_template(effective_preset)
    cfg_path.write_text(content, encoding="utf-8")
    click.echo(f"Wrote {cfg_path}")

    # Check for .gitignore and add .PLAN.md
    gitignore_path = repo_context.root / ".gitignore"
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text(encoding="utf-8")

        if ".PLAN.md" not in gitignore_content:
            if click.confirm(
                "Add .PLAN.md to .gitignore?",
                default=True,
            ):
                if not gitignore_content.endswith("\n"):
                    gitignore_content += "\n"
                gitignore_content += ".PLAN.md\n"
                gitignore_path.write_text(gitignore_content, encoding="utf-8")
                click.echo(f"Added .PLAN.md to {gitignore_path}")
