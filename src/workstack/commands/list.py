from pathlib import Path

import click

from workstack.config import load_global_config
from workstack.core import discover_repo_context, ensure_work_dir
from workstack.git import get_worktree_branches
from workstack.graphite import get_branch_stack


def _format_worktree_line(name: str, branch: str | None, is_root: bool = False) -> str:
    """Format a single worktree line with colorization."""
    name_part = click.style(name, fg="cyan", bold=True)
    branch_part = click.style(f"[{branch}]", fg="yellow") if branch else ""
    parts = [name_part, branch_part]
    return " ".join(p for p in parts if p)


def _list_worktrees(show_stacks: bool = False) -> None:
    """Internal function to list worktrees."""
    repo = discover_repo_context(Path.cwd())

    # Get branch info for all worktrees
    branches = get_worktree_branches(repo.root)

    # Check if stacks are requested and graphite is enabled
    if show_stacks:
        global_config = load_global_config()
        if not global_config.use_graphite:
            click.echo(
                "Error: --stacks requires graphite to be enabled. "
                "Run 'workstack config use-graphite true'",
                err=True,
            )
            raise SystemExit(1)

    # Show root repo first (using actual branch name instead of ".")
    root_branch = branches.get(repo.root)
    click.echo(_format_worktree_line(root_branch or "HEAD", root_branch, is_root=True))

    if show_stacks and root_branch:
        stack = get_branch_stack(repo.root, root_branch)
        if stack:
            for branch in reversed(stack):
                marker = "◉" if branch == root_branch else "◯"
                click.echo(f"  {marker}  {branch}")

    # Show worktrees
    work_dir = ensure_work_dir(repo)
    if not work_dir.exists():
        return
    entries = sorted(p for p in work_dir.iterdir() if p.is_dir())
    for p in entries:
        name = p.name
        wt_branch = branches.get(p)

        # Add blank line before each worktree (except first) when showing stacks
        if show_stacks and (root_branch or entries.index(p) > 0):
            click.echo()

        click.echo(_format_worktree_line(name, wt_branch, is_root=False))

        if show_stacks and wt_branch:
            stack = get_branch_stack(repo.root, wt_branch)
            if stack:
                for branch in reversed(stack):
                    marker = "◉" if branch == wt_branch else "◯"
                    click.echo(f"  {marker}  {branch}")


@click.command("list")
@click.option("--stacks", is_flag=True, help="Show graphite stacks for each worktree")
def list_cmd(stacks: bool) -> None:
    """List worktrees with activation hints (alias: ls)."""
    _list_worktrees(show_stacks=stacks)


# Register ls as a hidden alias (won't show in help)
@click.command("ls", hidden=True)
@click.option("--stacks", is_flag=True, help="Show graphite stacks for each worktree")
def ls_cmd(stacks: bool) -> None:
    """List worktrees with activation hints (alias of 'list')."""
    _list_worktrees(show_stacks=stacks)
