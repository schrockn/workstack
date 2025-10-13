# PR 5: Testing & Validation

## Overview

This PR adds the ability to run tests within rebase stacks before applying, ensuring rebased code works correctly.

**Status**: Planning Complete
**Timeline**: Week 5-6 (5 working days)
**Dependencies**: [PR 1-4](STACKED_REBASE_MASTER_PLAN.md)
**Next PR**: [PR 6: Polish & Integration](STACKED_REBASE_PR6_POLISH.md)

## Goals

1. Implement `workstack rebase test` command
2. Auto-detect common test commands
3. Run tests in isolated rebase stacks
4. Add pre-apply validation framework
5. Report test results clearly

## Files to Create

- `src/workstack/core/stack_test_runner.py` - Test execution in stacks
- `tests/core/test_stack_test_runner.py` - Test runner tests

## Files to Modify

- `src/workstack/cli/commands/rebase.py` - Add test command
- `tests/cli/commands/test_rebase.py` - Add E2E tests

## New Commands

```bash
workstack rebase test [BRANCH] [--command CMD]
```

## Implementation Details

### 1. Stack Test Runner

```python
"""Test runner for rebase stacks."""

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TestResult:
    """Result of running tests in a stack."""

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    command: str


class StackTestRunner:
    """Run tests in rebase stacks."""

    def detect_test_command(self, stack_path: Path) -> str | None:
        """Auto-detect test command from project files.

        Checks for:
        - package.json (npm test)
        - Makefile (make test)
        - pytest.ini / pyproject.toml (pytest)
        - cargo.toml (cargo test)
        - go.mod (go test)

        Returns:
            Detected test command or None
        """
        # Check for Node.js
        if (stack_path / "package.json").exists():
            return "npm test"

        # Check for Python
        if (stack_path / "pytest.ini").exists() or (stack_path / "pyproject.toml").exists():
            return "pytest"

        # Check for Makefile
        if (stack_path / "Makefile").exists():
            makefile = (stack_path / "Makefile").read_text(encoding="utf-8")
            if "test:" in makefile:
                return "make test"

        # Check for Rust
        if (stack_path / "Cargo.toml").exists():
            return "cargo test"

        # Check for Go
        if (stack_path / "go.mod").exists():
            return "go test ./..."

        return None

    def run_tests(
        self,
        stack_path: Path,
        command: str | None = None,
    ) -> TestResult:
        """Execute tests in the rebase stack.

        Args:
            stack_path: Path to rebase stack worktree
            command: Test command to run (auto-detected if None)

        Returns:
            TestResult with execution details
        """
        if command is None:
            command = self.detect_test_command(stack_path)
            if command is None:
                return TestResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr="No test command detected",
                    duration_seconds=0.0,
                    command="",
                )

        import time

        start_time = time.time()

        result = subprocess.run(
            command,
            shell=True,
            cwd=stack_path,
            capture_output=True,
            text=True,
            check=False,
        )

        duration = time.time() - start_time

        return TestResult(
            success=result.returncode == 0,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_seconds=duration,
            command=command,
        )
```

### 2. CLI Command

```python
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
    from pathlib import Path

    from workstack.core.stack_test_runner import StackTestRunner

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

    # Check stack state
    info = stack_ops.get_stack_info(stack_path)
    if info and info.state == StackState.CONFLICTED:
        click.echo("Error: Resolve conflicts before running tests", err=True)
        raise SystemExit(1)

    # Run tests
    runner = StackTestRunner()

    if command is None:
        detected = runner.detect_test_command(stack_path)
        if detected:
            click.echo(f"Detected test command: {detected}")
        else:
            click.echo("No test command detected. Specify with --command", err=True)
            raise SystemExit(1)

    click.echo(f"\nRunning tests in rebase stack for {branch}...")
    click.echo(f"Command: {command or detected}\n")

    result = runner.run_tests(stack_path, command)

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
```

### 3. Validation Framework

Add validation checks to apply command:

```python
def _validate_before_apply(
    ctx: WorkstackContext,
    repo_root: Path,
    branch: str,
    stack_path: Path,
    *,
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

    # Check: Tests passed (if they were run)
    stack_ops = RebaseStackOps(ctx.git_ops)
    info = stack_ops.get_stack_info(stack_path)

    if info and info.state == StackState.FAILED:
        click.echo("  ⚠ Tests failed in stack", err=True)
        if not click.confirm("Apply anyway?"):
            checks_passed = False

    if checks_passed:
        click.echo("  ✓ All checks passed\n")

    return checks_passed
```

## Testing Strategy

- Test auto-detection for different project types
- Test with passing and failing tests
- Test validation checks
- Mock subprocess for predictable tests

## Acceptance Criteria

- [ ] Auto-detects common test commands
- [ ] Runs tests in isolated stacks
- [ ] Reports results clearly
- [ ] Updates stack state based on results
- [ ] Validation framework prevents unsafe applies
- [ ] Test coverage ≥90%

## User Documentation

```bash
# Run tests in rebase stack
$ workstack rebase test feature-auth
Detected test command: npm test

Running tests in rebase stack for feature-auth...
Command: npm test

> test
> jest

 PASS  src/auth.test.ts
 PASS  src/api.test.ts

Tests: 24 passed, 24 total
Time: 2.3s

✓ Tests passed!
Duration: 2.4s

Next step:
  • workstack rebase apply feature-auth
```

## References

- [Master Plan](STACKED_REBASE_MASTER_PLAN.md)
- [Previous: PR 4](STACKED_REBASE_PR4_CONFLICT_RESOLUTION.md)
- [Next: PR 6](STACKED_REBASE_PR6_POLISH.md)
