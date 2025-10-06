import json
import shutil
from pathlib import Path

import click

from workstack.commands.switch import complete_worktree_names
from workstack.context import WorkstackContext
from workstack.core import discover_repo_context, ensure_work_dir, worktree_path_for
from workstack.graphite import get_branch_stack


def _delete_stack_branches(
    ctx: WorkstackContext, repo_root: Path, worktree_path: Path, worktree_name: str, *, force: bool
) -> None:
    """Delete all branches in the Graphite stack for a worktree.

    Args:
        ctx: Workstack context with git operations
        repo_root: Path to the repository root
        worktree_path: Path to the worktree being removed
        worktree_name: Name of the worktree (for error messages)
        force: Skip confirmation prompts
    """
    # Get the branch for this worktree
    worktrees = ctx.git_ops.list_worktrees(repo_root)
    worktree_branch = None
    for wt in worktrees:
        if wt.path == worktree_path:
            worktree_branch = wt.branch
            break

    if worktree_branch is None:
        click.echo(
            f"Warning: Worktree {worktree_name} is in detached HEAD state. "
            "Cannot delete stack without a branch.",
            err=True,
        )
        return

    # Get the full stack for this branch
    stack = get_branch_stack(ctx, repo_root, worktree_branch)

    if stack is None:
        click.echo(
            f"Warning: Branch {worktree_branch} is not tracked by Graphite. Cannot delete stack.",
            err=True,
        )
        return

    # Filter out trunk branches - we never delete those
    git_dir = ctx.git_ops.get_git_common_dir(repo_root)
    if git_dir is None:
        click.echo("Warning: Could not find git directory. Cannot delete stack.", err=True)
        return

    cache_file = git_dir / ".graphite_cache_persist"
    cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
    branches_data = cache_data.get("branches", [])

    trunk_branches = {
        branch_name
        for branch_name, info in branches_data
        if info.get("validationResult") == "TRUNK"
    }

    branches_to_delete = [b for b in stack if b not in trunk_branches]

    if not branches_to_delete:
        click.echo("No branches to delete (all branches in stack are trunk branches).")
        return

    # Show what will be deleted
    click.echo("Branches in stack to be deleted:")
    for branch in branches_to_delete:
        click.echo(f"  - {branch}")

    # Confirm deletion unless --force
    if not force:
        if not click.confirm("Delete these branches?", default=False):
            click.echo("Aborted.")
            return

    # Delete each branch
    for branch in branches_to_delete:
        ctx.git_ops.delete_branch_with_graphite(repo_root, branch, force=force)
        click.echo(f"Deleted branch: {branch}")


def _remove_worktree(ctx: WorkstackContext, name: str, force: bool, delete_stack: bool) -> None:
    """Internal function to remove a worktree.

    Uses git worktree remove when possible, but falls back to direct rmtree
    if git fails (e.g., worktree already removed from git metadata but directory exists).
    This is acceptable exception handling because there's no reliable way to check
    a priori if git worktree remove will succeed - the worktree might be in various
    states of partial removal.

    Args:
        ctx: Workstack context with git operations
        name: Name of the worktree to remove
        force: Skip confirmation prompts
        delete_stack: Delete all branches in the Graphite stack (requires Graphite)
    """
    repo = discover_repo_context(ctx, Path.cwd())
    work_dir = ensure_work_dir(repo)
    wt_path = worktree_path_for(work_dir, name)

    if not wt_path.exists() or not wt_path.is_dir():
        click.echo(f"Worktree not found: {wt_path}")
        raise SystemExit(1)

    # Handle --delete-stack option
    if delete_stack:
        use_graphite = ctx.global_config_ops.get_use_graphite()
        if not use_graphite:
            click.echo(
                "Error: --delete-stack requires Graphite to be enabled. "
                "Run 'workstack config set use-graphite true'",
                err=True,
            )
            raise SystemExit(1)

        _delete_stack_branches(ctx, repo.root, wt_path, name, force=force)

    # Now remove the worktree directory
    if not force:
        if not click.confirm(f"Remove worktree directory {wt_path}?", default=False):
            click.echo("Aborted.")
            return

    # Try to remove via git first; ignore errors and fall back to rmtree
    # This handles cases where worktree is already removed from git metadata
    try:
        ctx.git_ops.remove_worktree(repo.root, wt_path, force=force)
    except Exception:
        pass

    # Handle directory deletion (dry-run vs real)
    if wt_path.exists():
        if ctx.dry_run:
            click.echo(f"[DRY RUN] Would delete directory: {wt_path}", err=True)
        else:
            shutil.rmtree(wt_path)

    click.echo(str(wt_path))


@click.command("remove")
@click.argument("name", metavar="NAME", shell_complete=complete_worktree_names)
@click.option("-f", "--force", is_flag=True, help="Do not prompt for confirmation.")
@click.option(
    "-s",
    "--delete-stack",
    is_flag=True,
    help="Delete all branches in the Graphite stack (requires Graphite).",
)
@click.pass_obj
def remove_cmd(ctx: WorkstackContext, name: str, force: bool, delete_stack: bool) -> None:
    """Remove the worktree directory (alias: rm).

    With `-f/--force`, skips the confirmation prompt.
    Attempts `git worktree remove` before deleting the directory.
    """
    _remove_worktree(ctx, name, force, delete_stack)


# Register rm as a hidden alias (won't show in help)
@click.command("rm", hidden=True)
@click.argument("name", metavar="NAME", shell_complete=complete_worktree_names)
@click.option("-f", "--force", is_flag=True, help="Do not prompt for confirmation.")
@click.option(
    "-s",
    "--delete-stack",
    is_flag=True,
    help="Delete all branches in the Graphite stack (requires Graphite).",
)
@click.pass_obj
def rm_cmd(ctx: WorkstackContext, name: str, force: bool, delete_stack: bool) -> None:
    """Remove the worktree directory (alias of 'remove')."""
    _remove_worktree(ctx, name, force, delete_stack)
