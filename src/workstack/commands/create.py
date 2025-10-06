import re
import shlex
import shutil
import subprocess
from collections.abc import Iterable, Mapping
from pathlib import Path

import click

from workstack.config import LoadedConfig, load_config
from workstack.context import WorkstackContext
from workstack.core import discover_repo_context, ensure_work_dir, worktree_path_for

_SAFE_COMPONENT_RE = re.compile(r"[^A-Za-z0-9._/-]+")


def sanitize_branch_component(name: str) -> str:
    """Return a sanitized, predictable branch component from an arbitrary name.

    - Lowercases input
    - Replaces characters outside `[A-Za-z0-9._/-]` with `-`
    - Collapses consecutive `-`
    - Strips leading/trailing `-` and `/`
    Returns `"work"` if the result is empty.
    """

    lowered = name.strip().lower()
    replaced = _SAFE_COMPONENT_RE.sub("-", lowered)
    collapsed = re.sub(r"-+", "-", replaced)
    trimmed = collapsed.strip("-/")
    return trimmed or "work"


def sanitize_worktree_name(name: str) -> str:
    """Sanitize a worktree name for use as a directory name.

    - Lowercases input
    - Replaces underscores with hyphens
    - Replaces characters outside `[A-Za-z0-9.-]` with `-`
    - Collapses consecutive `-`
    - Strips leading/trailing `-`
    Returns `"work"` if the result is empty.
    """

    lowered = name.strip().lower()
    # Replace underscores with hyphens
    replaced_underscores = lowered.replace("_", "-")
    # Replace unsafe characters with hyphens
    replaced = re.sub(r"[^a-z0-9.-]+", "-", replaced_underscores)
    # Collapse consecutive hyphens
    collapsed = re.sub(r"-+", "-", replaced)
    # Strip leading/trailing hyphens
    trimmed = collapsed.strip("-")
    return trimmed or "work"


def default_branch_for_worktree(name: str) -> str:
    """Default branch name for a worktree with the given `name`.

    Returns the sanitized name directly (without any prefix).
    """

    return sanitize_branch_component(name)


def add_worktree(
    ctx: WorkstackContext,
    repo_root: Path,
    path: Path,
    *,
    branch: str | None,
    ref: str | None,
    use_existing_branch: bool,
    use_graphite: bool,
) -> None:
    """Create a git worktree.

    If `use_existing_branch` is True and `branch` is provided, checks out the existing branch
    in the new worktree: `git worktree add <path> <branch>`.

    If `use_existing_branch` is False and `branch` is provided, creates a new branch:
    - With graphite: `gt create <branch>` followed by `git worktree add <path> <branch>`
    - Without graphite: `git worktree add -b <branch> <path> <ref or HEAD>`

    Otherwise, uses `git worktree add <path> <ref or HEAD>`.
    """

    if branch and use_existing_branch:
        ctx.git_ops.add_worktree(repo_root, path, branch=branch, ref=None, create_branch=False)
    elif branch:
        if use_graphite:
            cwd = Path.cwd()
            original_branch = ctx.git_ops.get_current_branch(cwd)
            if original_branch is None:
                raise ValueError("Cannot create graphite branch from detached HEAD")
            subprocess.run(["gt", "create", branch], cwd=cwd, check=True)
            ctx.git_ops.checkout_branch(cwd, original_branch)
            ctx.git_ops.add_worktree(repo_root, path, branch=branch, ref=None, create_branch=False)
        else:
            ctx.git_ops.add_worktree(repo_root, path, branch=branch, ref=ref, create_branch=True)
    else:
        ctx.git_ops.add_worktree(repo_root, path, branch=None, ref=ref, create_branch=False)


def make_env_content(cfg: LoadedConfig, *, worktree_path: Path, repo_root: Path, name: str) -> str:
    """Render .env content using config templates.

    Substitution variables:
      - {worktree_path}
      - {repo_root}
      - {name}
    """

    variables: Mapping[str, str] = {
        "worktree_path": str(worktree_path),
        "repo_root": str(repo_root),
        "name": name,
    }

    lines: list[str] = []
    for key, template in cfg.env.items():
        value = template.format(**variables)
        # Quote value to be safe; dotenv parsers commonly accept quotes.
        lines.append(f"{key}={quote_env_value(value)}")

    # Always include these basics for convenience
    lines.append(f"WORKTREE_PATH={quote_env_value(str(worktree_path))}")
    lines.append(f"REPO_ROOT={quote_env_value(str(repo_root))}")
    lines.append(f"WORKTREE_NAME={quote_env_value(name)}")

    return "\n".join(lines) + "\n"


def quote_env_value(value: str) -> str:
    """Return a quoted value suitable for .env files."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


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
@click.pass_obj
def create(
    ctx: WorkstackContext,
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
        current_branch = ctx.git_ops.get_current_branch(Path.cwd())
        if current_branch is None:
            click.echo("Error: HEAD is detached (not on a branch)", err=True)
            raise SystemExit(1)

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

    # Validate that name is not a reserved word
    if name.lower() == "root":
        click.echo('Error: "root" is a reserved name and cannot be used for a worktree.', err=True)
        raise SystemExit(1)

    # Validate that name is not main or master (common branch names that should use root)
    if name.lower() in ("main", "master"):
        click.echo(
            f'Error: "{name}" cannot be used as a worktree name.\n'
            f"To switch to the {name} branch in the root repository, use:\n"
            f"  workstack switch root",
            err=True,
        )
        raise SystemExit(1)

    repo = discover_repo_context(ctx, Path.cwd())
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
        to_branch = ref if ref else ctx.git_ops.detect_default_branch(repo.root)

        # Switch current worktree to the target branch first
        ctx.git_ops.checkout_branch(repo.root, to_branch)

        # Create worktree with existing branch
        add_worktree(
            ctx,
            repo.root,
            wt_path,
            branch=branch,
            ref=None,
            use_existing_branch=True,
            use_graphite=False,
        )
    elif from_branch:
        # Create worktree with existing branch
        add_worktree(
            ctx,
            repo.root,
            wt_path,
            branch=branch,
            ref=None,
            use_existing_branch=True,
            use_graphite=False,
        )
    else:
        # Create worktree via git. If no branch provided, derive a sensible default.
        if branch is None:
            branch = default_branch_for_worktree(name)

        # Get graphite setting from global config
        use_graphite = ctx.global_config_ops.get_use_graphite()
        add_worktree(
            ctx,
            repo.root,
            wt_path,
            branch=branch,
            ref=ref,
            use_graphite=use_graphite,
            use_existing_branch=False,
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

    click.echo(f"Created workstack at {wt_path} checked out at branch '{branch}'")
    click.echo(f"\nworkstack switch {name}")


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
