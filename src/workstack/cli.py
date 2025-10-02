from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path

import click

from .activation import render_activation_script
from .config import (
    GLOBAL_CONFIG_PATH,
    create_global_config,
    detect_graphite,
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
from .git import add_worktree, checkout_branch, get_current_branch

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
    To load completions for every new session, execute once:

    \b
    Linux:
      workstack completion bash > /etc/bash_completion.d/workstack

    \b
    macOS:
      workstack completion bash > $(brew --prefix)/etc/bash_completion.d/workstack

    \b
    You will need to start a new shell for this setup to take effect.
    """
    import shutil
    import sys

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
    To load completions for every new session, execute once:
      mkdir -p ~/.zsh/completion
      workstack completion zsh > ~/.zsh/completion/_workstack

    \b
    Then add to your ~/.zshrc:
      fpath=(~/.zsh/completion $fpath)
      autoload -U compinit
      compinit

    \b
    You will need to start a new shell for this setup to take effect.
    """
    import sys

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
    To load completions for every new session, execute once:
      workstack completion fish > ~/.config/fish/completions/workstack.fish

    \b
    You will need to start a new shell for this setup to take effect.
    """
    import sys

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
        "Branch name to create and check out in the worktree. Defaults to `work/<name>` if omitted."
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
    "--move",
    is_flag=True,
    help=(
        "Move the current branch to the new worktree, then switch current worktree to --ref "
        "(defaults to main/master). Name defaults to current branch name."
    ),
)
def create(
    name: str | None,
    branch: str | None,
    ref: str | None,
    no_post: bool,
    plan_file: Path | None,
    move: bool,
) -> None:
    """Create a worktree and write a .env file.

    Reads config.toml for env templates and post-create commands (if present).
    If --plan is provided, derives name from the plan filename and moves it to
    .PLAN.md in the worktree.
    If --move is provided, moves the current branch to the new worktree.
    """

    # Handle --move flag
    if move:
        if plan_file:
            click.echo("Cannot use --move with --plan.")
            raise SystemExit(1)

        # Get the current branch
        try:
            current_branch = get_current_branch(Path.cwd())
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)
        except subprocess.CalledProcessError:
            click.echo(
                "Error: Not in a git repository or unable to determine current branch.", err=True
            )
            raise SystemExit(1)

        # Set branch to current branch and derive name if not provided
        if branch:
            click.echo("Cannot specify --branch with --move (uses current branch).")
            raise SystemExit(1)
        branch = current_branch

        if not name:
            from .naming import sanitize_worktree_name

            name = sanitize_worktree_name(current_branch)

    # Determine the worktree name (for non-move cases)
    if not move:
        if plan_file:
            if name:
                click.echo("Cannot specify both NAME and --plan. Use one or the other.")
                raise SystemExit(1)
            # Derive name from plan filename (strip extension)
            from .naming import sanitize_worktree_name

            plan_stem = plan_file.stem  # filename without extension
            name = sanitize_worktree_name(plan_stem)
        elif not name:
            click.echo("Must provide NAME or --plan option.")
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

    # Handle move logic: switch current worktree first
    to_branch = None
    if move:
        # Determine which branch to switch to (use ref if provided, else main/master)
        to_branch = ref
        if to_branch is None:
            # Try to find main or master
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--verify", "main"],
                    cwd=repo.root,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    to_branch = "main"
                else:
                    result = subprocess.run(
                        ["git", "rev-parse", "--verify", "master"],
                        cwd=repo.root,
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        to_branch = "master"
                    else:
                        click.echo(
                            "Error: Could not find 'main' or 'master' branch. "
                            "Please specify --ref explicitly."
                        )
                        raise SystemExit(1)
            except Exception as e:
                click.echo(f"Error determining default branch: {e}", err=True)
                raise SystemExit(1)

        # Switch current worktree to the target branch first
        checkout_branch(repo.root, to_branch)

        # Create worktree with existing branch
        add_worktree(repo.root, wt_path, branch=branch, ref=None, use_existing_branch=True)
    else:
        # Create worktree via git. If no branch provided, derive a sensible default.
        if branch is None:
            from .naming import default_branch_for_worktree

            branch = default_branch_for_worktree(name)

        # Get graphite setting from global config
        global_config = load_global_config()
        add_worktree(
            repo.root, wt_path, branch=branch, ref=ref, use_graphite=global_config.use_graphite
        )

    # Write .env based on config
    env_content = make_env_content(cfg, worktree_path=wt_path, repo_root=repo.root, name=name)
    (wt_path / ".env").write_text(env_content, encoding="utf-8")

    # Write activation script and make it executable
    act_path = wt_path / "activate.sh"
    act_content = render_activation_script(worktree_path=wt_path)
    act_path.write_text(act_content, encoding="utf-8")
    os.chmod(act_path, 0o755)

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

    if move:
        click.echo(f"Moved branch '{branch}' to worktree: {wt_path}")
        click.echo(f"Current worktree switched to branch: {to_branch}")
        click.echo(f"To activate the new worktree: source <(workstack switch {name})")
    else:
        click.echo(str(wt_path))
        click.echo(f"pushd {wt_path} && source activate.sh")


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


@cli.command("move")
@click.argument("name", metavar="NAME", required=False)
@click.option(
    "--to-branch",
    "to_branch",
    type=str,
    default=None,
    help="Branch to switch current worktree to (defaults to main or master).",
)
@click.option(
    "--no-post",
    is_flag=True,
    help="Skip running post-create commands from config.toml.",
)
def move_cmd(name: str | None, to_branch: str | None, no_post: bool) -> None:
    """Move the current branch to a new worktree.

    Creates a worktree with the current branch, then switches the current worktree
    to a different branch (defaults to main or master).

    If NAME is not provided, derives it from the current branch name.
    """

    repo = discover_repo_context(Path.cwd())

    # Get the current branch
    try:
        current_branch = get_current_branch(Path.cwd())
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except subprocess.CalledProcessError:
        click.echo(
            "Error: Not in a git repository or unable to determine current branch.", err=True
        )
        raise SystemExit(1)

    # Determine the worktree name
    if not name:
        from .naming import sanitize_worktree_name

        name = sanitize_worktree_name(current_branch)

    work_dir = ensure_work_dir(repo)
    cfg = load_config(work_dir)
    wt_path = worktree_path_for(work_dir, name)

    if wt_path.exists():
        click.echo(f"Worktree path already exists: {wt_path}")
        raise SystemExit(1)

    # Determine which branch to switch the current worktree to
    if to_branch is None:
        # Try to find main or master
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", "main"],
                cwd=repo.root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                to_branch = "main"
            else:
                result = subprocess.run(
                    ["git", "rev-parse", "--verify", "master"],
                    cwd=repo.root,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    to_branch = "master"
                else:
                    click.echo(
                        "Error: Could not find 'main' or 'master' branch. "
                        "Please specify --to-branch explicitly."
                    )
                    raise SystemExit(1)
        except Exception as e:
            click.echo(f"Error determining default branch: {e}", err=True)
            raise SystemExit(1)

    # Switch the current worktree to the target branch first
    # (must do this before creating the new worktree so the branch isn't locked)
    checkout_branch(repo.root, to_branch)

    # Create the worktree with the existing branch
    add_worktree(repo.root, wt_path, branch=current_branch, ref=None, use_existing_branch=True)

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

    click.echo(f"Moved branch '{current_branch}' to worktree: {wt_path}")
    click.echo(f"Current worktree switched to branch: {to_branch}")
    click.echo(f"To activate the new worktree: source <(workstack switch {name})")


def complete_worktree_names(
    ctx: click.Context, param: click.Parameter, incomplete: str
) -> list[str]:
    """Shell completion for worktree names. Includes '.' for root repo."""
    try:
        repo = discover_repo_context(Path.cwd())
        work_dir = repo.work_dir

        # Always include "." for root repo
        names = ["."] if ".".startswith(incomplete) else []

        # Add worktree directories
        if work_dir.exists():
            names.extend(
                [p.name for p in work_dir.iterdir() if p.is_dir() and p.name.startswith(incomplete)]
            )

        return names
    except Exception:
        return []


@cli.command("switch")
@click.argument("name", metavar="NAME", shell_complete=complete_worktree_names)
@click.option(
    "--script", is_flag=True, help="Print only the activation script without usage instructions."
)
def switch_cmd(name: str, script: bool) -> None:
    """Print shell code to switch to a worktree and activate it.

    Usage: source <(workstack switch NAME --script)

    Use '.' to switch to the root repo directory.
    This will cd to the worktree directory and source its activate.sh script.
    """

    repo = discover_repo_context(Path.cwd())

    # Handle special case: "." means root repo
    if name == ".":
        # Just cd to root, no activation script
        root_path = repo.root
        if script:
            lines = [
                f"cd '{str(root_path)}'",
                'echo "Switched to root repo: $(pwd)"',
            ]
            click.echo("\n".join(lines) + "\n", nl=True)
        else:
            click.echo("source <(workstack switch . --script)")
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


@cli.command("activate-script")
@click.argument("name", metavar="NAME", shell_complete=complete_worktree_names)
def activate_script(name: str) -> None:
    """Print shell code to activate the worktree env and venv.

    Note: `work create NAME` also writes `activate.sh` which can be
    sourced directly from the worktree directory.
    """

    repo = discover_repo_context(Path.cwd())
    work_dir = ensure_work_dir(repo)
    wt_path = worktree_path_for(work_dir, name)

    if not wt_path.exists():
        click.echo(f"Worktree not found: {wt_path}")
        raise SystemExit(1)

    script = render_activation_script(worktree_path=wt_path)
    click.echo(script, nl=True)


def _list_worktrees() -> None:
    """Internal function to list worktrees."""
    repo = discover_repo_context(Path.cwd())

    # Show root repo first
    click.echo(f". (root repo: {repo.root})")

    # Show worktrees
    work_dir = ensure_work_dir(repo)
    if not work_dir.exists():
        return
    entries = sorted(p for p in work_dir.iterdir() if p.is_dir())
    for p in entries:
        name = p.name
        act = p / "activate.sh"
        click.echo(f"{name} (source {act})")


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
    type=click.Choice(["auto", "generic", "dagster"], case_sensitive=False),
    default="auto",
    help=(
        "Config template to use. 'auto' detects Dagster repos by project files; "
        "'generic' writes a commented template; 'dagster' forces that preset."
    ),
)
def init_cmd(force: bool, preset: str) -> None:
    """Initialize workstack for this repo and scaffold config.toml."""

    # Check for global config first
    if not GLOBAL_CONFIG_PATH.exists():
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

    # Now proceed with repo-specific setup
    repo = discover_repo_context(Path.cwd())
    work_dir = ensure_work_dir(repo)
    cfg_path = work_dir / "config.toml"

    if cfg_path.exists() and not force:
        click.echo(f"Config already exists: {cfg_path}. Use --force to overwrite.")
        raise SystemExit(1)

    effective_preset: str | None
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

    # Check for .gitignore and add activate.sh and .PLAN.md
    gitignore_path = repo.root / ".gitignore"
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text(encoding="utf-8")
        additions = []

        if "activate.sh" not in gitignore_content:
            additions.append("activate.sh")

        if ".PLAN.md" not in gitignore_content:
            additions.append(".PLAN.md")

        if additions:
            if click.confirm(
                f"Add {', '.join(additions)} to .gitignore?",
                default=True,
            ):
                if not gitignore_content.endswith("\n"):
                    gitignore_content += "\n"
                gitignore_content += "\n".join(additions) + "\n"
                gitignore_path.write_text(gitignore_content, encoding="utf-8")
                click.echo(f"Added {', '.join(additions)} to {gitignore_path}")


@cli.command("co")
@click.argument("branch", metavar="BRANCH")
@click.option(
    "--name",
    "name",
    type=str,
    default=None,
    help="Name for the worktree (defaults to sanitized branch name).",
)
@click.option(
    "--no-post",
    is_flag=True,
    help="Skip running post-create commands from config.toml.",
)
def co_cmd(branch: str, name: str | None, no_post: bool) -> None:
    """Create a worktree and checkout an existing git branch.

    This is a convenience command that combines creating a worktree with checking out
    an existing branch. The worktree name defaults to the sanitized branch name.
    """

    repo = discover_repo_context(Path.cwd())

    # Determine the worktree name
    if not name:
        from .naming import sanitize_worktree_name

        name = sanitize_worktree_name(branch)

    work_dir = ensure_work_dir(repo)
    cfg = load_config(work_dir)
    wt_path = worktree_path_for(work_dir, name)

    if wt_path.exists():
        click.echo(f"Worktree path already exists: {wt_path}")
        raise SystemExit(1)

    # Create worktree with existing branch
    add_worktree(repo.root, wt_path, branch=branch, ref=None, use_existing_branch=True)

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
    click.echo(f"pushd {wt_path} && source activate.sh")


def _remove_worktree(name: str, force: bool) -> None:
    """Internal function to remove a worktree."""
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
    try:
        from .git import remove_worktree

        remove_worktree(repo.root, wt_path, force=force)
    except Exception:
        pass

    if wt_path.exists():
        shutil.rmtree(wt_path)

    click.echo(str(wt_path))


@cli.command("remove")
@click.argument("name", metavar="NAME")
@click.option("-f", "--force", is_flag=True, help="Do not prompt for confirmation.")
def remove_cmd(name: str, force: bool) -> None:
    """Remove the worktree directory (alias: rm).

    With `-f/--force`, skips the confirmation prompt.
    Attempts `git worktree remove` before deleting the directory.
    """
    _remove_worktree(name, force)


# Register rm as a hidden alias (won't show in help)
@cli.command("rm", hidden=True)
@click.argument("name", metavar="NAME")
@click.option("-f", "--force", is_flag=True, help="Do not prompt for confirmation.")
def rm_cmd(name: str, force: bool) -> None:
    """Remove the worktree directory (alias of 'remove')."""
    _remove_worktree(name, force)
