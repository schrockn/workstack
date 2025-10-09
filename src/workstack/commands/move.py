"""Move branches between worktrees with explicit source specification."""

import subprocess
from pathlib import Path

import click

from workstack.commands.switch import complete_worktree_names
from workstack.context import WorkstackContext
from workstack.core import discover_repo_context, ensure_work_dir, worktree_path_for


def _get_worktree_branch(ctx: WorkstackContext, repo_root: Path, wt_path: Path) -> str | None:
    """Get the branch checked out in a worktree.

    Returns None if worktree is not found or is in detached HEAD state.
    """
    worktrees = ctx.git_ops.list_worktrees(repo_root)
    # Resolve paths for comparison to handle relative vs absolute paths
    wt_path_resolved = wt_path.resolve()
    for wt in worktrees:
        if wt.path.resolve() == wt_path_resolved:
            return wt.branch
    return None


def _has_uncommitted_changes(cwd: Path) -> bool:
    """Check if a worktree has uncommitted changes.

    Uses git status --porcelain to detect any uncommitted changes.
    Returns False if git command fails (worktree might be in invalid state).
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False
    return bool(result.stdout.strip())


def _find_worktree_with_branch(ctx: WorkstackContext, repo_root: Path, branch: str) -> Path | None:
    """Find the worktree path containing the specified branch.

    Returns None if the branch is not found in any worktree.
    """
    worktrees = ctx.git_ops.list_worktrees(repo_root)
    for wt in worktrees:
        if wt.branch == branch:
            return wt.path
    return None


def resolve_source_worktree(
    ctx: WorkstackContext,
    repo_root: Path,
    *,
    current: bool,
    branch: str | None,
    worktree: str | None,
    work_dir: Path,
) -> Path:
    """Determine source worktree from flags.

    Defaults to current worktree if no flags provided.
    Raises SystemExit if multiple flags specified or if source cannot be resolved.
    """
    # Count how many source flags are specified
    flag_count = sum([current, branch is not None, worktree is not None])

    if flag_count > 1:
        click.echo(
            "Error: Only one of --current, --branch, or --worktree can be specified", err=True
        )
        raise SystemExit(1)

    if flag_count == 0:
        # Default to current worktree
        current_wt = ctx.git_ops.get_git_common_dir(Path.cwd())
        if current_wt is None:
            click.echo("Error: Not in a git repository", err=True)
            raise SystemExit(1)

        # Resolve to actual worktree path
        resolved = current_wt.parent.resolve()
        return resolved

    if current:
        current_wt = ctx.git_ops.get_git_common_dir(Path.cwd())
        if current_wt is None:
            click.echo("Error: Not in a git repository", err=True)
            raise SystemExit(1)

        # Resolve to actual worktree path
        resolved = current_wt.parent.resolve()
        return resolved

    if branch:
        # Find worktree containing this branch
        wt = _find_worktree_with_branch(ctx, repo_root, branch)
        if wt is None:
            click.echo(f"Error: Branch '{branch}' not found in any worktree", err=True)
            raise SystemExit(1)
        return wt

    if worktree:
        # Resolve worktree name to path
        wt_path = worktree_path_for(work_dir, worktree)
        # Validate that the worktree exists
        if not wt_path.exists():
            click.echo(f"Error: Worktree '{worktree}' does not exist", err=True)
            raise SystemExit(1)
        return wt_path

    click.echo("Error: Invalid state - no source specified", err=True)
    raise SystemExit(1)


def detect_operation_type(
    source_wt: Path, target_wt: Path, ctx: WorkstackContext, repo_root: Path
) -> str:
    """Determine whether to move, swap, or create based on target existence.

    Returns "move", "swap", or "create".
    """
    target_exists = target_wt.exists()

    if not target_exists:
        return "create"

    # Target exists - check if it has a branch
    target_branch = _get_worktree_branch(ctx, repo_root, target_wt)
    if target_branch:
        return "swap"
    else:
        return "move"


def execute_move(
    ctx: WorkstackContext,
    repo_root: Path,
    source_wt: Path,
    target_wt: Path,
    fallback_ref: str,
    *,
    force: bool,
) -> None:
    """Execute move operation (target doesn't exist or is in detached HEAD).

    Moves the branch from source to target, then switches source to fallback_ref.
    """
    # Validate source has a branch
    source_branch = _get_worktree_branch(ctx, repo_root, source_wt)
    if source_branch is None:
        click.echo("Error: Source worktree is in detached HEAD state", err=True)
        raise SystemExit(1)

    # Check for uncommitted changes in source
    if _has_uncommitted_changes(source_wt) and not force:
        click.echo(
            f"Error: Uncommitted changes in source worktree '{source_wt.name}'.\n"
            f"Commit, stash, or use --force to override.",
            err=True,
        )
        raise SystemExit(1)

    target_exists = target_wt.exists()

    if target_exists:
        # Target exists - check for uncommitted changes
        if _has_uncommitted_changes(target_wt) and not force:
            click.echo(
                f"Error: Uncommitted changes in target worktree '{target_wt.name}'.\n"
                f"Commit, stash, or use --force to override.",
                err=True,
            )
            raise SystemExit(1)

        # Checkout branch in target
        click.echo(f"Checking out '{source_branch}' in '{target_wt.name}'")
        ctx.git_ops.checkout_branch(target_wt, source_branch)
    else:
        # Create new worktree with branch
        click.echo(f"Creating worktree '{target_wt.name}' with branch '{source_branch}'")
        ctx.git_ops.add_worktree(
            repo_root, target_wt, branch=source_branch, ref=None, create_branch=False
        )

    # Switch source to fallback branch
    click.echo(f"Checking out '{fallback_ref}' in '{source_wt.name}'")
    ctx.git_ops.checkout_branch(source_wt, fallback_ref)

    click.echo(f"✓ Moved '{source_branch}' from '{source_wt.name}' to '{target_wt.name}'")


def execute_swap(
    ctx: WorkstackContext,
    repo_root: Path,
    source_wt: Path,
    target_wt: Path,
    *,
    force: bool,
) -> None:
    """Execute swap operation (both worktrees exist with branches).

    Swaps the branches between source and target worktrees.
    """
    source_branch = _get_worktree_branch(ctx, repo_root, source_wt)
    target_branch = _get_worktree_branch(ctx, repo_root, target_wt)

    if source_branch is None or target_branch is None:
        click.echo("Error: Both worktrees must have branches checked out for swap", err=True)
        raise SystemExit(1)

    # Check for uncommitted changes
    if _has_uncommitted_changes(source_wt) or _has_uncommitted_changes(target_wt):
        if not force:
            click.echo(
                "Error: Uncommitted changes detected in one or more worktrees.\n"
                "Commit, stash, or use --force to override.",
                err=True,
            )
            raise SystemExit(1)

    # Confirm swap unless --force
    if not force:
        click.echo("This will swap branches between worktrees:")
        click.echo(f"  '{source_wt.name}': '{source_branch}' → '{target_branch}'")
        click.echo(f"  '{target_wt.name}': '{target_branch}' → '{source_branch}'")
        if not click.confirm("Continue?"):
            click.echo("Swap cancelled")
            raise SystemExit(0)

    click.echo(f"Swapping branches between '{source_wt.name}' and '{target_wt.name}'")

    # Git allows checking out a branch in one worktree even if it's checked out in another,
    # as long as we do it in the right order. First checkout target's branch in source,
    # then source's original branch becomes available for target.
    ctx.git_ops.checkout_branch(source_wt, target_branch)
    ctx.git_ops.checkout_branch(target_wt, source_branch)

    click.echo(f"✓ Swapped '{source_branch}' ↔ '{target_branch}'")


@click.command("move")
@click.option("--current", is_flag=True, help="Use current worktree as source")
@click.option("--branch", help="Auto-detect worktree containing this branch")
@click.option("--worktree", help="Use specific worktree as source")
@click.option("--ref", default="main", help="Fallback branch for source after move (default: main)")
@click.option("-f", "--force", is_flag=True, help="Skip confirmation prompts")
@click.argument("target", required=True, shell_complete=complete_worktree_names)
@click.pass_obj
def move_cmd(
    ctx: WorkstackContext,
    current: bool,
    branch: str | None,
    worktree: str | None,
    ref: str,
    force: bool,
    target: str,
) -> None:
    """Move branches between worktrees with explicit source specification.

    Examples:

        \b
        # Move from current worktree to new worktree
        workstack move target-wt

        \b
        # Move from current worktree (explicit)
        workstack move --current target-wt

        \b
        # Auto-detect source from branch name
        workstack move --branch feature-x new-wt

        \b
        # Move from specific source to target
        workstack move --worktree old-wt new-wt

        \b
        # Swap branches between current and another worktree
        workstack move --current existing-wt

        \b
        # Force operation without prompts (for scripts)
        workstack move --current target-wt --force

        \b
        # Specify custom fallback branch
        workstack move --current new-wt --ref develop
    """
    # Discover repository context
    repo = discover_repo_context(ctx, Path.cwd())
    work_dir = ensure_work_dir(repo)

    # Resolve source worktree
    source_wt = resolve_source_worktree(
        ctx, repo.root, current=current, branch=branch, worktree=worktree, work_dir=work_dir
    )

    # Resolve target worktree path
    target_wt = worktree_path_for(work_dir, target)

    # Validate source and target are different
    if source_wt.resolve() == target_wt.resolve():
        click.echo("Error: Source and target worktrees are the same", err=True)
        raise SystemExit(1)

    # Detect operation type
    operation_type = detect_operation_type(source_wt, target_wt, ctx, repo.root)

    # Execute operation
    if operation_type == "swap":
        execute_swap(ctx, repo.root, source_wt, target_wt, force=force)
    else:
        # Auto-detect default branch if using 'main' default and it doesn't exist
        if ref == "main":
            detected_default = ctx.git_ops.detect_default_branch(repo.root)
            ref = detected_default

        execute_move(ctx, repo.root, source_wt, target_wt, ref, force=force)
