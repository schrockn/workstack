from pathlib import Path

import click

from ..config import (
    GLOBAL_CONFIG_PATH,
    create_global_config,
    detect_graphite,
    discover_presets,
    render_config_template,
)
from ..core import discover_repo_context, ensure_work_dir
from ..detect import is_repo_named


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
