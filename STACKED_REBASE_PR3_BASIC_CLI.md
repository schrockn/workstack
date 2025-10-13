# PR 3: Basic CLI with Preview

## Overview

This PR implements the first user-facing feature: the ability to preview rebases safely in rebase stacks before applying them.

**Status**: Planning Complete
**Timeline**: Week 3-4 (5 working days)
**Dependencies**: [PR 1](STACKED_REBASE_PR1_GIT_OPERATIONS.md), [PR 2](STACKED_REBASE_PR2_STACK_MANAGER.md)
**Next PR**: [PR 4: Conflict Resolution](STACKED_REBASE_PR4_CONFLICT_RESOLUTION.md)

## Goals

1. Implement `workstack rebase preview` command
2. Create and preview rebase stacks
3. Show conflicts without resolving them
4. Provide `rebase status` and `rebase abort` commands
5. Deliver first complete user workflow

## Non-Goals

- No conflict resolution yet (PR 4)
- No testing in stacks (PR 5)
- No configuration system (PR 6)
- No interactive mode (PR 6)

## Files to Create

- `src/workstack/cli/commands/rebase.py` - Main rebase CLI command
- `tests/cli/commands/test_rebase.py` - CLI E2E tests

## Files to Modify

- `src/workstack/cli/cli.py` - Register rebase command group

## Command Structure

```bash
workstack rebase preview [BRANCH] [--onto TARGET]
workstack rebase status [BRANCH]
workstack rebase abort [BRANCH]
```

## Implementation Details

### 1. CLI Command Structure

```python
"""Rebase command for safe, stacked rebasing."""

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
    from pathlib import Path

    # Discover repo and determine branch
    repo = discover_repo_context(ctx, Path.cwd())

    if branch is None:
        branch = ctx.git_ops.get_current_branch(Path.cwd())
        if branch is None:
            click.echo("Error: Not on a branch. Specify branch name.", err=True)
            raise SystemExit(1)

    # Determine target branch
    if onto is None:
        # TODO: Detect parent from Graphite or config
        onto = ctx.git_ops.detect_default_branch(repo.root)

    click.echo(f"Creating rebase stack for {branch}...")

    # Create stack
    stack_ops = RebaseStackOps(ctx.git_ops)

    if stack_ops.stack_exists(repo.root, branch):
        click.echo(
            f"Warning: Rebase stack already exists for {branch}. Recreating...",
            err=True,
        )

    stack_path = stack_ops.create_stack(repo.root, branch, onto)
    click.echo(f"Rebase stack created at: {stack_path}")

    # Create rebase plan
    plan = create_rebase_plan(ctx.git_ops, stack_path, branch, onto)
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
    from pathlib import Path

    repo = discover_repo_context(ctx, Path.cwd())
    stack_ops = RebaseStackOps(ctx.git_ops)

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


@rebase_group.command("abort")
@click.argument("branch", required=False)
@click.pass_obj
def abort_cmd(ctx: WorkstackContext, branch: str | None) -> None:
    """Abort and clean up a rebase stack.

    Removes the rebase stack without modifying your actual branch.
    """
    from pathlib import Path

    repo = discover_repo_context(ctx, Path.cwd())
    stack_ops = RebaseStackOps(ctx.git_ops)

    if branch is None:
        branch = ctx.git_ops.get_current_branch(Path.cwd())
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
    plan,
    success: bool,
    conflicts: list[str],
) -> None:
    """Display rebase preview results."""
    click.echo("\n" + "=" * 50)
    click.echo("REBASE STACK PREVIEW")
    click.echo("=" * 50 + "\n")

    if success:
        click.echo(click.style("✓ Rebase completed cleanly", fg="green", bold=True))
        click.echo(f"  All {len(plan.commits_to_rebase)} commits applied successfully")
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


def _display_stack_info(info) -> None:
    """Display information about a rebase stack."""
    branch_str = click.style(info.branch_name, fg="cyan", bold=True)
    state_color = _get_state_color(info.state)
    state_str = click.style(info.state.value, fg=state_color)

    click.echo(f"{branch_str} - {state_str}")
    click.echo(f"  Target: {info.target_branch}")
    click.echo(f"  Created: {info.created_at.strftime('%Y-%m-%d %H:%M')}")

    if info.conflicts:
        click.echo(f"  Conflicts: {len(info.conflicts)} file(s)")


def _get_state_color(state: StackState) -> str:
    """Get color for stack state."""
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
```

### 2. Register Command

Update `src/workstack/cli/cli.py`:

```python
from workstack.cli.commands.rebase import rebase_group

# ... existing imports ...

# Register commands
cli.add_command(rebase_group)  # Add this line
```

## Testing Strategy

### E2E Tests

Create `tests/cli/commands/test_rebase.py`:

```python
"""E2E tests for rebase commands."""

from pathlib import Path

import pytest


def test_rebase_preview_clean(cli_runner, test_repo_with_branches):
    """Test preview with no conflicts."""
    result = cli_runner.invoke(["rebase", "preview", "feature"])

    assert result.exit_code == 0
    assert "Rebase completed cleanly" in result.output
    assert "workstack rebase apply" in result.output


def test_rebase_preview_with_conflicts(cli_runner, test_repo_with_conflicts):
    """Test preview with conflicts."""
    result = cli_runner.invoke(["rebase", "preview", "feature"])

    assert result.exit_code == 0
    assert "Conflicts detected" in result.output
    assert "workstack rebase resolve" in result.output


def test_rebase_status_no_stacks(cli_runner, test_repo):
    """Test status when no stacks exist."""
    result = cli_runner.invoke(["rebase", "status"])

    assert result.exit_code == 0
    assert "No active rebase stacks" in result.output


def test_rebase_status_with_stacks(cli_runner, test_repo_with_stack):
    """Test status with active stacks."""
    result = cli_runner.invoke(["rebase", "status"])

    assert result.exit_code == 0
    assert "feature" in result.output


def test_rebase_abort(cli_runner, test_repo_with_stack):
    """Test aborting a rebase stack."""
    result = cli_runner.invoke(["rebase", "abort", "feature"])

    assert result.exit_code == 0
    assert "cleaned up" in result.output

    # Verify stack is gone
    result = cli_runner.invoke(["rebase", "status"])
    assert "No active rebase stacks" in result.output


def test_rebase_preview_current_branch(cli_runner, test_repo):
    """Test preview without branch argument uses current branch."""
    # Setup: checkout feature branch
    # ...

    result = cli_runner.invoke(["rebase", "preview"])

    assert result.exit_code == 0
    assert "feature" in result.output
```

## User Documentation

Example user workflow:

```bash
# Preview a rebase to see if there are conflicts
$ workstack rebase preview feature-auth
Creating rebase stack for feature-auth...
Rebase stack created at: /path/to/.rebase-stack-feature-auth

Previewing rebase of feature-auth onto main...
Commits to rebase: 5

==================================================
REBASE STACK PREVIEW
==================================================

⚠ Conflicts detected: 2 file(s)

Conflicted files:
  • src/auth/service.ts
  • tests/auth.test.ts

Next steps:
  • workstack rebase resolve feature-auth  (resolve conflicts)
  • workstack rebase abort feature-auth     (discard stack)

# Check status of all stacks
$ workstack rebase status
Active rebase stacks: 1

feature-auth - conflicted
  Target: main
  Created: 2025-10-12 14:30
  Conflicts: 2 file(s)

# Abort the stack
$ workstack rebase abort feature-auth
Aborting rebase stack for feature-auth...
Rebase stack cleaned up successfully
```

## Acceptance Criteria

- [ ] `rebase preview` creates stack and shows results
- [ ] Preview displays conflicts clearly
- [ ] Preview suggests next steps
- [ ] `rebase status` shows all active stacks
- [ ] `rebase status BRANCH` shows specific stack
- [ ] `rebase abort` removes stack completely
- [ ] Commands work without branch argument (use current)
- [ ] Error messages are clear and helpful
- [ ] E2E tests cover all command paths
- [ ] Test coverage ≥90%
- [ ] User documentation complete
- [ ] Pyright passes
- [ ] All existing tests pass

## Migration Notes

This PR adds new commands. No breaking changes to existing functionality.

## Next Steps

After this PR:

1. Users can safely preview rebases
2. PR 4 will add conflict resolution
3. PR 4 will add apply functionality

## References

- [Master Plan](STACKED_REBASE_MASTER_PLAN.md)
- [Previous: PR 2](STACKED_REBASE_PR2_STACK_MANAGER.md)
- [Next: PR 4](STACKED_REBASE_PR4_CONFLICT_RESOLUTION.md)
