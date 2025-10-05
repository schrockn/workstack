import shlex
import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path

import click

from ..config import load_config, load_global_config
from ..core import discover_repo_context, ensure_work_dir, make_env_content, worktree_path_for
from ..git import add_worktree, checkout_branch, detect_default_branch, get_current_branch
from ..naming import default_branch_for_worktree, sanitize_worktree_name


@click.command("create")
@click.argument("name", metavar="NAME", required=False)
@click.option(
    "--branch",
    "branch",
    type=str,
    help=("Branch name to create and check out in the worktree. Defaults to NAME if omitted."),
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
    help=("Create worktree from an existing branch. NAME defaults to the branch name."),
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
            click.echo(
                "Must provide NAME or --plan or --from-branch or --from-current-branch option."
            )
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
