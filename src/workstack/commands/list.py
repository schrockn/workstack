from pathlib import Path

import click

from workstack.context import WorkstackContext
from workstack.core import discover_repo_context, ensure_work_dir
from workstack.graphite import get_branch_stack


def _format_worktree_line(name: str, branch: str | None, is_root: bool = False) -> str:
    """Format a single worktree line with colorization."""
    name_part = click.style(name, fg="cyan", bold=True)
    branch_part = click.style(f"[{branch}]", fg="yellow") if branch else ""
    parts = [name_part, branch_part]
    return " ".join(p for p in parts if p)


def _filter_stack_for_worktree(
    stack: list[str],
    current_worktree_path: Path,
    all_worktree_branches: dict[Path, str | None],
) -> list[str]:
    """Filter a graphite stack to exclude descendant branches checked out in other worktrees.

    When displaying a stack for a specific worktree, we want to show:
    1. The current branch checked out in this worktree
    2. All ancestor branches (going down to trunk)
    3. Descendant branches up to (but not including) the first branch checked out elsewhere

    This prevents child branches from appearing in a parent worktree's stack display
    while still showing ancestor branches that provide context.

    Example:
        Stack: [master, foo, bar, baz]
        - root worktree on master, foo worktree on foo:
          - root shows: [master] (stops at foo since it's in another worktree)
          - foo shows: [master, foo, bar, baz] (master shown even though in root)

    Args:
        stack: The full graphite stack (ordered from trunk to leaf)
        current_worktree_path: Path to the worktree we're displaying the stack for
        all_worktree_branches: Mapping of all worktree paths to their checked-out branches

    Returns:
        Filtered stack with descendant branches belonging to other worktrees removed
    """
    # Get the branch checked out in the current worktree
    current_branch = all_worktree_branches.get(current_worktree_path)
    if current_branch is None or current_branch not in stack:
        # If current branch is not in stack (shouldn't happen), return full stack
        return stack

    # Find the index of the current branch in the stack
    current_idx = stack.index(current_branch)

    # Build a set of branches that are checked out in OTHER worktrees
    other_worktree_branches = {
        branch
        for path, branch in all_worktree_branches.items()
        if path != current_worktree_path and branch is not None
    }

    # Filter the stack:
    # - Keep all ancestors (indices < current_idx) regardless of where they're checked out
    # - Keep the current branch
    # - For descendants (indices > current_idx):
    #   - Stop at the first branch that's checked out in another worktree
    #   - Keep all branches before that cutoff point
    result = []
    for i, branch in enumerate(stack):
        if i <= current_idx:
            # Ancestors and current branch: always keep
            result.append(branch)
        else:
            # Descendants: stop at first branch in another worktree
            if branch in other_worktree_branches:
                # Found a branch checked out elsewhere - stop here
                break
            result.append(branch)

    return result


def _display_branch_stack(
    ctx: WorkstackContext,
    repo_root: Path,
    worktree_path: Path,
    branch: str,
    all_branches: dict[Path, str | None],
) -> None:
    """Display the graphite stack for a worktree.

    Shows branches with markers indicating which is currently checked out.
    """
    stack = get_branch_stack(ctx, repo_root, branch)
    if not stack:
        return

    filtered_stack = _filter_stack_for_worktree(stack, worktree_path, all_branches)
    if not filtered_stack:
        return

    # Determine which branch to highlight
    actual_branch = ctx.git_ops.get_current_branch(worktree_path)
    highlight_branch = actual_branch if actual_branch else branch

    # Display stack with markers
    for branch_name in reversed(filtered_stack):
        marker = "◉" if branch_name == highlight_branch else "◯"
        click.echo(f"  {marker}  {branch_name}")


def _list_worktrees(ctx: WorkstackContext, show_stacks: bool = False) -> None:
    """Internal function to list worktrees."""
    repo = discover_repo_context(ctx, Path.cwd())

    # Get branch info for all worktrees
    worktrees = ctx.git_ops.list_worktrees(repo.root)
    branches = {wt.path: wt.branch for wt in worktrees}

    # Check if stacks are requested and graphite is enabled
    if show_stacks:
        if not ctx.global_config_ops.get_use_graphite():
            click.echo(
                "Error: --stacks requires graphite to be enabled. "
                "Run 'workstack config use-graphite true'",
                err=True,
            )
            raise SystemExit(1)

    # Show root repo first (display as "root" to distinguish from worktrees)
    root_branch = branches.get(repo.root)
    click.echo(_format_worktree_line("root", root_branch, is_root=True))

    if show_stacks and root_branch:
        _display_branch_stack(ctx, repo.root, repo.root, root_branch, branches)

    # Show worktrees
    work_dir = ensure_work_dir(repo)
    if not work_dir.exists():
        return
    entries = sorted(p for p in work_dir.iterdir() if p.is_dir())
    for p in entries:
        name = p.name
        # Find the actual worktree path from git worktree list
        # The path p might be a symlink or different from the actual worktree path
        wt_path = None
        wt_branch = None
        for branch_path, branch_name in branches.items():
            if branch_path.resolve() == p.resolve():
                wt_path = branch_path
                wt_branch = branch_name
                break

        # Add blank line before each worktree (except first) when showing stacks
        if show_stacks and (root_branch or entries.index(p) > 0):
            click.echo()

        click.echo(_format_worktree_line(name, wt_branch, is_root=False))

        if show_stacks and wt_branch and wt_path:
            _display_branch_stack(ctx, repo.root, wt_path, wt_branch, branches)


@click.command("list")
@click.option("--stacks", "-s", is_flag=True, help="Show graphite stacks for each worktree")
@click.pass_obj
def list_cmd(ctx: WorkstackContext, stacks: bool) -> None:
    """List worktrees with activation hints (alias: ls)."""
    _list_worktrees(ctx, show_stacks=stacks)


# Register ls as a hidden alias (won't show in help)
@click.command("ls", hidden=True)
@click.option("--stacks", "-s", is_flag=True, help="Show graphite stacks for each worktree")
@click.pass_obj
def ls_cmd(ctx: WorkstackContext, stacks: bool) -> None:
    """List worktrees with activation hints (alias of 'list')."""
    _list_worktrees(ctx, show_stacks=stacks)
