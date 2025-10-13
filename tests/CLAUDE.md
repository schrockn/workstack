# Test Structure Documentation

For comprehensive testing patterns and architecture, see:
**[.agent/docs/TESTING.md](../.agent/docs/TESTING.md)**

## Quick Commands

Run all tests: `uv run pytest`
Run specific test: `uv run pytest tests/commands/workspace/test_rm.py::test_rm_force_removes_directory`
Run with coverage: `uv run pytest --cov=workstack`

## Test Organization

Tests are organized hierarchically to optimize context loading and provide targeted guidance:

### Command Tests (CLI Layer)

- `tests/commands/` - CLI command tests with subcategories:
  - `workspace/` - Create, rename, rm, move commands
  - `navigation/` - Switch, up, down commands
  - `display/` - Status, tree, list commands
  - `shell/` - Shell integration and wrappers
  - `management/` - Garbage collection, planning
  - `setup/` - Init, config, completion

See [commands/CLAUDE.md](commands/CLAUDE.md) for CLI testing patterns.

### Core Tests (Business Logic Layer)

- `tests/core/` - Core logic unit tests with subcategories:
  - `config/` - Configuration management
  - `operations/` - Git, Graphite, GitHub operations (see [core/operations/CLAUDE.md](core/operations/CLAUDE.md))
  - `detection/` - Auto-detection logic
  - `utils/` - Utility functions
  - `foundation/` - Core infrastructure

See [core/CLAUDE.md](core/CLAUDE.md) for core testing patterns.

### Other Test Directories

- `tests/integration/` - Integration tests with real git
- `tests/status/` - Status system tests
- `tests/dev_cli_core/` - Dev CLI infrastructure tests
- `tests/fakes/` - Fake implementations for dependency injection

## Quick Reference

| Need to...                      | See                                                                                                   |
| ------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Understand testing architecture | [.agent/docs/TESTING.md](../.agent/docs/TESTING.md)                                                   |
| Write a new CLI command test    | [.agent/docs/TESTING.md#unit-test-pattern](../.agent/docs/TESTING.md#unit-test-pattern)               |
| Test real git behavior          | [.agent/docs/TESTING.md#integration-test-pattern](../.agent/docs/TESTING.md#integration-test-pattern) |
| Test dry-run mode               | [.agent/docs/TESTING.md#dry-run-test-pattern](../.agent/docs/TESTING.md#dry-run-test-pattern)         |
| Configure fakes                 | [.agent/docs/TESTING.md#dependency-categories](../.agent/docs/TESTING.md#dependency-categories)       |

## Context Window Strategy

Each subdirectory has targeted CLAUDE.md files with domain-specific patterns:

- Load only the CLAUDE.md relevant to your current work
- Example: working on `test_create.py` → load `commands/workspace/CLAUDE.md`
- This reduces context noise by 50-70% compared to flat structure

## Testing Principles

1. **Use dependency injection** - All tests inject fakes via WorkstackContext
2. **No mock.patch** - Use FakeShellOps, FakeGitOps, etc. instead
3. **Constructor injection** - All fake state configured at construction
4. **Mutation tracking** - Use read-only properties for assertions (e.g., `git_ops.deleted_branches`)
5. **Three implementations** - Real (production), Dry-Run (safety), Fake (testing)

For complete details, see [.agent/docs/TESTING.md](../.agent/docs/TESTING.md).
