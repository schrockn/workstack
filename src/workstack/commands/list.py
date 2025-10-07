from pathlib import Path

import click

from workstack.context import WorkstackContext
from workstack.core import discover_repo_context, ensure_work_dir
from workstack.github_ops import PullRequestInfo
from workstack.graphite import _load_graphite_cache, get_branch_stack


def _format_worktree_line(name: str, branch: str | None, path: str | None, is_root: bool) -> str:
    """Format a single worktree line with colorization.

    Args:
        name: Worktree name to display
        branch: Branch name (if any)
        path: Filesystem path to display (if provided, shows path instead of branch)
        is_root: True if this is the root repository worktree

    Returns:
        Formatted line with appropriate colorization
    """
    # Root worktree gets green to distinguish it from regular worktrees
    name_color = "green" if is_root else "cyan"
    name_part = click.style(name, fg=name_color, bold=True)

    # If path is provided, show path in dim white; otherwise show branch in yellow
    if path:
        location_part = click.style(f"[{path}]", fg="white", dim=True)
    elif branch:
        location_part = click.style(f"[{branch}]", fg="yellow")
    else:
        location_part = ""

    parts = [name_part, location_part]
    return " ".join(p for p in parts if p)


def _filter_stack_for_worktree(
    stack: list[str],
    current_worktree_path: Path,
    all_worktree_branches: dict[Path, str | None],
    is_root_worktree: bool,
) -> list[str]:
    """Filter a graphite stack to only show branches relevant to the current worktree.

    When displaying a stack for a specific worktree, we want to show:
    - Root worktree: Current branch + all ancestors (no descendants)
    - Other worktrees: Ancestors + current + descendants that are checked out somewhere

    This ensures that:
    - Root worktree shows context from trunk down to current branch
    - Other worktrees show full context but only "active" descendants with worktrees
    - Branches without active worktrees don't clutter non-root displays

    Example:
        Stack: [main, foo, bar, baz]
        Worktrees:
          - root on bar
          - worktree-baz on baz

        Root display: [main, foo, bar]  (ancestors + current, no descendants)
        Worktree-baz display: [main, foo, bar, baz]  (full context with checked-out descendants)

    Args:
        stack: The full graphite stack (ordered from trunk to leaf)
        current_worktree_path: Path to the worktree we're displaying the stack for
        all_worktree_branches: Mapping of all worktree paths to their checked-out branches
        is_root_worktree: True if this is the root repository worktree

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

    # Filter the stack based on whether this is the root worktree
    if is_root_worktree:
        # Root worktree: show only ancestors + current (no descendants)
        # This keeps the display clean and focused on context
        return stack[: current_idx + 1]
    else:
        # Non-root worktree: show ancestors + current + descendants with worktrees
        # Build a set of branches that are checked out in ANY worktree
        all_checked_out_branches = {
            branch for branch in all_worktree_branches.values() if branch is not None
        }

        result = []
        for i, branch in enumerate(stack):
            if i <= current_idx:
                # Ancestors and current branch: always keep
                result.append(branch)
            else:
                # Descendants: only keep if checked out in some worktree
                if branch in all_checked_out_branches:
                    result.append(branch)

        return result


def _is_trunk_branch(
    ctx: WorkstackContext, repo_root: Path, branch: str, cache_data: dict | None = None
) -> bool:
    """Check if a branch is a trunk branch (has no parent in graphite).

    Returns False for missing cache files rather than None because this function
    answers a boolean question: "Is this branch trunk?" When cache is missing,
    the answer is definitively "no" (we can't determine trunk status, default to False).

    This differs from get_branch_stack() which returns None for missing cache because
    it's retrieving optional data - None indicates "no stack data available" vs
    an empty list which would mean "stack exists but is empty".

    Args:
        ctx: Workstack context with git operations
        repo_root: Path to the repository root
        branch: Branch name to check
        cache_data: Pre-loaded graphite cache data (optional optimization)
                   If None, cache will be loaded from disk

    Returns:
        True if the branch is a trunk branch (no parent), False otherwise
        False is also returned when cache is missing/inaccessible (conservative default)
    """
    if cache_data is None:
        git_dir = ctx.git_ops.get_git_common_dir(repo_root)
        if git_dir is None:
            return False

        cache_file = git_dir / ".graphite_cache_persist"
        if not cache_file.exists():
            return False

        cache_data = _load_graphite_cache(cache_file)

    branches_data = cache_data.get("branches", [])

    for branch_name, info in branches_data:
        if branch_name == branch:
            # Check if this is marked as trunk or has no parent
            is_trunk = info.get("validationResult") == "TRUNK"
            has_parent = info.get("parentBranchName") is not None
            return is_trunk or not has_parent

    return False


def _get_pr_status_emoji(pr: PullRequestInfo) -> str:
    """Determine the emoji to display for a PR based on its status.

    Args:
        pr: Pull request information

    Returns:
        Emoji character representing the PR's current state
    """
    if pr.is_draft:
        return "🚧"
    if pr.state == "MERGED":
        return "🟣"
    if pr.state == "CLOSED":
        return "⭕"
    if pr.checks_passing is True:
        return "✅"
    if pr.checks_passing is False:
        return "❌"
    # Open PR with no checks
    return "◯"


def _format_pr_info(
    ctx: WorkstackContext,
    repo_root: Path,
    branch: str,
    prs: dict[str, PullRequestInfo],
) -> str:
    """Format PR status indicator with emoji and link.

    Args:
        ctx: Workstack context with GitHub/Graphite operations
        repo_root: Repository root directory
        branch: Branch name
        prs: Mapping of branch name -> PullRequestInfo

    Returns:
        Formatted PR info string (e.g., "✅ #23") or empty string if no PR
    """
    pr = prs.get(branch)
    if pr is None:
        return ""

    emoji = _get_pr_status_emoji(pr)

    # Get Graphite URL (always available since we have owner/repo from GitHub)
    url = ctx.graphite_ops.get_graphite_url(pr.owner, pr.repo, pr.number)

    # Format as clickable link using OSC 8 terminal escape sequence
    # Format: \033]8;;URL\033\\TEXT\033]8;;\033\\
    pr_text = f"#{pr.number}"
    clickable_link = f"\033]8;;{url}\033\\{pr_text}\033]8;;\033\\"

    return f"{emoji} {clickable_link}"


def _display_branch_stack(
    ctx: WorkstackContext,
    repo_root: Path,
    worktree_path: Path,
    branch: str,
    all_branches: dict[Path, str | None],
    is_root_worktree: bool,
    cache_data: dict | None = None,  # If None, cache will be loaded from disk
    prs: dict[str, PullRequestInfo] | None = None,  # If None, no PR info displayed
) -> None:
    """Display the graphite stack for a worktree with colorization and PR info.

    Shows branches with colored markers indicating which is currently checked out.
    Current branch is emphasized with bright green, others are de-emphasized with gray.
    Also displays PR status and links for branches that have PRs.

    Args:
        ctx: Workstack context with git operations
        repo_root: Path to the repository root
        worktree_path: Path to the current worktree
        branch: Branch name to display stack for
        all_branches: Mapping of all worktree paths to their checked-out branches
        cache_data: Pre-loaded graphite cache data (if None, loaded from disk)
        prs: Mapping of branch names to PR information (if None, no PR info displayed)
    """
    stack = get_branch_stack(ctx, repo_root, branch)
    if not stack:
        return

    filtered_stack = _filter_stack_for_worktree(
        stack, worktree_path, all_branches, is_root_worktree
    )
    if not filtered_stack:
        return

    # Determine which branch to highlight
    actual_branch = ctx.git_ops.get_current_branch(worktree_path)
    highlight_branch = actual_branch if actual_branch else branch

    # Display stack with colored markers and PR info
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

        # Add PR info if available
        if prs:
            pr_info = _format_pr_info(ctx, repo_root, branch_name, prs)
            if pr_info:
                line = f"  {marker}  {branch_text} {pr_info}"
            else:
                line = f"  {marker}  {branch_text}"
        else:
            line = f"  {marker}  {branch_text}"

        click.echo(line)


def _list_worktrees(ctx: WorkstackContext, show_stacks: bool) -> None:
    """Internal function to list worktrees."""
    repo = discover_repo_context(ctx, Path.cwd())

    # Get branch info for all worktrees
    worktrees = ctx.git_ops.list_worktrees(repo.root)
    branches = {wt.path: wt.branch for wt in worktrees}

    # Load graphite cache once if showing stacks
    cache_data = None
    if show_stacks:
        if not ctx.global_config_ops.get_use_graphite():
            click.echo(
                "Error: --stacks requires graphite to be enabled. "
                "Run 'workstack config set use_graphite true'",
                err=True,
            )
            raise SystemExit(1)

        # Load cache once for all worktrees
        git_dir = ctx.git_ops.get_git_common_dir(repo.root)
        if git_dir is not None:
            cache_file = git_dir / ".graphite_cache_persist"
            if cache_file.exists():
                cache_data = _load_graphite_cache(cache_file)

    # Fetch PR information once for all branches (if show_pr_info is enabled)
    prs: dict[str, PullRequestInfo] | None = None
    if ctx.global_config_ops.get_show_pr_info():
        prs = ctx.github_ops.get_prs_for_repo(repo.root)

    # Show root repo first (display as "root" to distinguish from worktrees)
    root_branch = branches.get(repo.root)
    click.echo(_format_worktree_line("root", root_branch, path=None, is_root=True))

    if show_stacks and root_branch:
        _display_branch_stack(
            ctx, repo.root, repo.root, root_branch, branches, True, cache_data, prs
        )

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

        click.echo(_format_worktree_line(name, wt_branch, path=None, is_root=False))

        if show_stacks and wt_branch and wt_path:
            _display_branch_stack(
                ctx, repo.root, wt_path, wt_branch, branches, False, cache_data, prs
            )


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
