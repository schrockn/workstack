import re
import shlex
import shutil
import subprocess
from collections.abc import Iterable, Mapping
from pathlib import Path

import click

from workstack.cli.config import LoadedConfig, load_config
from workstack.cli.core import discover_repo_context, ensure_workstacks_dir, worktree_path_for
from workstack.cli.graphite import get_parent_branch
from workstack.cli.shell_utils import render_cd_script, write_script_to_temp
from workstack.cli.subprocess_utils import run_with_error_reporting
from workstack.core.context import WorkstackContext

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


def strip_plan_from_filename(filename: str) -> str:
    """Remove 'plan' or 'implementation plan' from a filename stem intelligently.

    Handles case-insensitive matching and common separators (-, _, space).
    If removal would leave empty string, returns original unchanged.

    Examples:
        "devclikit-extraction-plan" → "devclikit-extraction"
        "my-feature-plan" → "my-feature"
        "implementation-plan-for-auth" → "for-auth"
        "feature_implementation_plan" → "feature"
        "plan" → "plan" (preserved - would be empty)
    """

    original_trimmed = filename.strip("-_ \t\n\r")
    original_is_plan = original_trimmed.casefold() == "plan" if original_trimmed else False

    # First, handle "implementation plan" with various separators
    # Pattern matches "implementation" + separator + "plan" as complete words
    impl_pattern = r"(^|[-_\s])(implementation)([-_\s])(plan)([-_\s]|$)"

    def replace_impl_plan(match: re.Match[str]) -> str:
        prefix = match.group(1)
        implementation_word = match.group(2)  # Preserves original case
        suffix = match.group(5)

        if suffix == "" and prefix:
            prefix_start = match.start(1)
            preceding_segment = filename[:prefix_start]
            trimmed_segment = preceding_segment.strip("-_ \t\n\r")
            if trimmed_segment:
                preceding_tokens = re.split(r"[-_\s]+", trimmed_segment)
                if preceding_tokens:
                    preceding_token = preceding_tokens[-1]
                    if preceding_token.casefold() == "plan":
                        return f"{prefix}{implementation_word}"

        # If entire string is "implementation-plan", keep just "implementation"
        if not prefix and not suffix:
            return implementation_word

        # If in the middle, preserve one separator
        if prefix and suffix:
            return prefix if prefix.strip() else suffix

        # At start or end: remove it and the adjacent separator
        return ""

    cleaned = re.sub(impl_pattern, replace_impl_plan, filename, flags=re.IGNORECASE)

    # Then handle standalone "plan" as a complete word
    plan_pattern = r"(^|[-_\s])(plan)([-_\s]|$)"

    def replace_plan(match: re.Match[str]) -> str:
        prefix = match.group(1)
        suffix = match.group(3)

        # If both prefix and suffix are empty (entire string is "plan"), keep it
        if not prefix and not suffix:
            return "plan"

        # If plan is in the middle, preserve one separator
        if prefix and suffix:
            # Use the prefix separator if available, otherwise use suffix
            return prefix if prefix.strip() else suffix

        # Plan at start or end: remove it and the adjacent separator
        return ""

    cleaned = re.sub(plan_pattern, replace_plan, cleaned, flags=re.IGNORECASE)

    def clean_separators(text: str) -> str:
        stripped = text.strip("-_ \t\n\r")
        stripped = re.sub(r"--+", "-", stripped)
        stripped = re.sub(r"__+", "_", stripped)
        stripped = re.sub(r"\s+", " ", stripped)
        return stripped

    cleaned = clean_separators(cleaned)

    plan_only_cleaned = clean_separators(
        re.sub(plan_pattern, replace_plan, filename, flags=re.IGNORECASE)
    )

    if (
        cleaned.casefold() == "plan"
        and plan_only_cleaned
        and plan_only_cleaned.casefold() != "plan"
    ):
        cleaned = plan_only_cleaned

    # If stripping left us with nothing or just "plan", preserve original
    if not cleaned or (cleaned.casefold() == "plan" and original_is_plan):
        return filename

    return cleaned


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
        # Validate branch is not already checked out
        existing_path = ctx.git_ops.is_branch_checked_out(repo_root, branch)
        if existing_path:
            click.echo(
                f"Error: Branch '{branch}' is already checked out at {existing_path}\n"
                f"Git doesn't allow the same branch to be checked out in multiple worktrees.\n\n"
                f"Options:\n"
                f"  • Use a different branch name\n"
                f"  • Create a new branch instead: workstack create {path.name}\n"
                f"  • Switch to that worktree: workstack switch {path.name}",
                err=True,
            )
            raise SystemExit(1)

        ctx.git_ops.add_worktree(repo_root, path, branch=branch, ref=None, create_branch=False)
    elif branch:
        if use_graphite:
            cwd = Path.cwd()
            original_branch = ctx.git_ops.get_current_branch(cwd)
            if original_branch is None:
                raise ValueError("Cannot create graphite branch from detached HEAD")
            if ctx.git_ops.has_staged_changes(repo_root):
                click.echo(
                    "Error: Staged changes detected. "
                    "Graphite cannot create a branch while staged changes are present.\n"
                    "`gt create --no-interactive` attempts to commit staged files but fails when "
                    "no commit message is provided.\n\n"
                    "Resolve the staged changes before running `workstack create`:\n"
                    '  • Commit them: git commit -m "message"\n'
                    "  • Unstage them: git reset\n"
                    "  • Stash them: git stash\n"
                    "  • Disable Graphite: workstack config set use_graphite false",
                    err=True,
                )
                raise SystemExit(1)
            run_with_error_reporting(
                ["gt", "create", "--no-interactive", branch],
                cwd=cwd,
                error_prefix=f"Failed to create Graphite branch '{branch}'",
                troubleshooting=[
                    "Check if branch name is valid",
                    "Ensure Graphite is properly configured (gt repo init)",
                    f"Try creating the branch manually: gt create {branch}",
                    "Disable Graphite: workstack config set use_graphite false",
                ],
            )
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
    "--keep-plan",
    is_flag=True,
    help="Copy the plan file instead of moving it (requires --plan).",
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
@click.option(
    "--script",
    is_flag=True,
    hidden=True,
    help="Output shell script for directory change instead of messages.",
)
@click.pass_obj
def create(
    ctx: WorkstackContext,
    name: str | None,
    branch: str | None,
    ref: str | None,
    no_post: bool,
    plan_file: Path | None,
    keep_plan: bool,
    from_current_branch: bool,
    from_branch: str | None,
    script: bool,
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

    # Validate --keep-plan requires --plan
    if keep_plan and not plan_file:
        click.echo("Error: --keep-plan requires --plan", err=True)
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
        cleaned_stem = strip_plan_from_filename(plan_stem)
        name = sanitize_worktree_name(cleaned_stem)

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
    workstacks_dir = ensure_workstacks_dir(repo)
    cfg = load_config(workstacks_dir)
    wt_path = worktree_path_for(workstacks_dir, name)

    if wt_path.exists():
        click.echo(f"Worktree path already exists: {wt_path}")
        raise SystemExit(1)

    # Handle from-current-branch logic: switch current worktree first
    to_branch = None
    if from_current_branch:
        current_branch = ctx.git_ops.get_current_branch(Path.cwd())
        if current_branch is None:
            click.echo("Error: Unable to determine current branch", err=True)
            raise SystemExit(1)

        # Determine preferred branch to checkout (prioritize Graphite parent)
        parent_branch = (
            get_parent_branch(ctx, repo.root, current_branch) if current_branch else None
        )

        if parent_branch:
            # Prefer Graphite parent branch
            to_branch = parent_branch
        elif ref:
            # Use ref if provided
            to_branch = ref
        else:
            # Fall back to default branch (main/master)
            to_branch = ctx.git_ops.detect_default_branch(repo.root)

        # Check for edge case: can't move main to worktree then switch to main
        if current_branch == to_branch:
            click.echo(
                f"Error: Cannot use --from-current-branch when on '{current_branch}'.\n"
                f"The current branch cannot be moved to a worktree and then checked out again.\n\n"
                f"Alternatives:\n"
                f"  • Create a new branch: workstack create {name}\n"
                f"  • Switch to a feature branch first, then use --from-current-branch\n"
                f"  • Use --from-branch to create from a different existing branch",
                err=True,
            )
            raise SystemExit(1)

        # Check if target branch is available (not checked out in another worktree)
        checkout_path = ctx.git_ops.is_branch_checked_out(repo.root, to_branch)
        if checkout_path is not None:
            # Target branch is in use, fall back to detached HEAD
            ctx.git_ops.checkout_detached(Path.cwd(), current_branch)
        else:
            # Target branch is available, checkout normally
            ctx.git_ops.checkout_branch(Path.cwd(), to_branch)

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

    # Move or copy plan file if provided
    if plan_file:
        plan_dest = wt_path / ".PLAN.md"
        if keep_plan:
            shutil.copy2(str(plan_file), str(plan_dest))
            if not script:
                click.echo(f"Copied plan to {plan_dest}")
        else:
            shutil.move(str(plan_file), str(plan_dest))
            if not script:
                click.echo(f"Moved plan to {plan_dest}")

    # Post-create commands
    if not no_post and cfg.post_create_commands:
        click.echo("Running post-create commands...")
        run_commands_in_worktree(
            commands=cfg.post_create_commands,
            worktree_path=wt_path,
            shell=cfg.post_create_shell,
        )

    if script:
        script_content = render_cd_script(
            wt_path,
            comment="cd to new worktree",
            success_message="✓ Switched to new worktree.",
        )
        script_path = write_script_to_temp(
            script_content,
            command_name="create",
            comment=f"cd to {name}",
        )
        click.echo(str(script_path), nl=False)
    else:
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
        cmd_list = [shell, "-lc", cmd] if shell else shlex.split(cmd)
        run_with_error_reporting(
            cmd_list,
            cwd=worktree_path,
            error_prefix="Post-create command failed",
            troubleshooting=[
                "The worktree was created successfully, but a post-create command failed",
                "You can still use the worktree or re-run the command manually",
            ],
        )
