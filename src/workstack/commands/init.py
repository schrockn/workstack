import os
import re
import shutil
import tomllib
from pathlib import Path

import click

from workstack.context import WorkstackContext
from workstack.core import discover_repo_context, ensure_work_dir
from workstack.global_config_ops import GlobalConfigOps


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


def create_global_config(
    global_config_ops: GlobalConfigOps,
    workstacks_root: Path,
    shell_setup_complete: bool,
) -> None:
    """Create global config using the provided config ops."""
    use_graphite = detect_graphite()
    global_config_ops.set(
        workstacks_root=workstacks_root,
        use_graphite=use_graphite,
        shell_setup_complete=shell_setup_complete,
    )


def discover_presets() -> list[str]:
    """Discover available preset names by scanning the presets directory.

    Returns a list of preset names (without .toml extension).
    """
    presets_dir = Path(__file__).parent.parent / "presets"
    if not presets_dir.exists():
        return []

    return sorted(p.stem for p in presets_dir.glob("*.toml") if p.is_file())


def render_config_template(preset: str | None) -> str:
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


def _add_gitignore_entry(content: str, entry: str, prompt_message: str) -> tuple[str, bool]:
    """Add an entry to gitignore content if not present and user confirms.

    Args:
        content: Current gitignore content
        entry: Entry to add (e.g., ".PLAN.md")
        prompt_message: Message to show user when confirming

    Returns:
        Tuple of (updated_content, was_modified)
    """
    # Entry already present
    if entry in content:
        return (content, False)

    # User declined
    if not click.confirm(prompt_message, default=True):
        return (content, False)

    # Ensure trailing newline before adding
    if not content.endswith("\n"):
        content += "\n"

    content += f"{entry}\n"
    return (content, True)


def detect_shell() -> tuple[str, Path] | None:
    """Detect current shell and return (shell_name, rc_file_path).

    Returns None if shell cannot be detected or is unsupported.
    """
    shell_path = os.environ.get("SHELL", "")
    if not shell_path:
        return None

    shell_name = Path(shell_path).name

    if shell_name == "bash":
        rc_file = Path.home() / ".bashrc"
        return ("bash", rc_file)
    if shell_name == "zsh":
        rc_file = Path.home() / ".zshrc"
        return ("zsh", rc_file)
    if shell_name == "fish":
        rc_file = Path.home() / ".config" / "fish" / "config.fish"
        return ("fish", rc_file)

    return None


def get_shell_wrapper_content(shell: str) -> str:
    """Load the shell wrapper function for the given shell type."""
    shell_integration_dir = Path(__file__).parent.parent / "shell_integration"

    if shell == "fish":
        wrapper_file = shell_integration_dir / "fish_wrapper.fish"
    else:
        wrapper_file = shell_integration_dir / f"{shell}_wrapper.sh"

    if not wrapper_file.exists():
        raise ValueError(f"Shell wrapper not found for {shell}")

    return wrapper_file.read_text(encoding="utf-8")


def perform_shell_setup() -> bool:
    """Interactively set up shell integration (completion + wrapper function).

    Returns True if setup was completed, False if skipped.
    """
    shell_info = detect_shell()
    if not shell_info:
        click.echo("Unable to detect shell. Skipping shell integration setup.")
        return False

    shell, rc_file = shell_info

    click.echo(f"\nDetected shell: {shell}")
    click.echo("Shell integration provides:")
    click.echo("  - Tab completion for workstack commands")
    click.echo("  - Automatic worktree activation on 'workstack switch'")

    if not click.confirm("\nSet up shell integration?", default=True):
        click.echo("Skipping shell integration. You can run 'workstack init --shell' later.")
        return False

    # Step 1: Completion setup
    click.echo(f"\n1. Setting up tab completion for {shell}...")
    completion_line = f"source <(workstack completion {shell})"

    if rc_file.exists():
        rc_content = rc_file.read_text(encoding="utf-8")
        if completion_line in rc_content:
            click.echo(f"   ✓ Completion already configured in {rc_file}")
        else:
            if click.confirm(f"   Add completion to {rc_file}?", default=True):
                rc_file.write_text(
                    rc_content + f"\n# Workstack completion\n{completion_line}\n", encoding="utf-8"
                )
                click.echo(f"   ✓ Added completion to {rc_file}")
            else:
                click.echo(f"   To set up manually, add to {rc_file}:")
                click.echo(f"   {completion_line}")
    else:
        click.echo(f"   {rc_file} not found. To set up manually, add:")
        click.echo(f"   {completion_line}")

    # Step 2: Shell wrapper function
    click.echo(f"\n2. Setting up auto-activation wrapper for {shell}...")
    wrapper_content = get_shell_wrapper_content(shell)

    if rc_file.exists():
        rc_content = rc_file.read_text(encoding="utf-8")
        if "workstack shell integration" in rc_content.lower():
            click.echo(f"   ✓ Wrapper already configured in {rc_file}")
        else:
            if click.confirm(f"   Add wrapper function to {rc_file}?", default=True):
                rc_file.write_text(rc_content + f"\n{wrapper_content}\n", encoding="utf-8")
                click.echo(f"   ✓ Added wrapper to {rc_file}")
            else:
                click.echo(f"   To set up manually, add to {rc_file}:")
                click.echo(f"\n{wrapper_content}")
    else:
        rc_file.parent.mkdir(parents=True, exist_ok=True)
        if click.confirm(f"   Create {rc_file} with wrapper function?", default=True):
            rc_file.write_text(f"{wrapper_content}\n", encoding="utf-8")
            click.echo(f"   ✓ Created {rc_file} with wrapper")
        else:
            click.echo(f"   To set up manually, create {rc_file} with:")
            click.echo(f"\n{wrapper_content}")

    click.echo("\n✓ Shell integration setup complete!")
    click.echo(f"Run 'source {rc_file}' or start a new shell to activate.")

    return True


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
@click.option(
    "--shell",
    is_flag=True,
    help="Set up shell integration only (completion + auto-activation wrapper).",
)
@click.pass_obj
def init_cmd(
    ctx: WorkstackContext, force: bool, preset: str, list_presets: bool, repo: bool, shell: bool
) -> None:
    """Initialize workstack for this repo and scaffold config.toml."""

    # Handle --shell flag: only do shell setup
    if shell:
        setup_complete = perform_shell_setup()
        if setup_complete:
            ctx.global_config_ops.set(shell_setup_complete=True)
        return

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

    # Track if this is the first time init is run
    first_time_init = False

    # Check for global config first (unless --repo flag is set)
    if not repo and not ctx.global_config_ops.exists():
        first_time_init = True
        click.echo(f"Global config not found at {ctx.global_config_ops.get_path()}")
        click.echo("Please provide the path where you want to store all worktrees.")
        click.echo("(This directory will contain subdirectories for each repository)")
        workstacks_root = click.prompt("Worktrees root directory", type=Path)
        workstacks_root = workstacks_root.expanduser().resolve()
        create_global_config(ctx.global_config_ops, workstacks_root, shell_setup_complete=False)
        click.echo(f"Created global config at {ctx.global_config_ops.get_path()}")
        # Show graphite status on first init
        has_graphite = detect_graphite()
        if has_graphite:
            click.echo("Graphite (gt) detected - will use 'gt create' for new branches")
        else:
            click.echo("Graphite (gt) not detected - will use 'git' for branch creation")

    # When --repo is set, verify that global config exists
    if repo and not ctx.global_config_ops.exists():
        click.echo(f"Global config not found at {ctx.global_config_ops.get_path()}", err=True)
        click.echo("Run 'workstack init' without --repo to create global config first.", err=True)
        raise SystemExit(1)

    # Now proceed with repo-specific setup
    repo_context = discover_repo_context(ctx, Path.cwd())

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

    # Check for .gitignore and add .PLAN.md and .env
    gitignore_path = repo_context.root / ".gitignore"
    if not gitignore_path.exists():
        # Early return: no gitignore file
        pass
    else:
        gitignore_content = gitignore_path.read_text(encoding="utf-8")
        modified = False

        # Add .PLAN.md
        gitignore_content, plan_added = _add_gitignore_entry(
            gitignore_content,
            ".PLAN.md",
            "Add .PLAN.md to .gitignore?",
        )
        modified = modified or plan_added

        # Add .env
        gitignore_content, env_added = _add_gitignore_entry(
            gitignore_content,
            ".env",
            "Add .env to .gitignore?",
        )
        modified = modified or env_added

        # Write if modified
        if modified:
            gitignore_path.write_text(gitignore_content, encoding="utf-8")
            click.echo(f"Updated {gitignore_path}")

    # On first-time init, offer shell setup if not already completed
    if first_time_init:
        if not ctx.global_config_ops.get_shell_setup_complete():
            setup_complete = perform_shell_setup()
            if setup_complete:
                ctx.global_config_ops.set(shell_setup_complete=True)
