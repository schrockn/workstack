import os
import shlex
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Iterable
from pathlib import Path

import click

from .activation import render_activation_script
from .config import (
    GLOBAL_CONFIG_PATH,
    create_global_config,
    detect_graphite,
    discover_presets,
    load_config,
    load_global_config,
    render_config_template,
)
from .core import (
    discover_repo_context,
    ensure_work_dir,
    make_env_content,
    worktree_path_for,
)
from .detect import is_repo_named
from .git import (
    add_worktree,
    checkout_branch,
    detect_default_branch,
    get_current_branch,
    get_pr_status,
    get_worktree_branches,
    remove_worktree,
)
from .naming import default_branch_for_worktree, sanitize_worktree_name

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])  # terse help flags


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(package_name="workstack")
def cli() -> None:
    """Manage git worktrees in a global worktrees directory."""


@cli.group("completion")
def completion_group() -> None:
    """Generate shell completion scripts."""


@completion_group.command("bash")
def completion_bash() -> None:
    """Generate bash completion script.

    \b
    To load completions in your current shell session:
      source <(workstack completion bash)

    \b
    To load completions permanently, add to your ~/.bashrc:
      echo 'source <(workstack completion bash)' >> ~/.bashrc

    \b
    Alternatively, you can save the completion script to bash_completion.d:
      workstack completion bash > /usr/local/etc/bash_completion.d/workstack

    \b
    You will need to start a new shell for this setup to take effect.
    """
    # Find the workstack executable
    workstack_exe = shutil.which("workstack")
    if not workstack_exe:
        # Fallback to current Python + module
        workstack_exe = sys.argv[0]

    env = os.environ.copy()
    env["_WORKSTACK_COMPLETE"] = "bash_source"
    result = subprocess.run([workstack_exe], env=env, capture_output=True, text=True)
    click.echo(result.stdout, nl=False)


@completion_group.command("zsh")
def completion_zsh() -> None:
    """Generate zsh completion script.

    \b
    To load completions in your current shell session:
      source <(workstack completion zsh)

    \b
    To load completions permanently, add to your ~/.zshrc:
      echo 'source <(workstack completion zsh)' >> ~/.zshrc

    \b
    Note: Make sure compinit is called in your ~/.zshrc after loading completions.

    \b
    You will need to start a new shell for this setup to take effect.
    """
    # Find the workstack executable
    workstack_exe = shutil.which("workstack")
    if not workstack_exe:
        # Fallback to current Python + module
        workstack_exe = sys.argv[0]

    env = os.environ.copy()
    env["_WORKSTACK_COMPLETE"] = "zsh_source"
    result = subprocess.run([workstack_exe], env=env, capture_output=True, text=True)
    click.echo(result.stdout, nl=False)


@completion_group.command("fish")
def completion_fish() -> None:
    """Generate fish completion script.

    \b
    To load completions in your current shell session:
      workstack completion fish | source

    \b
    To load completions permanently:
      mkdir -p ~/.config/fish/completions && \\
      workstack completion fish > ~/.config/fish/completions/workstack.fish

    \b
    You will need to start a new shell for this setup to take effect.
    """
    # Find the workstack executable
    workstack_exe = shutil.which("workstack")
    if not workstack_exe:
        # Fallback to current Python + module
        workstack_exe = sys.argv[0]

    env = os.environ.copy()
    env["_WORKSTACK_COMPLETE"] = "fish_source"
    result = subprocess.run([workstack_exe], env=env, capture_output=True, text=True)
    click.echo(result.stdout, nl=False)


@cli.command("create")
@click.argument("name", metavar="NAME", required=False)
@click.option(
    "--branch",
    "branch",
    type=str,
    help=(
        "Branch name to create and check out in the worktree. Defaults to NAME if omitted."
    ),
)
@click.option(
    "--ref",
    "ref",
    type=str,
    default=None,
    help=("Git ref to base the worktree on (e.g. HEAD, origin/main). Defaults to HEAD if omitted."),
)
@click.option(
    "--no-post",
    is_flag=True,
    help="Skip running post-create commands from config.toml.",
)
@click.option(
    "--plan",
    "plan_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help=(
        "Path to a plan markdown file. Will derive worktree name from filename "
        "and move to .PLAN.md in the worktree."
    ),
)
@click.option(
    "--from-current-branch",
    is_flag=True,
    help=(
        "Move the current branch to the new worktree, then switch current worktree to --ref "
        "(defaults to main/master). NAME defaults to current branch name."
    ),
)
@click.option(
    "--from-branch",
    "from_branch",
    type=str,
    default=None,
    help=(
        "Create worktree from an existing branch. NAME defaults to the branch name."
    ),
)
def create(
    name: str | None,
    branch: str | None,
    ref: str | None,
    no_post: bool,
    plan_file: Path | None,
    from_current_branch: bool,
    from_branch: str | None,
) -> None:
    """Create a worktree and write a .env file.

    Reads config.toml for env templates and post-create commands (if present).
    If --plan is provided, derives name from the plan filename and moves it to
    .PLAN.md in the worktree.
    If --from-current-branch is provided, moves the current branch to the new worktree.
    If --from-branch is provided, creates a worktree from an existing branch.
    """

    # Validate mutually exclusive options
    flags_set = sum([from_current_branch, from_branch is not None, plan_file is not None])
    if flags_set > 1:
        click.echo("Cannot use multiple of: --from-current-branch, --from-branch, --plan")
        raise SystemExit(1)

    # Handle --from-current-branch flag
    if from_current_branch:
        # Get the current branch
        try:
            current_branch = get_current_branch(Path.cwd())
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1) from e
        except subprocess.CalledProcessError as e:
            click.echo(
                "Error: Not in a git repository or unable to determine current branch.", err=True
            )
            raise SystemExit(1) from e

        # Set branch to current branch and derive name if not provided
        if branch:
            click.echo("Cannot specify --branch with --from-current-branch (uses current branch).")
            raise SystemExit(1)
        branch = current_branch

        if not name:
            name = sanitize_worktree_name(current_branch)

    # Handle --from-branch flag
    elif from_branch:
        if branch:
            click.echo("Cannot specify --branch with --from-branch (uses the specified branch).")
            raise SystemExit(1)
        branch = from_branch

        if not name:
            name = sanitize_worktree_name(from_branch)

    # Handle --plan flag
    elif plan_file:
        if name:
            click.echo("Cannot specify both NAME and --plan. Use one or the other.")
            raise SystemExit(1)
        # Derive name from plan filename (strip extension)
        plan_stem = plan_file.stem  # filename without extension
        name = sanitize_worktree_name(plan_stem)

    # Regular create (no special flags)
    else:
        if not name:
            click.echo("Must provide NAME or --plan or --from-branch or --from-current-branch option.")
            raise SystemExit(1)

    # At this point, name should always be set
    assert name is not None, "name must be set by now"

    repo = discover_repo_context(Path.cwd())
    work_dir = ensure_work_dir(repo)
    cfg = load_config(work_dir)
    wt_path = worktree_path_for(work_dir, name)

    if wt_path.exists():
        click.echo(f"Worktree path already exists: {wt_path}")
        raise SystemExit(1)

    # Handle from-current-branch logic: switch current worktree first
    to_branch = None
    if from_current_branch:
        # Determine which branch to switch to (use ref if provided, else main/master)
        to_branch = ref if ref else detect_default_branch(repo.root)

        # Switch current worktree to the target branch first
        checkout_branch(repo.root, to_branch)

        # Create worktree with existing branch
        add_worktree(repo.root, wt_path, branch=branch, ref=None, use_existing_branch=True)
    elif from_branch:
        # Create worktree with existing branch
        add_worktree(repo.root, wt_path, branch=branch, ref=None, use_existing_branch=True)
    else:
        # Create worktree via git. If no branch provided, derive a sensible default.
        if branch is None:
            branch = default_branch_for_worktree(name)

        # Get graphite setting from global config
        global_config = load_global_config()
        add_worktree(
            repo.root, wt_path, branch=branch, ref=ref, use_graphite=global_config.use_graphite
        )

    # Write .env based on config
    env_content = make_env_content(cfg, worktree_path=wt_path, repo_root=repo.root, name=name)
    (wt_path / ".env").write_text(env_content, encoding="utf-8")

    # Move plan file if provided
    if plan_file:
        plan_dest = wt_path / ".PLAN.md"
        shutil.move(str(plan_file), str(plan_dest))
        click.echo(f"Moved plan to {plan_dest}")

    # Post-create commands
    if not no_post and cfg.post_create_commands:
        click.echo("Running post-create commands...")
        run_commands_in_worktree(
            commands=cfg.post_create_commands,
            worktree_path=wt_path,
            shell=cfg.post_create_shell,
        )

    if from_current_branch:
        click.echo(f"Moved branch '{branch}' to worktree: {wt_path}")
        click.echo(f"Current worktree switched to branch: {to_branch}")
        click.echo(f"To activate the new worktree: source <(workstack switch {name} --script)")
    else:
        click.echo(str(wt_path))
        click.echo(f"source <(workstack switch {name} --script)")


def run_commands_in_worktree(
    *, commands: Iterable[str], worktree_path: Path, shell: str | None
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


def complete_worktree_names(
    ctx: click.Context, param: click.Parameter, incomplete: str
) -> list[str]:
    """Shell completion for worktree names. Includes default branch (main/master) for root repo.

    This is a shell completion function, which is an acceptable error boundary.
    Exceptions are caught to provide graceful degradation - if completion fails,
    we return an empty list rather than breaking the user's shell experience.
    """
    try:
        repo = discover_repo_context(Path.cwd())
        work_dir = repo.work_dir

        # Include default branch name (main or master) for root repo
        names = []
        default_branch = detect_default_branch(repo.root)
        if default_branch.startswith(incomplete):
            names.append(default_branch)

        # Add worktree directories
        if work_dir.exists():
            names.extend(
                [p.name for p in work_dir.iterdir() if p.is_dir() and p.name.startswith(incomplete)]
            )

        return names
    except Exception:
        # Shell completion error boundary: return empty list for graceful degradation
        return []


@cli.command("switch")
@click.argument("name", metavar="NAME", shell_complete=complete_worktree_names)
@click.option(
    "--script", is_flag=True, help="Print only the activation script without usage instructions."
)
def switch_cmd(name: str, script: bool) -> None:
    """Print shell code to switch to a worktree and activate it.

    Usage: source <(workstack switch NAME --script)

    NAME can be a worktree name, or 'main'/'master' to switch to the root repo.
    This will cd to the worktree directory and source its activate.sh script.
    """

    repo = discover_repo_context(Path.cwd())

    # Check if name refers to the default branch (main/master) which means root repo
    default_branch = detect_default_branch(repo.root)

    if name in ("main", "master"):
        # User is trying to switch to root repo via branch name
        if name != default_branch:
            # User specified wrong branch name
            click.echo(
                f"Error: This repository uses '{default_branch}' as the default branch, "
                f"not '{name}'.",
                err=True,
            )
            raise SystemExit(1)

        # Switch to root repo
        root_path = repo.root
        if script:
            # Generate activation script for root repo (similar to worktrees)
            venv_path = root_path / ".venv"
            venv_activate = venv_path / "bin" / "activate"

            lines = [
                f"# work activate-script (root repo - {default_branch})",
                f"cd '{str(root_path)}'",
                "# Create venv if it doesn't exist",
                f"if [ ! -d '{str(venv_path)}' ]; then",
                "  echo 'Creating virtual environment with uv sync...'",
                "  uv sync",
                "fi",
                f"if [ -f '{str(venv_activate)}' ]; then",
                f"  . '{str(venv_activate)}'",
                "fi",
                "# Load .env into the environment (allexport)",
                "set -a",
                "if [ -f ./.env ]; then . ./.env; fi",
                "set +a",
                f'echo "Switched to root repo ({default_branch}): $(pwd)"',
            ]
            click.echo("\n".join(lines) + "\n", nl=True)
        else:
            click.echo(f"source <(workstack switch {default_branch} --script)")
        return

    work_dir = ensure_work_dir(repo)
    wt_path = worktree_path_for(work_dir, name)

    if not wt_path.exists():
        click.echo(f"Worktree not found: {wt_path}", err=True)
        raise SystemExit(1)

    if script:
        activation_script = render_activation_script(worktree_path=wt_path)
        click.echo(activation_script, nl=True)
    else:
        click.echo(f"source <(workstack switch {name} --script)")


def _format_worktree_line(name: str, branch: str | None, is_root: bool = False) -> str:
    """Format a single worktree line with colorization."""
    name_part = click.style(name, fg="cyan", bold=True)
    branch_part = click.style(f"[{branch}]", fg="yellow") if branch else ""
    root_label = click.style("(root)", fg="bright_black") if is_root else ""
    hint = f"(source <(workstack switch {name} --script))"
    hint_part = click.style(hint, fg="bright_black")
    parts = [name_part, branch_part, root_label, hint_part]
    return " ".join(p for p in parts if p)


def _list_worktrees() -> None:
    """Internal function to list worktrees."""
    repo = discover_repo_context(Path.cwd())

    # Get branch info for all worktrees
    branches = get_worktree_branches(repo.root)

    # Show root repo first (using actual branch name instead of ".")
    root_branch = branches.get(repo.root)
    click.echo(_format_worktree_line(root_branch or "HEAD", root_branch, is_root=True))

    # Show worktrees
    work_dir = ensure_work_dir(repo)
    if not work_dir.exists():
        return
    entries = sorted(p for p in work_dir.iterdir() if p.is_dir())
    for p in entries:
        name = p.name
        wt_branch = branches.get(p)
        click.echo(_format_worktree_line(name, wt_branch, is_root=False))


@cli.command("list")
def list_cmd() -> None:
    """List worktrees with activation hints (alias: ls)."""
    _list_worktrees()


# Register ls as a hidden alias (won't show in help)
@cli.command("ls", hidden=True)
def ls_cmd() -> None:
    """List worktrees with activation hints (alias of 'list')."""
    _list_worktrees()


@cli.command("init")
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


def _remove_worktree(name: str, force: bool) -> None:
    """Internal function to remove a worktree.

    Uses git worktree remove when possible, but falls back to direct rmtree
    if git fails (e.g., worktree already removed from git metadata but directory exists).
    This is acceptable exception handling because there's no reliable way to check
    a priori if git worktree remove will succeed - the worktree might be in various
    states of partial removal.
    """
    repo = discover_repo_context(Path.cwd())
    work_dir = ensure_work_dir(repo)
    wt_path = worktree_path_for(work_dir, name)

    if not wt_path.exists() or not wt_path.is_dir():
        click.echo(f"Worktree not found: {wt_path}")
        raise SystemExit(1)

    if not force:
        if not click.confirm(f"Remove worktree directory {wt_path}?", default=False):
            click.echo("Aborted.")
            return

    # Try to remove via git first; ignore errors and fall back to rmtree
    # This handles cases where worktree is already removed from git metadata
    try:
        remove_worktree(repo.root, wt_path, force=force)
    except Exception:
        pass

    if wt_path.exists():
        shutil.rmtree(wt_path)

    click.echo(str(wt_path))


@cli.command("remove")
@click.argument("name", metavar="NAME", shell_complete=complete_worktree_names)
@click.option("-f", "--force", is_flag=True, help="Do not prompt for confirmation.")
def remove_cmd(name: str, force: bool) -> None:
    """Remove the worktree directory (alias: rm).

    With `-f/--force`, skips the confirmation prompt.
    Attempts `git worktree remove` before deleting the directory.
    """
    _remove_worktree(name, force)


# Register rm as a hidden alias (won't show in help)
@cli.command("rm", hidden=True)
@click.argument("name", metavar="NAME", shell_complete=complete_worktree_names)
@click.option("-f", "--force", is_flag=True, help="Do not prompt for confirmation.")
def rm_cmd(name: str, force: bool) -> None:
    """Remove the worktree directory (alias of 'remove')."""
    _remove_worktree(name, force)


@cli.group("config")
def config_group() -> None:
    """Manage workstack configuration."""


@config_group.command("list")
def config_list() -> None:
    """Print a list of configuration keys and values."""
    # Try to load global config
    global_config = None
    try:
        global_config = load_global_config()
        click.echo(click.style("Global configuration:", bold=True))
        click.echo(f"  workstacks_root={global_config.workstacks_root}")
        click.echo(f"  use_graphite={str(global_config.use_graphite).lower()}")
    except FileNotFoundError:
        click.echo(click.style("Global configuration:", bold=True))
        click.echo("  (not configured - run 'workstack init' to create)")

    # Try to load repo config
    try:
        repo = discover_repo_context(Path.cwd())
        work_dir = ensure_work_dir(repo)
        cfg = load_config(work_dir)

        click.echo(click.style("\nRepository configuration:", bold=True))
        if cfg.env:
            for key, value in cfg.env.items():
                click.echo(f"  env.{key}={value}")
        if cfg.post_create_shell:
            click.echo(f"  post_create.shell={cfg.post_create_shell}")
        if cfg.post_create_commands:
            click.echo(f"  post_create.commands={cfg.post_create_commands}")

        if not cfg.env and not cfg.post_create_shell and not cfg.post_create_commands:
            click.echo("  (no configuration - run 'workstack init --repo' to create)")
    except Exception:
        click.echo(click.style("\nRepository configuration:", bold=True))
        click.echo("  (not in a git repository)")


@config_group.command("get")
@click.argument("key", metavar="KEY")
def config_get(key: str) -> None:
    """Print the value of a given configuration key."""
    # Parse key into parts
    parts = key.split(".")

    # Handle global config keys
    if parts[0] in ("workstacks_root", "use_graphite"):
        try:
            global_config = load_global_config()
            if parts[0] == "workstacks_root":
                click.echo(str(global_config.workstacks_root))
            elif parts[0] == "use_graphite":
                click.echo(str(global_config.use_graphite).lower())
        except FileNotFoundError as e:
            click.echo(f"Global config not found at {GLOBAL_CONFIG_PATH}", err=True)
            raise SystemExit(1) from e
        return

    # Handle repo config keys
    try:
        repo = discover_repo_context(Path.cwd())
        work_dir = ensure_work_dir(repo)
        cfg = load_config(work_dir)

        if parts[0] == "env" and len(parts) == 2:
            if parts[1] in cfg.env:
                click.echo(cfg.env[parts[1]])
            else:
                click.echo(f"Key not found: {key}", err=True)
                raise SystemExit(1)
        elif parts[0] == "post_create":
            if len(parts) == 2:
                if parts[1] == "shell" and cfg.post_create_shell:
                    click.echo(cfg.post_create_shell)
                elif parts[1] == "commands":
                    for cmd in cfg.post_create_commands:
                        click.echo(cmd)
                else:
                    click.echo(f"Key not found: {key}", err=True)
                    raise SystemExit(1)
            else:
                click.echo(f"Invalid key: {key}", err=True)
                raise SystemExit(1)
        else:
            click.echo(f"Invalid key: {key}", err=True)
            raise SystemExit(1)
    except Exception as e:
        if "not in a git repository" in str(e).lower() or "not a git repository" in str(e).lower():
            click.echo("Not in a git repository", err=True)
        else:
            click.echo(f"Error: {e}", err=True)
        raise SystemExit(1) from e


@config_group.command("set")
@click.argument("key", metavar="KEY")
@click.argument("value", metavar="VALUE")
def config_set(key: str, value: str) -> None:
    """Update configuration with a value for the given key."""
    # Parse key into parts
    parts = key.split(".")

    # Handle global config keys
    if parts[0] in ("workstacks_root", "use_graphite"):
        try:
            load_global_config()
        except FileNotFoundError as e:
            click.echo(f"Global config not found at {GLOBAL_CONFIG_PATH}", err=True)
            click.echo("Run 'workstack init' to create it.", err=True)
            raise SystemExit(1) from e

        # Read existing config
        data = tomllib.loads(GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))

        # Update value
        if parts[0] == "workstacks_root":
            data["workstacks_root"] = str(Path(value).expanduser().resolve())
        elif parts[0] == "use_graphite":
            if value.lower() not in ("true", "false"):
                click.echo(f"Invalid boolean value: {value}", err=True)
                raise SystemExit(1)
            data["use_graphite"] = value.lower() == "true"

        # Write back
        content = f"""# Global workstack configuration
workstacks_root = "{data["workstacks_root"]}"
use_graphite = {str(data["use_graphite"]).lower()}
"""
        GLOBAL_CONFIG_PATH.write_text(content, encoding="utf-8")
        click.echo(f"Set {key}={value}")
        return

    # Handle repo config keys - not implemented yet
    click.echo("Setting repo config keys not yet implemented", err=True)
    raise SystemExit(1)


@cli.command("gc")
@click.option(
    "--debug",
    is_flag=True,
    # debug=True: Feature in development, keep debug output enabled by default for user feedback
    default=True,
    help="Show commands being executed.",
)
def gc_cmd(debug: bool) -> None:
    """List workstacks that are safe to delete (merged/closed PRs).

    Checks each worktree's branch for PRs that have been merged or closed on GitHub.
    Does not actually delete anything - just prints what could be deleted.
    """

    click.echo("Debug mode is enabled by default while this feature is in development.\n")

    def debug_print(msg: str) -> None:
        if debug:
            click.echo(click.style(msg, fg="bright_black"))

    repo = discover_repo_context(Path.cwd())
    work_dir = ensure_work_dir(repo)

    # Get all worktree branches
    debug_print("$ git worktree list --porcelain")
    branches = get_worktree_branches(repo.root)

    debug_print(f"Found {len(branches)} worktrees\n")

    # Track workstacks eligible for deletion
    deletable: list[tuple[str, str, str, int]] = []

    # Check each worktree (skip root repo)
    for wt_path, branch in branches.items():
        # Skip root repo
        if wt_path == repo.root:
            debug_print(f"Skipping root repo: {wt_path}")
            continue

        # Skip detached HEAD
        if branch is None:
            debug_print(f"Skipping detached HEAD: {wt_path}")
            continue

        # Check if this is a managed workstack
        if not wt_path.parent == work_dir:
            debug_print(
                f"Skipping non-managed worktree: {wt_path} "
                f"(parent: {wt_path.parent}, expected: {work_dir})"
            )
            continue

        # Get PR status
        debug_print(f"Checking PR status for {wt_path.name} [{branch}]...")
        state, pr_number, title = get_pr_status(repo.root, branch, debug=debug)

        debug_print(f"  → state={state}, pr_number={pr_number}, title={title}\n")

        # Check if PR is merged or closed
        if state in ("MERGED", "CLOSED") and pr_number is not None:
            name = wt_path.name
            deletable.append((name, branch, state, pr_number))

    # Display results
    if not deletable:
        click.echo("No workstacks found that are safe to delete.")
        return

    click.echo("Workstacks safe to delete:\n")

    for name, branch, state, pr_number in deletable:
        name_part = click.style(name, fg="cyan", bold=True)
        branch_part = click.style(f"[{branch}]", fg="yellow")
        state_part = click.style(state.lower(), fg="green" if state == "MERGED" else "red")
        pr_part = click.style(f"PR #{pr_number}", fg="bright_black")
        cmd_part = click.style(f"workstack rm {name}", fg="bright_black")

        click.echo(f"  {name_part} {branch_part} - {state_part} ({pr_part})")
        click.echo(f"    → {cmd_part}\n")
