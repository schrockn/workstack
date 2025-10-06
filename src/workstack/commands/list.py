from pathlib import Path

import click

from workstack.context import WorkstackContext
from workstack.core import discover_repo_context, ensure_work_dir
from workstack.graphite import get_branch_stack


def _format_worktree_line(name: str, branch: str | None, is_root: bool = False) -> str:
    """Format a single worktree line with colorization.

    Args:
        name: Worktree name to display
        branch: Branch name (if any)
        is_root: True if this is the root repository worktree

    Returns:
        Formatted line with appropriate colorization
    """
    # Root worktree gets green to distinguish it from regular worktrees
    name_color = "green" if is_root else "cyan"
    name_part = click.style(name, fg=name_color, bold=True)

    # Branch remains yellow (consistent across root and regular worktrees)
    branch_part = click.style(f"[{branch}]", fg="yellow") if branch else ""

    parts = [name_part, branch_part]
    return " ".join(p for p in parts if p)


def _filter_stack_for_worktree(
    stack: list[str],
    current_worktree_path: Path,
    all_worktree_branches: dict[Path, str | None],
) -> list[str]:
    """Filter a graphite stack to only show branches relevant to the current worktree.

    When displaying a stack for a specific worktree, we want to show:
    1. The current branch checked out in this worktree
    2. All ancestor branches (going down to trunk) - provides context
    3. Descendant branches ONLY if they're checked out in some worktree

    This ensures that:
    - Branches without active worktrees don't clutter the display
    - Ancestor context is preserved (even if ancestors aren't checked out)
    - Only "active" descendants (with worktrees) appear

    Example:
        Stack: [main, foo, bar, baz]
        Worktrees:
          - root on main
          - worktree-baz on baz

        Root display: [main, baz]  (skip foo, bar - no worktrees)
        Worktree-baz display: [main, foo, bar, baz]  (ancestors shown for context)

    Args:
        stack: The full graphite stack (ordered from trunk to leaf)
        current_worktree_path: Path to the worktree we're displaying the stack for
        all_worktree_branches: Mapping of all worktree paths to their checked-out branches

    Returns:
        Filtered stack with only relevant branches
    """
    # Get the branch checked out in the current worktree
    current_branch = all_worktree_branches.get(current_worktree_path)
    if current_branch is None or current_branch not in stack:
        # If current branch is not in stack (shouldn't happen), return full stack
        return stack

    # Find the index of the current branch in the stack
    current_idx = stack.index(current_branch)

    # Build a set of branches that are checked out in ANY worktree (including current)
    all_checked_out_branches = {
        branch for branch in all_worktree_branches.values() if branch is not None
    }

    # Filter the stack:
    # - Keep all ancestors (indices < current_idx) regardless of where they're checked out
    # - Keep the current branch
    # - For descendants (indices > current_idx):
    #   - Only keep if checked out in some worktree
    result = []
    for i, branch in enumerate(stack):
        if i <= current_idx:
            # Ancestors and current branch: always keep
            result.append(branch)
        else:
            # Descendants: only keep if checked out in some worktree
            if branch in all_checked_out_branches:
                result.append(branch)
            # else: skip it (not checked out anywhere)

    return result


def _display_branch_stack(
    ctx: WorkstackContext,
    repo_root: Path,
    worktree_path: Path,
    branch: str,
    all_branches: dict[Path, str | None],
) -> None:
    """Display the graphite stack for a worktree with colorization.

    Shows branches with colored markers indicating which is currently checked out.
    Current branch is emphasized with bright green, others are de-emphasized with gray.
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

    # Display stack with colored markers
    for branch_name in reversed(filtered_stack):
        is_current = branch_name == highlight_branch

        if is_current:
            # Current branch: bright green marker + bright green bold text
            marker = click.style("◉", fg="bright_green")
            branch_text = click.style(branch_name, fg="bright_green", bold=True)
        else:
            # Other branches: gray marker + normal text
            marker = click.style("◯", fg="bright_black")
            branch_text = branch_name  # Normal white text

        click.echo(f"  {marker}  {branch_text}")


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
