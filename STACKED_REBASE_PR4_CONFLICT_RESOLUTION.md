# PR 4: Conflict Resolution System

## Overview

This PR completes the core rebase workflow by adding interactive conflict resolution and the ability to apply completed rebase stacks to actual branches.

**Status**: Planning Complete
**Timeline**: Week 4-5 (5 working days)
**Dependencies**: [PR 1](STACKED_REBASE_PR1_GIT_OPERATIONS.md), [PR 2](STACKED_REBASE_PR2_STACK_MANAGER.md), [PR 3](STACKED_REBASE_PR3_BASIC_CLI.md)
**Next PR**: [PR 5: Testing & Validation](STACKED_REBASE_PR5_TESTING.md)

## Goals

1. Implement `workstack rebase resolve` command
2. Interactive conflict resolution in stacks
3. Implement `workstack rebase apply` command
4. Complete the full rebase workflow
5. Add safety checks before applying

## Files to Create

- `src/workstack/core/conflict_resolver.py` - Conflict resolution logic
- `tests/core/test_conflict_resolver.py` - Resolution tests

## Files to Modify

- `src/workstack/cli/commands/rebase.py` - Add resolve and apply commands
- `tests/cli/commands/test_rebase.py` - Add E2E tests

## New Commands

```bash
workstack rebase resolve [BRANCH] [--auto] [--editor EDITOR]
workstack rebase apply [BRANCH] [--force]
workstack rebase compare [BRANCH]
```

## Implementation Details

### 1. Conflict Resolver Module

```python
"""Conflict resolution for rebase stacks."""

from dataclasses import dataclass
from pathlib import Path

import click

from workstack.core.gitops import GitOps
from workstack.core.rebase_utils import ConflictInfo, parse_conflict_markers


@dataclass(frozen=True)
class Resolution:
    """Represents a conflict resolution choice."""

    file_path: str
    strategy: str  # "ours", "theirs", "manual"
    resolved_content: str | None  # For manual resolutions


class ConflictResolver:
    """Interactive conflict resolution for rebase stacks."""

    def __init__(self, git_ops: GitOps) -> None:
        self.git_ops = git_ops

    def resolve_interactively(
        self,
        stack_path: Path,
        conflicts: list[str],
    ) -> list[Resolution]:
        """Resolve conflicts interactively.

        Args:
            stack_path: Path to rebase stack
            conflicts: List of conflicted file paths

        Returns:
            List of resolutions applied
        """
        resolutions = []

        for file_path in conflicts:
            full_path = stack_path / file_path
            content = full_path.read_text(encoding="utf-8")

            conflict_info = parse_conflict_markers(content)

            click.echo(f"\nConflict in: {click.style(file_path, fg='cyan', bold=True)}")
            click.echo(f"Number of conflict regions: {len(conflict_info)}")

            choice = self._prompt_resolution_strategy(file_path)

            if choice == "ours":
                resolved = self._resolve_keep_ours(content)
                resolutions.append(Resolution(file_path, "ours", resolved))
            elif choice == "theirs":
                resolved = self._resolve_keep_theirs(content)
                resolutions.append(Resolution(file_path, "theirs", resolved))
            elif choice == "manual":
                self._open_in_editor(full_path)
                # Verify resolution
                if self._check_resolution_complete(full_path):
                    resolutions.append(Resolution(file_path, "manual", None))
                else:
                    click.echo("  Warning: Conflict markers still present", err=True)

        return resolutions

    def apply_resolution(
        self,
        stack_path: Path,
        resolution: Resolution,
    ) -> None:
        """Apply a resolution to a file."""
        if resolution.resolved_content is not None:
            file_path = stack_path / resolution.file_path
            file_path.write_text(resolution.resolved_content, encoding="utf-8")

        # Stage the resolved file
        import subprocess

        subprocess.run(
            ["git", "add", resolution.file_path],
            cwd=stack_path,
            check=True,
            capture_output=True,
        )

    def _prompt_resolution_strategy(self, file_path: str) -> str:
        """Prompt user for resolution strategy."""
        click.echo("\nResolution options:")
        click.echo("  1. Keep ours (discard their changes)")
        click.echo("  2. Keep theirs (discard our changes)")
        click.echo("  3. Manual (open in editor)")
        click.echo("  4. Skip for now")

        choice = click.prompt(
            "Choose resolution strategy",
            type=click.Choice(["1", "2", "3", "4"]),
            default="3",
        )

        mapping = {"1": "ours", "2": "theirs", "3": "manual", "4": "skip"}
        return mapping[choice]

    def _resolve_keep_ours(self, content: str) -> str:
        """Resolve by keeping 'ours' version."""
        lines = content.split("\n")
        result = []
        in_conflict = False
        in_ours = False

        for line in lines:
            if line.startswith("<<<<<<<"):
                in_conflict = True
                in_ours = True
                continue
            elif line.startswith("======="):
                in_ours = False
                continue
            elif line.startswith(">>>>>>>"):
                in_conflict = False
                in_ours = False
                continue

            if not in_conflict:
                result.append(line)
            elif in_ours:
                result.append(line)

        return "\n".join(result)

    def _resolve_keep_theirs(self, content: str) -> str:
        """Resolve by keeping 'theirs' version."""
        lines = content.split("\n")
        result = []
        in_conflict = False
        in_theirs = False

        for line in lines:
            if line.startswith("<<<<<<<"):
                in_conflict = True
                continue
            elif line.startswith("======="):
                in_theirs = True
                continue
            elif line.startswith(">>>>>>>"):
                in_conflict = False
                in_theirs = False
                continue

            if not in_conflict:
                result.append(line)
            elif in_theirs:
                result.append(line)

        return "\n".join(result)

    def _open_in_editor(self, file_path: Path) -> None:
        """Open file in configured editor."""
        import os
        import subprocess

        editor = os.environ.get("EDITOR", "vim")

        try:
            subprocess.run([editor, str(file_path)], check=True)
        except subprocess.CalledProcessError:
            click.echo(f"  Error opening editor: {editor}", err=True)

    def _check_resolution_complete(self, file_path: Path) -> bool:
        """Check if all conflict markers are resolved."""
        content = file_path.read_text(encoding="utf-8")
        markers = ["<<<<<<<", "=======", ">>>>>>>"]
        return not any(marker in content for marker in markers)
```

### 2. CLI Commands

Add to `src/workstack/cli/commands/rebase.py`:

```python
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
    from pathlib import Path

    from workstack.core.conflict_resolver import ConflictResolver

    repo = discover_repo_context(ctx, Path.cwd())

    if branch is None:
        branch = ctx.git_ops.get_current_branch(Path.cwd())
        if branch is None:
            click.echo("Error: Not on a branch. Specify branch name.", err=True)
            raise SystemExit(1)

    stack_ops = RebaseStackOps(ctx.git_ops)

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
    from pathlib import Path

    repo = discover_repo_context(ctx, Path.cwd())

    if branch is None:
        branch = ctx.git_ops.get_current_branch(Path.cwd())
        if branch is None:
            click.echo("Error: Not on a branch. Specify branch name.", err=True)
            raise SystemExit(1)

    stack_ops = RebaseStackOps(ctx.git_ops)

    if not stack_ops.stack_exists(repo.root, branch):
        click.echo(f"No rebase stack to apply for {branch}", err=True)
        raise SystemExit(1)

    stack_path = stack_ops.get_stack_path(repo.root, branch)

    # Pre-flight checks
    if not force:
        click.echo("Running pre-flight checks...")

        # Check stack is clean
        if not ctx.git_ops.check_clean_worktree(stack_path):
            click.echo("Error: Rebase stack has uncommitted changes", err=True)
            raise SystemExit(1)

        # Check target branch is clean
        # Get worktree for branch
        worktrees = ctx.git_ops.list_worktrees(repo.root)
        branch_worktree = None
        for wt in worktrees:
            if wt.branch == branch and wt.path != stack_path:
                branch_worktree = wt.path
                break

        if branch_worktree and not ctx.git_ops.check_clean_worktree(branch_worktree):
            click.echo(
                f"Error: Target branch {branch} has uncommitted changes",
                err=True,
            )
            raise SystemExit(1)

        # Check no rebase in progress
        rebase_status = ctx.git_ops.get_rebase_status(stack_path)
        if rebase_status.get("in_progress"):
            click.echo("Error: Rebase still in progress. Resolve conflicts first.", err=True)
            raise SystemExit(1)

        click.echo("✓ Pre-flight checks passed\n")

    # Apply the rebase
    click.echo(f"Applying rebase stack to {branch}...")

    # Get the stack's current commit
    import subprocess

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=stack_path,
        capture_output=True,
        text=True,
        check=True,
    )
    stack_commit = result.stdout.strip()

    # Update the branch ref to point to stack's commit
    subprocess.run(
        ["git", "branch", "-f", branch, stack_commit],
        cwd=repo.root,
        check=True,
        capture_output=True,
    )

    click.echo(click.style("✓ Rebase applied successfully!", fg="green", bold=True))

    # Cleanup stack
    stack_ops.update_stack_state(stack_path, StackState.APPLIED)
    stack_ops.cleanup_stack(repo.root, branch)

    click.echo(f"Rebase stack cleaned up")
    click.echo(f"\n{branch} has been rebased successfully")


@rebase_group.command("compare")
@click.argument("branch", required=False)
@click.pass_obj
def compare_cmd(ctx: WorkstackContext, branch: str | None) -> None:
    """Compare current branch with rebase stack.

    Shows the diff between your actual branch and the rebased version
    in the stack.
    """
    from pathlib import Path

    repo = discover_repo_context(ctx, Path.cwd())

    if branch is None:
        branch = ctx.git_ops.get_current_branch(Path.cwd())
        if branch is None:
            click.echo("Error: Not on a branch. Specify branch name.", err=True)
            raise SystemExit(1)

    stack_ops = RebaseStackOps(ctx.git_ops)

    if not stack_ops.stack_exists(repo.root, branch):
        click.echo(f"No rebase stack for {branch}", err=True)
        raise SystemExit(1)

    stack_path = stack_ops.get_stack_path(repo.root, branch)

    # Get commits
    import subprocess

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
```

## Testing Strategy

E2E tests covering:

- Resolving conflicts with different strategies
- Applying clean rebases
- Applying after conflict resolution
- Pre-flight check failures
- Comparing before/after

## Acceptance Criteria

- [ ] Interactive conflict resolution works
- [ ] Apply command updates actual branch
- [ ] Pre-flight checks prevent unsafe applies
- [ ] Compare shows diffs accurately
- [ ] Error handling is robust
- [ ] E2E tests cover all scenarios
- [ ] Test coverage ≥90%

## References

- [Master Plan](STACKED_REBASE_MASTER_PLAN.md)
- [Previous: PR 3](STACKED_REBASE_PR3_BASIC_CLI.md)
- [Next: PR 5](STACKED_REBASE_PR5_TESTING.md)
