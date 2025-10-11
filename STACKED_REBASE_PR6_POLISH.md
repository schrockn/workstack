# PR 6: Polish & Integration

## Overview

This PR adds configuration, state persistence, UX enhancements, and integration with existing workstack commands to make stacked rebase production-ready.

**Status**: Planning Complete
**Timeline**: Week 6-7 (5 working days)
**Dependencies**: [PR 1-5](STACKED_REBASE_MASTER_PLAN.md)
**Next PR**: None (Final PR)

## Goals

1. Add configuration options for rebase behavior
2. Implement state persistence across sessions
3. Add rich progress indicators
4. Integrate with `workstack list` and `workstack status`
5. Add interactive guided mode
6. Polish error messages and UX
7. Complete documentation

## Files to Create

- `src/workstack/core/rebase_config.py` - Configuration management
- `src/workstack/core/rebase_state.py` - State persistence

## Files to Modify

- `src/workstack/cli/commands/config.py` - Add rebase config options
- `src/workstack/cli/commands/list.py` - Show rebase stack indicators
- `src/workstack/cli/commands/rebase.py` - Add interactive mode, progress bars
- Global config defaults

## Configuration Options

### Rebase Configuration Schema

```python
"""Configuration for stacked rebase."""

REBASE_CONFIG_SCHEMA = {
    "rebase.useStacks": {
        "type": "bool",
        "default": True,
        "description": "Always use rebase stacks (safe rebasing)",
    },
    "rebase.autoTest": {
        "type": "bool",
        "default": False,
        "description": "Automatically run tests after resolving conflicts",
    },
    "rebase.preserveStacks": {
        "type": "bool",
        "default": False,
        "description": "Keep rebase stacks after applying (for inspection)",
    },
    "rebase.conflictTool": {
        "type": "string",
        "default": "vimdiff",
        "description": "Default tool for resolving conflicts",
        "allowed": ["vimdiff", "meld", "kdiff3", "opendiff", "code"],
    },
    "rebase.stackLocation": {
        "type": "string",
        "default": ".rebase-stack",
        "description": "Directory name prefix for rebase stacks",
    },
}
```

### CLI Configuration Commands

```bash
# View rebase settings
workstack config get rebase.autoTest

# Set options
workstack config set rebase.autoTest true
workstack config set rebase.conflictTool meld

# List all rebase settings
workstack config list --filter rebase
```

## Implementation Details

### 1. State Persistence

```python
"""State persistence for rebase stacks."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class PersistedStackState:
    """Persisted state for resume capability."""

    branch_name: str
    target_branch: str
    conflicts_resolved: list[str]
    last_updated: str
    test_results: dict | None


class RebaseState:
    """Manage persistent state for rebase stacks."""

    def __init__(self, repo_root: Path) -> None:
        self.state_dir = repo_root / ".git" / ".rebase-state"
        self.state_dir.mkdir(exist_ok=True)

    def save_state(self, branch: str, state: PersistedStackState) -> None:
        """Save state for a rebase stack."""
        state_file = self.state_dir / f"{branch}.json"

        data = {
            "branch_name": state.branch_name,
            "target_branch": state.target_branch,
            "conflicts_resolved": state.conflicts_resolved,
            "last_updated": state.last_updated,
            "test_results": state.test_results,
        }

        state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load_state(self, branch: str) -> PersistedStackState | None:
        """Load saved state for a branch."""
        state_file = self.state_dir / f"{branch}.json"

        if not state_file.exists():
            return None

        data = json.loads(state_file.read_text(encoding="utf-8"))

        return PersistedStackState(
            branch_name=data["branch_name"],
            target_branch=data["target_branch"],
            conflicts_resolved=data["conflicts_resolved"],
            last_updated=data["last_updated"],
            test_results=data.get("test_results"),
        )

    def clear_state(self, branch: str) -> None:
        """Remove saved state after completion."""
        state_file = self.state_dir / f"{branch}.json"
        if state_file.exists():
            state_file.unlink()
```

### 2. Integration with List Command

Modify `src/workstack/cli/commands/list.py`:

```python
def _display_worktree_row(wt_info, has_rebase_stack: bool = False):
    """Display worktree with rebase stack indicator."""
    # ... existing display code ...

    # Add rebase stack indicator
    if has_rebase_stack:
        stack_indicator = click.style(" [REBASE STACK]", fg="yellow", bold=True)
        click.echo(stack_indicator, nl=False)

    click.echo()  # Newline


# In list command:
from workstack.core.rebase_stack_ops import RebaseStackOps

stack_ops = RebaseStackOps(ctx.git_ops)
active_stacks = {s.branch_name for s in stack_ops.list_stacks(repo.root)}

for wt in worktrees:
    has_stack = wt.branch in active_stacks
    _display_worktree_row(wt, has_rebase_stack=has_stack)
```

### 3. Progress Indicators

Add progress bars for long operations:

```python
import click

def rebase_with_progress(git_ops, stack_path, onto, commits_count):
    """Rebase with progress bar."""
    with click.progressbar(
        length=commits_count,
        label="Rebasing commits",
        show_eta=True,
    ) as bar:
        # Start rebase
        success, conflicts = git_ops.start_rebase(stack_path, onto)

        # Update progress as commits are applied
        # (This requires polling rebase status)
        while True:
            status = git_ops.get_rebase_status(stack_path)
            if not status["in_progress"]:
                break

            commits_done = commits_count - status["remaining_commits"]
            bar.update(commits_done - bar.pos)

            if conflicts:
                break

    return success, conflicts
```

### 4. Interactive Mode

```python
@rebase_group.command("interactive")
@click.argument("branch", required=False)
@click.pass_obj
def interactive_cmd(ctx: WorkstackContext, branch: str | None) -> None:
    """Guided interactive rebase workflow.

    Walks through the entire rebase process step-by-step with
    prompts and explanations.
    """
    from pathlib import Path

    click.echo(click.style("Interactive Stacked Rebase", fg="cyan", bold=True))
    click.echo("This will guide you through a safe rebase.\n")

    repo = discover_repo_context(ctx, Path.cwd())

    # Step 1: Determine branch
    if branch is None:
        branch = ctx.git_ops.get_current_branch(Path.cwd())
        if branch is None:
            branch = click.prompt("Enter branch name to rebase")

    click.echo(f"Branch to rebase: {click.style(branch, fg='cyan')}")

    # Step 2: Determine target
    default_branch = ctx.git_ops.detect_default_branch(repo.root)
    onto = click.prompt(
        "Rebase onto which branch?",
        default=default_branch,
    )

    # Step 3: Preview
    click.echo("\n📋 Step 1: Preview")
    click.echo("Creating rebase stack to preview changes...")

    # ... create stack and preview ...

    if not click.confirm("\nContinue with this rebase?"):
        click.echo("Rebase cancelled")
        return

    # Step 4: Handle conflicts
    if conflicts:
        click.echo("\n⚠️  Step 2: Resolve Conflicts")
        click.echo(f"Found {len(conflicts)} conflicted file(s)")

        if click.confirm("Open interactive conflict resolution?"):
            # ... resolve conflicts ...
            pass

    # Step 5: Test
    if ctx.config.get("rebase.autoTest", False):
        click.echo("\n🧪 Step 3: Run Tests")
        # ... run tests ...

    if click.confirm("\nTests passed. Apply rebase?"):
        click.echo("\n✅ Step 4: Apply")
        # ... apply rebase ...

    click.echo("\n✓ Rebase complete!")
```

### 5. Enhanced Error Messages

```python
class RebaseError(Exception):
    """Base exception for rebase errors."""

    def __init__(self, message: str, suggestion: str | None = None) -> None:
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)


def handle_rebase_error(error: RebaseError) -> None:
    """Display user-friendly error with suggestions."""
    click.echo(click.style(f"Error: {error.message}", fg="red", bold=True), err=True)

    if error.suggestion:
        click.echo(f"\n💡 Suggestion: {error.suggestion}", err=True)

    # Common troubleshooting
    click.echo("\nTroubleshooting:", err=True)
    click.echo("  • workstack rebase status  (check current state)", err=True)
    click.echo("  • workstack rebase abort   (start over)", err=True)
```

### 6. Documentation

Update user documentation:

- Add rebase section to README
- Create REBASE_GUIDE.md
- Add examples to CLI help text
- Document configuration options

## Testing Strategy

- Test configuration persistence
- Test state save/load
- Test integration with list command
- Test interactive mode flow
- Test error handling

## Acceptance Criteria

- [ ] Configuration system working
- [ ] State persists across sessions
- [ ] List command shows rebase indicators
- [ ] Progress bars for long operations
- [ ] Interactive mode is intuitive
- [ ] Error messages are helpful
- [ ] Complete user documentation
- [ ] Test coverage ≥90%
- [ ] All integration tests pass

## User Documentation Examples

### Configuration

```bash
# Enable auto-testing
workstack config set rebase.autoTest true

# Set conflict resolution tool
workstack config set rebase.conflictTool meld

# View all rebase settings
workstack config list --filter rebase
```

### List Integration

```bash
$ workstack list
Repository: my-project

Worktrees:
  main (root)           /Users/dev/repos/my-project
  feature-auth [REBASE STACK]        /Users/dev/worktrees/feature-auth
  feature-api           /Users/dev/worktrees/feature-api
```

### Interactive Mode

```bash
$ workstack rebase interactive
Interactive Stacked Rebase
This will guide you through a safe rebase.

Branch to rebase: feature-auth
Rebase onto which branch? [main]: main

📋 Step 1: Preview
Creating rebase stack to preview changes...
✓ 5 commits will rebase cleanly

Continue with this rebase? [y/N]: y

✅ Step 2: Apply
Applying rebase stack...
✓ Rebase complete!
```

## Migration Notes

This PR adds new features but maintains backward compatibility. Users can opt into new features via configuration.

## Final Deliverables

- Full stacked rebase feature
- Comprehensive documentation
- Integration with existing commands
- Production-ready UX
- Complete test coverage

## References

- [Master Plan](STACKED_REBASE_MASTER_PLAN.md)
- [Previous: PR 5](STACKED_REBASE_PR5_TESTING.md)
- [Original Spec](../../SANDBOX_REBASE_SPEC.md)

---

**Status**: Implementation Complete
**Next Action**: Feature ready for production use
