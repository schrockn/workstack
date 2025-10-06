import json
import subprocess
from pathlib import Path

import click

from workstack.context import WorkstackContext
from workstack.core import discover_repo_context, ensure_work_dir


def get_pr_status(
    repo_root: Path, branch: str, debug: bool = False
) -> tuple[str | None, int | None, str | None]:
    """Get PR status for a branch using GitHub CLI.

    Returns tuple of (state, pr_number, title) where:
    - state is "MERGED", "CLOSED", "OPEN", or None if no PR found
    - pr_number is the PR number or None
    - title is the PR title or None

    Returns (None, None, None) if gh CLI is not installed or not authenticated.

    Note: Uses try/except as an acceptable error boundary for handling gh CLI
    availability and authentication. We cannot reliably check gh installation
    and authentication status a priori without duplicating gh's logic.
    """

    def debug_print(msg: str) -> None:
        if debug:
            click.echo(click.style(msg, fg="bright_black"))

    try:
        # Check merged PRs first
        for state in ["merged", "closed", "open"]:
            cmd = [
                "gh",
                "pr",
                "list",
                "--state",
                state,
                "--head",
                branch,
                "--json",
                "state,number,title",
            ]

            debug_print(f"  $ {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            prs = json.loads(result.stdout)
            if prs:
                # Take the first PR (should only be one per branch)
                pr = prs[0]
                return pr.get("state"), pr.get("number"), pr.get("title")

        return None, None, None

    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        # gh not installed, not authenticated, or JSON parsing failed
        return None, None, None


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

    repo = discover_repo_context(Path.cwd(), ctx)
    work_dir = ensure_work_dir(repo)

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
