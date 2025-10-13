# Test Structure Documentation

For comprehensive testing patterns and architecture, see:
**[.agent/docs/TESTING.md](../.agent/docs/TESTING.md)**

## Quick Commands

Run all tests: `uv run pytest`
Run specific test: `uv run pytest tests/commands/test_rm.py::test_rm_force_removes_directory`
Run with coverage: `uv run pytest --cov=workstack`

## Test Organization

- `tests/commands/` - CLI command tests (unit tests with fakes)
- `tests/core/` - Core logic unit tests
- `tests/integration/` - Integration tests with real git
- `tests/fakes/` - Fake implementations for dependency injection

## Quick Reference

| Need to...                      | See                                                                                                   |
| ------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Understand testing architecture | [.agent/docs/TESTING.md](../.agent/docs/TESTING.md)                                                   |
| Write a new CLI command test    | [.agent/docs/TESTING.md#unit-test-pattern](../.agent/docs/TESTING.md#unit-test-pattern)               |
| Test real git behavior          | [.agent/docs/TESTING.md#integration-test-pattern](../.agent/docs/TESTING.md#integration-test-pattern) |
| Test dry-run mode               | [.agent/docs/TESTING.md#dry-run-test-pattern](../.agent/docs/TESTING.md#dry-run-test-pattern)         |
| Configure fakes                 | [.agent/docs/TESTING.md#dependency-categories](../.agent/docs/TESTING.md#dependency-categories)       |

## Testing Principles

1. **Use dependency injection** - All tests inject fakes via WorkstackContext
2. **No mock.patch** - Use FakeShellOps, FakeGitOps, etc. instead
3. **Constructor injection** - All fake state configured at construction
4. **Mutation tracking** - Use read-only properties for assertions (e.g., `git_ops.deleted_branches`)
5. **Three implementations** - Real (production), Dry-Run (safety), Fake (testing)

For complete details, see [.agent/docs/TESTING.md](../.agent/docs/TESTING.md).
