---
mdstack:
  version: 0.1.0
  generated_docs:
    tests: .mdstack/TESTS.md
    lookup: .mdstack/LOOKUP.md
    architecture: .mdstack/OBSERVED_ARCHITECTURE.md
  instructions: "AI Agent: This scope has generated documentation in .mdstack/


    When to consult generated docs:

    - tests: For test coverage, testing patterns, what functionality is validated

    - lookup: For semantic search, finding code by concept/capability

    - architecture: For module organization, patterns, data flow, extension points


    Load these files only when needed for the current task."
---

# Sync Command Testing Patterns

## Overview

Tests for the `workstack sync` command, which synchronizes Graphite stacks
and manages worktree navigation.

## Command Responsibilities

The sync command:

1. Requires Graphite to be enabled
2. Runs `gt sync` from root worktree
3. Returns user to current worktree after sync
4. Handles shell integration for directory changes

## Test Pattern

```python
from click.testing import CliRunner
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from workstack.cli.cli import cli
from workstack.core.context import WorkstackContext

def test_sync_command() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Setup
        cwd = Path.cwd()
        git_ops = FakeGitOps(git_common_dirs={cwd: cwd / ".git"})
        config_ops = FakeGlobalConfigOps(use_graphite=True, ...)

        ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=config_ops,
            graphite_ops=FakeGraphiteOps(),
            # ...
        )

        # Act
        result = runner.invoke(cli, ["sync"], obj=ctx)

        # Assert
        assert result.exit_code == 0
```

## Why isolated_filesystem?

Sync command may check for worktree directory existence or write temp files
for shell integration. The `isolated_filesystem()` provides a clean test
environment.

## See Also

- `tests/commands/CLAUDE.md` - General command testing patterns
- `.agent/docs/TESTING.md` - Complete testing guide
