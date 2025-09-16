from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Iterable, Optional

import click

from .config import LoadedConfig, load_config, render_config_template
from .core import (
    RepoContext,
    discover_repo_context,
    ensure_work_dir,
    make_env_content,
    worktree_path_for,
)
from .git import add_worktree
from .detect import is_repo_named
from .activation import render_activation_script


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])  # terse help flags


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(package_name="work")
def cli() -> None:
    """Manage git worktrees under `.work/` in the current repo."""


@cli.command("create")
@click.argument("name", metavar="NAME")
@click.option(
    "--branch",
    "branch",
    type=str,
    help=(
        "Create and check out a new branch in the worktree. "
        "Equivalent to `git worktree add -b <branch>`."
    ),
)
@click.option(
    "--ref",
    "ref",
    type=str,
    default=None,
    help=(
        "Git ref to base the worktree on (e.g. HEAD, origin/main). "
        "If omitted and --branch is set, uses the current HEAD."
    ),
)
@click.option(
    "--no-post",
    is_flag=True,
    help="Skip running post-create commands from `.work/config.toml`.",
)
def create(name: str, branch: Optional[str], ref: Optional[str], no_post: bool) -> None:
    """Create a worktree at `.work/NAME` and write a .env file.

    Reads `.work/config.toml` for env templates and post-create commands (if present).
    """

    repo = discover_repo_context(Path.cwd())
    cfg = load_config(repo.root)
    work_dir = ensure_work_dir(repo)
    wt_path = worktree_path_for(work_dir, name)

    if wt_path.exists():
        click.echo(f"Worktree path already exists: {wt_path}")
        raise SystemExit(1)

    # Create worktree via git
    add_worktree(repo.root, wt_path, branch=branch, ref=ref)

    # Write .env based on config
    env_content = make_env_content(cfg, worktree_path=wt_path, repo_root=repo.root, name=name)
    (wt_path / ".env").write_text(env_content, encoding="utf-8")

    # Write activation script and make it executable
    act_path = wt_path / "activate.sh"
    act_content = render_activation_script(worktree_path=wt_path)
    act_path.write_text(act_content, encoding="utf-8")
    os.chmod(act_path, 0o755)

    # Post-create commands
    if not no_post and cfg.post_create_commands:
        click.echo("Running post-create commands...")
        run_commands_in_worktree(
            commands=cfg.post_create_commands,
            worktree_path=wt_path,
            shell=cfg.post_create_shell,
        )

    click.echo(str(wt_path))


def run_commands_in_worktree(
    *, commands: Iterable[str], worktree_path: Path, shell: Optional[str]
) -> None:
    """Run commands serially in the worktree directory.

    Each command is executed in its own subprocess. If `shell` is provided, commands
    run through that shell (e.g., "bash -lc <cmd>"). Otherwise, commands are tokenized
    via `shlex.split` and run directly.
    """

    for cmd in commands:
        if shell:
            subprocess.run([shell, "-lc", cmd], cwd=worktree_path, check=True)
        else:
            subprocess.run(shlex.split(cmd), cwd=worktree_path, check=True)


@cli.command("activate-script")
@click.argument("name", metavar="NAME")
def activate_script(name: str) -> None:
    """Print shell code to activate the worktree env and venv.

    Note: `work create NAME` also writes `.work/NAME/activate.sh` which can be
    sourced directly: `source .work/NAME/activate.sh`.
    """

    repo = discover_repo_context(Path.cwd())
    work_dir = ensure_work_dir(repo)
    wt_path = worktree_path_for(work_dir, name)

    if not wt_path.exists():
        click.echo(f"Worktree not found: {wt_path}")
        raise SystemExit(1)

    script = render_activation_script(worktree_path=wt_path)
    click.echo(script, nl=True)


@cli.command("list")
def list_cmd() -> None:
    """List worktrees under `.work/` (paths only)."""
    repo = discover_repo_context(Path.cwd())
    work_dir = ensure_work_dir(repo)
    for p in sorted(work_dir.iterdir() if work_dir.exists() else []):
        if p.is_dir():
            click.echo(str(p))


@cli.command("init")
@click.option("--force", is_flag=True, help="Overwrite existing .work/config.toml if present.")
@click.option(
    "--preset",
    type=click.Choice(["auto", "generic", "dagster"], case_sensitive=False),
    default="auto",
    help=(
        "Config template to use. 'auto' detects Dagster repos by project files; "
        "'generic' writes a commented template; 'dagster' forces that preset."
    ),
)
def init_cmd(force: bool, preset: str) -> None:
    """Initialize `.work/` and scaffold `.work/config.toml` for this repo."""

    repo = discover_repo_context(Path.cwd())
    work_dir = ensure_work_dir(repo)
    cfg_path = work_dir / "config.toml"

    if cfg_path.exists() and not force:
        click.echo(f"Config already exists: {cfg_path}. Use --force to overwrite.")
        raise SystemExit(1)

    effective_preset: Optional[str]
    choice = preset.lower()
    if choice == "auto":
        effective_preset = "dagster" if is_repo_named(repo.root, "dagster") else None
    elif choice == "generic":
        effective_preset = None
    else:
        effective_preset = choice

    content = render_config_template(effective_preset)
    cfg_path.write_text(content, encoding="utf-8")
    click.echo(f"Wrote {cfg_path}")
