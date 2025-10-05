from pathlib import Path

import click

from workstack.core import discover_repo_context, ensure_work_dir
from workstack.git import get_worktree_branches


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


@click.command("list")
def list_cmd() -> None:
    """List worktrees with activation hints (alias: ls)."""
    _list_worktrees()


# Register ls as a hidden alias (won't show in help)
@click.command("ls", hidden=True)
def ls_cmd() -> None:
    """List worktrees with activation hints (alias of 'list')."""
    _list_worktrees()
