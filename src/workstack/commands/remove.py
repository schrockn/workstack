import shutil
from pathlib import Path

import click

from ..core import discover_repo_context, ensure_work_dir, worktree_path_for
from ..git import remove_worktree
from .switch import complete_worktree_names


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


@click.command("remove")
@click.argument("name", metavar="NAME", shell_complete=complete_worktree_names)
@click.option("-f", "--force", is_flag=True, help="Do not prompt for confirmation.")
def remove_cmd(name: str, force: bool) -> None:
    """Remove the worktree directory (alias: rm).

    With `-f/--force`, skips the confirmation prompt.
    Attempts `git worktree remove` before deleting the directory.
    """
    _remove_worktree(name, force)


# Register rm as a hidden alias (won't show in help)
@click.command("rm", hidden=True)
@click.argument("name", metavar="NAME", shell_complete=complete_worktree_names)
@click.option("-f", "--force", is_flag=True, help="Do not prompt for confirmation.")
def rm_cmd(name: str, force: bool) -> None:
    """Remove the worktree directory (alias of 'remove')."""
    _remove_worktree(name, force)
