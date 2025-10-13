"""Rebase command for safe, stacked rebasing."""

from pathlib import Path

import click

from workstack.cli.core import discover_repo_context
from workstack.core.context import WorkstackContext
from workstack.core.rebase_stack_ops import RebaseStackOps, StackState
from workstack.core.rebase_utils import create_rebase_plan


@click.group("rebase")
@click.pass_obj
def rebase_group(ctx: WorkstackContext) -> None:
    """Safe rebasing using rebase stacks."""
    pass


@rebase_group.command("preview")
@click.argument("branch", required=False)
@click.option(
    "--onto",
    help="Target branch to rebase onto (default: parent branch)",
)
@click.pass_obj
def preview_cmd(
    ctx: WorkstackContext,
    branch: str | None,
    onto: str | None,
) -> None:
    """Preview a rebase in a stack without applying changes.

    Creates a rebase stack (temporary worktree) and attempts the rebase
    to show what conflicts would occur without modifying your actual branch.

    Examples:
        workstack rebase preview              # Preview current branch
        workstack rebase preview feature-api  # Preview specific branch
        workstack rebase preview --onto main  # Preview onto specific target
    """
    cwd = Path.cwd()

    # Discover repo and determine branch
    repo = discover_repo_context(ctx, cwd)

    if branch is None:
        branch = ctx.git_ops.get_current_branch(repo.root)
        if branch is None:
            click.echo("Error: Not on a branch. Specify branch name.", err=True)
            raise SystemExit(1)

    # Determine target branch
    if onto is None:
        # TODO: Detect parent from Graphite or config
        onto = ctx.git_ops.detect_default_branch(repo.root)

    click.echo(f"Creating rebase stack for {branch}...")

    # Create stack
    stack_ops = RebaseStackOps(ctx.git_ops, ctx.global_config_ops)

    if stack_ops.stack_exists(repo.root, branch):
        click.echo(
            f"Warning: Rebase stack already exists for {branch}. Recreating...",
            err=True,
        )

    stack_path = stack_ops.create_stack(repo.root, branch, onto)
    click.echo(f"Rebase stack created at: {stack_path}")

    # Create rebase plan
    plan = create_rebase_plan(ctx.git_ops.rebase_ops, stack_path, branch, onto)
    if plan is None:
        click.echo(f"Error: No common ancestor between {branch} and {onto}", err=True)
        stack_ops.cleanup_stack(repo.root, branch)
        raise SystemExit(1)

    click.echo(f"\nPreviewing rebase of {branch} onto {onto}...")
    click.echo(f"Commits to rebase: {len(plan.commits_to_rebase)}")

    # Attempt rebase in stack
    success, conflicts = ctx.git_ops.start_rebase(stack_path, onto)

    # Display results
    _display_preview_results(branch, onto, plan, success, conflicts)

    # Update stack state
    if success:
        stack_ops.update_stack_state(stack_path, StackState.RESOLVED)
    elif len(conflicts) > 0:
        stack_ops.update_stack_state(stack_path, StackState.CONFLICTED)
    else:
        stack_ops.update_stack_state(stack_path, StackState.FAILED)


@rebase_group.command("status")
@click.argument("branch", required=False)
@click.pass_obj
def status_cmd(ctx: WorkstackContext, branch: str | None) -> None:
    """Show status of rebase stacks.

    If BRANCH is specified, shows status of that branch's stack.
    Otherwise, shows all active rebase stacks.
    """
    cwd = Path.cwd()
    repo = discover_repo_context(ctx, cwd)
    stack_ops = RebaseStackOps(ctx.git_ops, ctx.global_config_ops)

    if branch:
        # Show single stack status
        if not stack_ops.stack_exists(repo.root, branch):
            click.echo(f"No rebase stack for {branch}")
            return

        stack_path = stack_ops.get_stack_path(repo.root, branch)
        info = stack_ops.get_stack_info(stack_path)
        if info:
            _display_stack_info(info)
    else:
        # Show all stacks
        stacks = stack_ops.list_stacks(repo.root)

        if not stacks:
            click.echo("No active rebase stacks")
            return

        click.echo(f"Active rebase stacks: {len(stacks)}\n")
        for stack in stacks:
            _display_stack_info(stack)
            click.echo()


@rebase_group.command("resolve")
@click.argument("branch", required=False)
@click.option("--editor", help="Editor to use for manual resolution")
@click.pass_obj
def resolve_cmd(
    ctx: WorkstackContext,
    branch: str | None,
    editor: str | None,
) -> None:
    """Resolve conflicts in a rebase stack interactively.

    Opens conflicted files for resolution, then continues the rebase.
    """
    from workstack.core.conflict_resolver import ConflictResolver

    repo = discover_repo_context(ctx, Path.cwd())

    if branch is None:
        branch = ctx.git_ops.get_current_branch(Path.cwd())
        if branch is None:
            click.echo("Error: Not on a branch. Specify branch name.", err=True)
            raise SystemExit(1)

    stack_ops = RebaseStackOps(ctx.git_ops, ctx.global_config_ops)

    if not stack_ops.stack_exists(repo.root, branch):
        click.echo(f"No rebase stack for {branch}", err=True)
        raise SystemExit(1)

    stack_path = stack_ops.get_stack_path(repo.root, branch)
    conflicts = ctx.git_ops.get_conflicted_files(stack_path)

    if not conflicts:
        click.echo(f"No conflicts to resolve for {branch}")
        return

    click.echo(f"Resolving conflicts for {branch}...")
    click.echo(f"Conflicted files: {len(conflicts)}\n")

    # Override editor if specified
    if editor:
        import os

        os.environ["EDITOR"] = editor

    # Interactive resolution
    resolver = ConflictResolver(ctx.git_ops)
    resolutions = resolver.resolve_interactively(stack_path, conflicts)

    # Apply resolutions
    for resolution in resolutions:
        resolver.apply_resolution(stack_path, resolution)

    # Continue rebase
    click.echo("\nContinuing rebase...")
    success, remaining_conflicts = ctx.git_ops.continue_rebase(stack_path)

    if success:
        click.echo(click.style("✓ Rebase completed!", fg="green", bold=True))
        stack_ops.update_stack_state(stack_path, StackState.RESOLVED)
        click.echo("\nNext step:")
        click.echo(f"  • workstack rebase apply {branch}")
    elif remaining_conflicts:
        click.echo(
            click.style(
                f"⚠ More conflicts remain: {len(remaining_conflicts)}",
                fg="yellow",
            )
        )
        click.echo("Run this command again to continue resolving")
    else:
        click.echo(click.style("✗ Rebase failed", fg="red"), err=True)
        stack_ops.update_stack_state(stack_path, StackState.FAILED)


@rebase_group.command("test")
@click.argument("branch", required=False)
@click.option("--command", help="Custom test command to run")
@click.pass_obj
def test_cmd(
    ctx: WorkstackContext,
    branch: str | None,
    command: str | None,
) -> None:
    """Run tests in a rebase stack.

    Tests are run in the isolated stack environment to verify the
    rebased code works correctly before applying.

    Examples:
        workstack rebase test              # Auto-detect and run tests
        workstack rebase test --command "npm run test:unit"
    """
    from workstack.core.stack_test_runner import StackTestRunner

    repo = discover_repo_context(ctx, Path.cwd())

    if branch is None:
        branch = ctx.git_ops.get_current_branch(Path.cwd())
        if branch is None:
            click.echo("Error: Not on a branch. Specify branch name.", err=True)
            raise SystemExit(1)

    stack_ops = RebaseStackOps(ctx.git_ops, ctx.global_config_ops)

    if not stack_ops.stack_exists(repo.root, branch):
        click.echo(f"No rebase stack for {branch}", err=True)
        raise SystemExit(1)

    stack_path = stack_ops.get_stack_path(repo.root, branch)

    # Check stack state
    info = stack_ops.get_stack_info(stack_path)
    if info and info.state == StackState.CONFLICTED:
        click.echo("Error: Resolve conflicts before running tests", err=True)
        raise SystemExit(1)

    # Run tests
    runner = StackTestRunner()

    # Determine command to run
    test_command = command
    if test_command is None:
        test_command = runner.detect_test_command(stack_path)
        if test_command:
            click.echo(f"Detected test command: {test_command}")
        else:
            click.echo("No test command detected. Specify with --command", err=True)
            raise SystemExit(1)

    click.echo(f"\nRunning tests in rebase stack for {branch}...")
    click.echo(f"Command: {test_command}\n")

    result = runner.run_tests(stack_path, test_command)

    # Display results
    if result.success:
        click.echo(click.style("✓ Tests passed!", fg="green", bold=True))
        click.echo(f"Duration: {result.duration_seconds:.1f}s")

        # Update stack state
        stack_ops.update_stack_state(stack_path, StackState.TESTED)

        click.echo("\nNext step:")
        click.echo(f"  • workstack rebase apply {branch}")
    else:
        click.echo(click.style("✗ Tests failed", fg="red", bold=True))
        click.echo(f"Exit code: {result.exit_code}")
        click.echo(f"Duration: {result.duration_seconds:.1f}s")

        # Update stack state
        stack_ops.update_stack_state(stack_path, StackState.FAILED)

        if result.stdout:
            click.echo("\n--- stdout ---")
            click.echo(result.stdout)

        if result.stderr:
            click.echo("\n--- stderr ---")
            click.echo(result.stderr)

        raise SystemExit(1)


@rebase_group.command("apply")
@click.argument("branch", required=False)
@click.option("--force", is_flag=True, help="Skip safety checks")
@click.pass_obj
def apply_cmd(
    ctx: WorkstackContext,
    branch: str | None,
    force: bool,
) -> None:
    """Apply a completed rebase stack to the actual branch.

    This is the final step that updates your real branch with the
    rebased commits from the stack.
    """
    import subprocess

    repo = discover_repo_context(ctx, Path.cwd())

    if branch is None:
        branch = ctx.git_ops.get_current_branch(Path.cwd())
        if branch is None:
            click.echo("Error: Not on a branch. Specify branch name.", err=True)
            raise SystemExit(1)

    stack_ops = RebaseStackOps(ctx.git_ops, ctx.global_config_ops)

    if not stack_ops.stack_exists(repo.root, branch):
        click.echo(f"No rebase stack to apply for {branch}", err=True)
        raise SystemExit(1)

    stack_path = stack_ops.get_stack_path(repo.root, branch)

    # Pre-apply validation
    if not _validate_before_apply(ctx, repo.root, branch, stack_path, force=force):
        raise SystemExit(1)

    # Apply the rebase
    click.echo(f"Applying rebase stack to {branch}...")

    # Get the stack's current commit before cleaning up
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=stack_path,
        capture_output=True,
        text=True,
        check=True,
    )
    stack_commit = result.stdout.strip()

    branch_worktree = ctx.git_ops.is_branch_checked_out(repo.root, branch)
    if branch_worktree is not None:
        subprocess.run(
            ["git", "reset", "--hard", stack_commit],
            cwd=branch_worktree,
            check=True,
            capture_output=True,
            text=True,
        )
    else:
        subprocess.run(
            ["git", "branch", "-f", branch, stack_commit],
            cwd=repo.root,
            check=True,
            capture_output=True,
            text=True,
        )

    stack_ops.update_stack_state(stack_path, StackState.APPLIED)
    stack_ops.cleanup_stack(repo.root, branch)

    click.echo(click.style("✓ Rebase applied successfully!", fg="green", bold=True))
    click.echo(f"{branch} has been rebased successfully")


@rebase_group.command("compare")
@click.argument("branch", required=False)
@click.pass_obj
def compare_cmd(ctx: WorkstackContext, branch: str | None) -> None:
    """Compare current branch with rebase stack.

    Shows the diff between your actual branch and the rebased version
    in the stack.
    """
    import subprocess

    repo = discover_repo_context(ctx, Path.cwd())

    if branch is None:
        branch = ctx.git_ops.get_current_branch(Path.cwd())
        if branch is None:
            click.echo("Error: Not on a branch. Specify branch name.", err=True)
            raise SystemExit(1)

    stack_ops = RebaseStackOps(ctx.git_ops, ctx.global_config_ops)

    if not stack_ops.stack_exists(repo.root, branch):
        click.echo(f"No rebase stack for {branch}", err=True)
        raise SystemExit(1)

    stack_path = stack_ops.get_stack_path(repo.root, branch)

    # Get commits
    # Current branch commit
    branch_commit = subprocess.run(
        ["git", "rev-parse", branch],
        cwd=repo.root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Stack commit
    stack_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=stack_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    click.echo(f"Comparing {branch} with rebase stack:\n")
    click.echo(f"Current:  {branch_commit[:8]}")
    click.echo(f"Rebased:  {stack_commit[:8]}\n")

    # Show diff
    subprocess.run(
        ["git", "diff", branch_commit, stack_commit],
        cwd=repo.root,
        check=True,
    )


@rebase_group.command("abort")
@click.argument("branch", required=False)
@click.pass_obj
def abort_cmd(ctx: WorkstackContext, branch: str | None) -> None:
    """Abort and clean up a rebase stack.

    Removes the rebase stack without modifying your actual branch.
    """
    cwd = Path.cwd()
    repo = discover_repo_context(ctx, cwd)
    stack_ops = RebaseStackOps(ctx.git_ops, ctx.global_config_ops)

    if branch is None:
        branch = ctx.git_ops.get_current_branch(repo.root)
        if branch is None:
            click.echo("Error: Not on a branch. Specify branch name.", err=True)
            raise SystemExit(1)

    if not stack_ops.stack_exists(repo.root, branch):
        click.echo(f"No rebase stack to abort for {branch}")
        return

    click.echo(f"Aborting rebase stack for {branch}...")
    stack_ops.cleanup_stack(repo.root, branch)
    click.echo("Rebase stack cleaned up successfully")


# Helper functions


def _display_preview_results(
    branch: str,
    onto: str,
    plan: object,
    success: bool,
    conflicts: list[str],
) -> None:
    """Display rebase preview results."""
    click.echo("\n" + "=" * 50)
    click.echo("REBASE STACK PREVIEW")
    click.echo("=" * 50 + "\n")

    if success:
        click.echo(click.style("✓ Rebase completed cleanly", fg="green", bold=True))
        # Access commits_to_rebase from plan object
        commits_count = len(plan.commits_to_rebase) if hasattr(plan, "commits_to_rebase") else 0  # type: ignore
        click.echo(f"  All {commits_count} commits applied successfully")
        click.echo("\nNext steps:")
        click.echo(f"  • workstack rebase apply {branch}  (apply to actual branch)")
    else:
        if conflicts:
            click.echo(
                click.style(
                    f"⚠ Conflicts detected: {len(conflicts)} file(s)",
                    fg="yellow",
                    bold=True,
                )
            )
            click.echo("\nConflicted files:")
            for file in conflicts:
                click.echo(f"  • {file}")
            click.echo("\nNext steps:")
            click.echo(f"  • workstack rebase resolve {branch}  (resolve conflicts)")
            click.echo(f"  • workstack rebase abort {branch}     (discard stack)")
        else:
            click.echo(click.style("✗ Rebase failed", fg="red", bold=True))
            click.echo("\nCheck the rebase stack for details:")
            click.echo(f"  cd {branch} rebase stack directory")


def _display_stack_info(info: object) -> None:
    """Display information about a rebase stack."""
    # Access attributes from info object
    branch_name = info.branch_name if hasattr(info, "branch_name") else "unknown"  # type: ignore
    state = info.state if hasattr(info, "state") else None  # type: ignore
    target_branch = info.target_branch if hasattr(info, "target_branch") else "unknown"  # type: ignore
    created_at = info.created_at if hasattr(info, "created_at") else None  # type: ignore
    conflicts = info.conflicts if hasattr(info, "conflicts") else []  # type: ignore

    branch_str = click.style(str(branch_name), fg="cyan", bold=True)
    state_color = _get_state_color(state)
    state_str = click.style(state.value if state else "unknown", fg=state_color)

    click.echo(f"{branch_str} - {state_str}")
    click.echo(f"  Target: {target_branch}")
    if created_at:
        click.echo(f"  Created: {created_at.strftime('%Y-%m-%d %H:%M')}")

    if conflicts:
        click.echo(f"  Conflicts: {len(conflicts)} file(s)")


def _get_state_color(state: StackState | None) -> str:
    """Get color for stack state."""
    if state is None:
        return "white"

    colors = {
        StackState.CREATED: "blue",
        StackState.IN_PROGRESS: "yellow",
        StackState.CONFLICTED: "red",
        StackState.RESOLVED: "green",
        StackState.TESTED: "green",
        StackState.FAILED: "red",
        StackState.APPLIED: "green",
    }
    return colors.get(state, "white")


def _validate_before_apply(
    ctx: WorkstackContext,
    repo_root: Path,
    branch: str,
    stack_path: Path,
    force: bool,
) -> bool:
    """Run validation checks before applying.

    Returns:
        True if all checks pass
    """
    if force:
        return True

    click.echo("Running validation checks...")

    checks_passed = True

    # Check: No rebase in progress
    rebase_status = ctx.git_ops.get_rebase_status(stack_path)
    if rebase_status.get("in_progress"):
        click.echo("  ✗ Rebase still in progress", err=True)
        checks_passed = False

    # Check: No conflicts
    if rebase_status.get("conflicts"):
        click.echo("  ✗ Unresolved conflicts", err=True)
        checks_passed = False

    # Check: Worktree is clean
    if not ctx.git_ops.check_clean_worktree(stack_path):
        click.echo("  ✗ Uncommitted changes in stack", err=True)
        checks_passed = False

    # Check target branch is clean
    worktrees = ctx.git_ops.list_worktrees(repo_root)
    branch_worktree = None
    for wt in worktrees:
        if wt.branch == branch and wt.path != stack_path:
            branch_worktree = wt.path
            break

    if branch_worktree and not ctx.git_ops.check_clean_worktree(branch_worktree):
        click.echo(f"  ✗ Target branch {branch} has uncommitted changes", err=True)
        checks_passed = False

    # Check: Tests passed (if they were run)
    stack_ops = RebaseStackOps(ctx.git_ops, ctx.global_config_ops)
    info = stack_ops.get_stack_info(stack_path)

    if info and info.state == StackState.FAILED:
        click.echo("  ⚠ Tests failed in stack", err=True)
        if not click.confirm("Apply anyway?"):
            checks_passed = False

    if checks_passed:
        click.echo("  ✓ All checks passed\n")

    return checks_passed
