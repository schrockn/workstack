import os
import subprocess
from pathlib import Path

import click

from workstack.commands.remove import _remove_worktree
from workstack.context import WorkstackContext
from workstack.core import discover_repo_context, ensure_work_dir, worktree_path_for


def _return_to_original_worktree(work_dir: Path, current_worktree_name: str | None) -> None:
    """Return to original worktree if it exists."""
    if current_worktree_name is None:
        return

    wt_path = worktree_path_for(work_dir, current_worktree_name)
    if not wt_path.exists():
        return

    click.echo(f"\nReturning to: {current_worktree_name}")
    os.chdir(wt_path)


@click.command("sync")
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Pass --force to gt sync and automatically remove merged worktrees without confirmation.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    # dry_run=False: Allow destructive operations by default
    default=False,
    help="Show what would be done without executing destructive operations.",
)
@click.pass_obj
def sync_cmd(ctx: WorkstackContext, force: bool, dry_run: bool) -> None:
    """Sync with Graphite and clean up merged worktrees.

    This command must be run from a workstack-managed repository.

    Steps:
    1. Verify graphite is enabled
    2. Save current worktree location
    3. Switch to root worktree (to avoid git checkout conflicts)
    4. Run `gt sync [-f]` from root
    5. Identify merged/closed workstacks
    6. With -f: automatically remove worktrees without confirmation
    7. Without -f: show deletable worktrees and prompt for confirmation
    8. Return to original worktree (if it still exists)
    """

    # Step 1: Verify Graphite is enabled
    use_graphite = ctx.global_config_ops.get_use_graphite()
    if not use_graphite:
        click.echo(
            "Error: 'workstack sync' requires Graphite. "
            "Run 'workstack config set use-graphite true'",
            err=True,
        )
        raise SystemExit(1)

    # Step 2: Save current location
    repo = discover_repo_context(ctx, Path.cwd())
    work_dir = ensure_work_dir(repo)

    # Determine current worktree (if any)
    current_wt_path = Path.cwd().resolve()
    current_worktree_name: str | None = None

    if current_wt_path.parent == work_dir:
        current_worktree_name = current_wt_path.name

    # Step 3: Switch to root (only if not already at root)
    if Path.cwd().resolve() != repo.root:
        click.echo(f"Switching to root worktree: {repo.root}")
        os.chdir(repo.root)

    # Step 4: Run `gt sync`
    cmd = ["gt", "sync"]
    if force:
        cmd.append("-f")

    if not dry_run:
        click.echo(f"Running: {' '.join(cmd)}")
        try:
            ctx.graphite_ops.sync(repo.root, force=force)
        except subprocess.CalledProcessError as e:
            click.echo(f"Error: gt sync failed with exit code {e.returncode}", err=True)
            raise SystemExit(e.returncode) from e
        except FileNotFoundError as e:
            click.echo(
                "Error: 'gt' command not found. Install Graphite CLI: "
                "brew install withgraphite/tap/graphite",
                err=True,
            )
            raise SystemExit(1) from e
    else:
        click.echo(f"[DRY RUN] Would run {' '.join(cmd)}")

    # Step 5: Identify deletable workstacks
    worktrees = ctx.git_ops.list_worktrees(repo.root)

    # Track workstacks eligible for deletion
    deletable: list[tuple[str, str, str, int]] = []

    for wt in worktrees:
        # Skip root
        if wt.path == repo.root:
            continue

        # Skip detached HEAD
        if wt.branch is None:
            continue

        # Skip non-managed worktrees
        if wt.path.parent != work_dir:
            continue

        # Check PR status
        state, pr_number, title = ctx.github_ops.get_pr_status(repo.root, wt.branch, debug=False)

        if state in ("MERGED", "CLOSED") and pr_number is not None:
            name = wt.path.name
            deletable.append((name, wt.branch, state, pr_number))

    # Step 6: Display and optionally clean
    if not deletable:
        click.echo("\nNo workstacks to clean up.")
    else:
        click.echo("\nWorkstacks safe to delete:\n")

        for name, branch, state, pr_number in deletable:
            # Display formatted (reuse gc.py formatting)
            name_part = click.style(name, fg="cyan", bold=True)
            branch_part = click.style(f"[{branch}]", fg="yellow")
            state_part = click.style(state.lower(), fg="green" if state == "MERGED" else "red")
            pr_part = click.style(f"PR #{pr_number}", fg="bright_black")

            click.echo(f"  {name_part} {branch_part} - {state_part} ({pr_part})")

        click.echo()  # Blank line

        # Confirm unless --force or --dry-run
        if not force and not dry_run:
            if not click.confirm(f"Remove {len(deletable)} worktree(s)?", default=False):
                click.echo("Cleanup cancelled.")
                _return_to_original_worktree(work_dir, current_worktree_name)
                return

        # Remove each worktree
        for name, _branch, _state, _pr_number in deletable:
            if dry_run:
                click.echo(f"[DRY RUN] Would remove worktree: {name} (branch: {_branch})")
            else:
                click.echo(f"Removing worktree: {name} (branch: {_branch})")
                # Reuse remove logic from remove.py
                _remove_worktree(
                    ctx,
                    name,
                    force=True,  # Already confirmed above
                    delete_stack=False,  # Leave branches for gt sync -f
                    dry_run=False,
                )

        click.echo("\nNext step: Run 'gt sync -f' to delete the merged branches.")

    # Step 7: Return to original worktree
    if current_worktree_name:
        wt_path = worktree_path_for(work_dir, current_worktree_name)

        if wt_path.exists():
            click.echo(f"\nReturning to: {current_worktree_name}")
            os.chdir(wt_path)
        else:
            click.echo(
                f"\nNote: Original worktree '{current_worktree_name}' was deleted during cleanup."
            )
