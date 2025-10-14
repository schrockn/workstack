from pathlib import Path

import click

from workstack.cli.core import discover_repo_context, ensure_workstacks_dir
from workstack.core.context import WorkstackContext


@click.command("gc")
@click.option(
    "--debug",
    is_flag=True,
    # debug=True: Feature in development, keep debug output enabled by default for user feedback
    default=True,
    help="Show commands being executed.",
)
@click.pass_obj
def gc_cmd(ctx: WorkstackContext, debug: bool) -> None:
    """List workstacks that are safe to delete (merged/closed PRs).

    Checks each worktree's branch for PRs that have been merged or closed on GitHub.
    Does not actually delete anything - just prints what could be deleted.
    """

    click.echo("Debug mode is enabled by default while this feature is in development.\n")

    def debug_print(msg: str) -> None:
        if debug:
            click.echo(click.style(msg, fg="bright_black"))

    repo = discover_repo_context(ctx, Path.cwd())
    workstacks_dir = ensure_workstacks_dir(repo)

    # Get all worktree branches
    debug_print("$ git worktree list --porcelain")
    worktrees = ctx.git_ops.list_worktrees(repo.root)
    branches = {wt.path: wt.branch for wt in worktrees}

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
        if not wt_path.parent == workstacks_dir:
            debug_print(
                f"Skipping non-managed worktree: {wt_path} "
                f"(parent: {wt_path.parent}, expected: {workstacks_dir})"
            )
            continue

        # Get PR status
        debug_print(f"Checking PR status for {wt_path.name} [{branch}]...")
        state, pr_number, title = ctx.github_ops.get_pr_status(repo.root, branch, debug=debug)

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
