# Workstack Coding Standards

This document defines coding standards for the `workstack` project. These standards should be followed by all contributors, including AI coding assistants.

**📍 Quick navigation**: This file contains core rules. For detailed examples and guides, see the [Quick Reference](#quick-reference) table below.

---

## Project Structure

This project uses the **src layout**:

- Source code: `src/workstack/`
- Tests: `tests/`
- Configuration: `pyproject.toml`

When adding new modules, place them in `src/workstack/` and add corresponding tests in `tests/`.

---

## Quick Reference

| What You Need                  | Documentation                                                          |
| ------------------------------ | ---------------------------------------------------------------------- |
| **See code examples**          | [.agent/docs/PATTERNS.md](.agent/docs/PATTERNS.md)                     |
| **Exception handling details** | [.agent/docs/EXCEPTION_HANDLING.md](.agent/docs/EXCEPTION_HANDLING.md) |
| **Documentation index**        | [.agent/docs/README.md](.agent/docs/README.md)                         |
| **Write tests**                | [tests/CLAUDE.md](tests/CLAUDE.md)                                     |

---

## Critical Rules

### Python Version Requirements

- **Target Python Version**: Python 3.13 and above only
- **Modern Python Features**: Use all modern Python features available in 3.13+
- **Type Annotations**: Use built-in generic types (e.g., `list[str]`, `dict[str, Any]`) instead of `typing` module equivalents

### Python Typing Conventions

- **NEVER use `from __future__ import annotations`** - This is explicitly forbidden in this codebase and unnecessary for Python 3.13+
- **All functions must have complete type annotations** for parameters and return values
- **Built-in Generic Types**: Use lowercase built-in types (`list`, `dict`, `set`, `tuple`) instead of capitalized `typing` imports
  - ✅ Use: `list[str]`, `dict[str, Any]`, `set[int]`
  - ❌ Avoid: `List[str]`, `Dict[str, Any]`, `Set[int]`
- **Modern Union Syntax**: Use `X | Y` instead of `Union[X, Y]`
- **Optional Types**: Use `X | None` instead of `Optional[X]`
- **No string quotes in type hints**: Use modern syntax without quotes
- **Return type for void functions**: Use `-> None`
- **Immutable data structures**: Use `dataclass` with `frozen=True`

**Examples**: [.agent/docs/PATTERNS.md#type-annotations](.agent/docs/PATTERNS.md#type-annotations)

### Abstract Interfaces and Dependency Injection

- **ALWAYS use Abstract Base Classes (ABC) for defining interfaces** - never use `typing.Protocol`
- **Use `from abc import ABC, abstractmethod`** for interface definitions
- **Inject dependencies through dataclass constructors** - use frozen dataclasses for contexts
- **Follow the existing GitOps pattern** - see `src/workstack/gitops.py` as the reference implementation
- **Test implementations must inherit from the ABC** - place fakes in `tests/fakes/`
- **Fakes must be in-memory only** - no filesystem I/O in test implementations

**Pattern & Examples**: [.agent/docs/PATTERNS.md#dependency-injection](.agent/docs/PATTERNS.md#dependency-injection)

### Import Organization

Imports must be organized in three groups (enforced by isort/ruff):

1. **Standard library imports** (e.g., `import os`, `from pathlib import Path`)
2. **Third-party imports** (e.g., `import click`)
3. **Local imports** (e.g., `from workstack.config import load_config`)

Within each group, imports should be alphabetically sorted.

**Additional rules**:

- **ALWAYS use top-level (module-scoped) imports** - avoid function-scoped imports except in very rare cases
- **ALWAYS use absolute imports** - never use relative imports (e.g., use `from workstack.config import load_config` instead of `from .config import load_config`)
- **DO NOT alias imports with `as`** unless strictly required to resolve naming collisions

**Acceptable exceptions for function-scoped imports**:

1. TYPE_CHECKING blocks (imports only needed for type annotations)
2. Circular import resolution
3. Optional dependencies (when import failure should be handled gracefully)
4. Expensive lazy loading

**Examples**: [.agent/docs/PATTERNS.md#import-organization](.agent/docs/PATTERNS.md#import-organization)

### Exception Handling ⚠️ CRITICAL

**This codebase has strict exception handling rules:**

- **NEVER use exceptions for control flow**
- **Prefer "Look Before You Leap" (LBYL) over "Easier to Ask for Forgiveness than Permission" (EAFP)** - Check conditions before performing operations rather than catching exceptions
- **NEVER write try/except blocks for alternate execution paths** - Let exceptions bubble up
- **NEVER swallow exceptions silently** - Don't use empty `except:` blocks or `except Exception: pass` patterns
- **ALWAYS let exceptions propagate to appropriate error boundaries** - Only handle exceptions at CLI level or when dealing with third-party API quirks

**If you find yourself writing try/except, STOP and ask: "Should this exception bubble up instead?"**

**Complete Guide**: [.agent/docs/EXCEPTION_HANDLING.md](.agent/docs/EXCEPTION_HANDLING.md) - Read this before handling exceptions

### Code Formatting & Type Checking

- **Ruff** for formatting and linting
  - Line length: 100 characters
  - Target version: Python 3.13
  - Run: `make format` or `uv run ruff format`
  - **Enabled lint rules**: E (pycodestyle), F (pyflakes), I (isort), UP (pyupgrade), B (flake8-bugbear)
- **Pyright** for type checking
  - Mode: standard
  - All Python code must pass type checking with zero errors
  - Run: `make pyright` or `uv run pyright`

### Naming Conventions

- **Functions and variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `GLOBAL_CONFIG_PATH`)
- **Private functions:** prefix with `_` (e.g., `_remove_worktree`, `_list_worktrees`)
- **CLI commands:** kebab-case (e.g., `workstack create`, `workstack switch`)
- **Module names:** Use underscores for multi-word modules (e.g., `github_ops.py`, not `githubops.py`)
- **Brand names in code:** Use proper capitalization:
  - ✅ `GitHub` (capital H) - in class names, comments, docstrings
  - ❌ `Github` (lowercase h) - incorrect capitalization

### Code Indentation and Nesting

**NEVER exceed 4 levels of indentation** in production code (5 is acceptable only in test data structures):

**Strategies to reduce nesting**:

- Use early returns and guard clauses
- Extract helper functions when logic becomes deeply nested
- Prefer early continue/break over nested conditionals in loops
- Flatten if-else chains by handling error cases early

**When extracting functions**:

- Name with descriptive verbs (e.g., `_validate_input`, `_load_configuration`)
- Keep extracted functions close to their usage (typically just above the calling function)
- Document what None/empty returns mean for error handling
- Prefix internal helpers with `_` to indicate they're not part of the public API

**Examples**: [.agent/docs/PATTERNS.md#code-style](.agent/docs/PATTERNS.md#code-style) shows before/after refactoring

### Module Exports

- **DO NOT use `__all__` in `__init__.py` files** - avoid explicit export control in package initialization
- Let imports be naturally available without restricting the module's public API

### File Operations

- **Always use `pathlib.Path`** (never `os.path`)
- Always specify `encoding="utf-8"` when reading/writing text files
- Use `.resolve()` to get absolute paths
- Use `.exists()`, `.is_dir()`, `.is_file()` for path checks
- Use `.expanduser()` for paths with `~`

**Examples**: [.agent/docs/PATTERNS.md#file-operations](.agent/docs/PATTERNS.md#file-operations)

### CLI Development (Click)

- Use `click.group()` for command groups
- Use `click.command()` for individual commands
- Use `click.argument()` for required positional arguments
- Use `click.option()` for optional flags and parameters
- Use `is_flag=True` for boolean flags
- Provide help text for all commands and options
- Use `shell_complete=` for shell completion functions
- Use `click.echo()` for all CLI output (not `print()`)
- Use `click.echo(..., err=True)` for error messages
- Exit with `raise SystemExit(1)` for CLI errors
- Use `subprocess.run(..., check=True)` for subprocess calls
- Provide clear, actionable error messages

**Examples**: [.agent/docs/PATTERNS.md#cli-development](.agent/docs/PATTERNS.md#cli-development)

### Function Arguments

- **STRONGLY PREFER: No default arguments** - Force explicit values at all call sites to prevent entire class of errors
- **Always be explicit about parameter values** - Make intent clear at every call site
- **Exception**: Default arguments are acceptable when they significantly improve API ergonomics AND are accompanied by a comment explaining why the default is appropriate
- **Rationale**: Explicit call sites prevent ambiguity, make refactoring easier, and avoid implicit behavior bugs

**Examples**: [.agent/docs/PATTERNS.md#function-arguments](.agent/docs/PATTERNS.md#function-arguments)

### Context Managers

**DO NOT assign unentered context manager objects to intermediate variables** - use them directly as the target of `with`:

**Exception**: When you need to access properties of the context manager object after it exits (e.g., results set during `__exit__`), it's acceptable to assign to a variable.

**Rationale**: Assigning an unentered context manager to a variable can lead to resource leaks if the variable is accidentally used outside the context manager, and makes the code less clear about when resources are acquired and released.

**Examples**: [.agent/docs/PATTERNS.md#context-managers](.agent/docs/PATTERNS.md#context-managers)

### Resource Management and Cleanup

**DO NOT use `__del__` for resource cleanup** - Python's garbage collection is not deterministic, making `__del__` unreliable for cleanup.

**DO NOT implement context manager protocol directly on objects** - this tightly couples resource lifecycle to object lifecycle.

**PREFERRED: Use classmethod factories that return context managers** - this separates object construction from resource management.

**Alternative: Standalone factory functions** - use `@contextmanager` decorator for simple cases.

**Rationale**:

- **Deterministic cleanup**: Context managers guarantee cleanup happens when the `with` block exits
- **Clear resource boundaries**: Resource acquisition and release are explicit and scoped
- **Separation of concerns**: Object lifecycle is separate from resource lifecycle
- **Testing friendly**: Easy to test resource management independently

**Examples**: [.agent/docs/PATTERNS.md#resource-management](.agent/docs/PATTERNS.md#resource-management)

---

## Design Principles

1. **Dependency Injection**: All external dependencies behind ABC interfaces
2. **Immutability**: Use frozen dataclasses, no mutable state
3. **Testability**: In-memory fakes, no filesystem I/O in unit tests
4. **Explicit is better than implicit**: No default arguments without comments
5. **Fail fast**: Let exceptions bubble to error boundaries

These principles guide all design decisions in the codebase.

---

## Async/Sync Interface Pattern

When you need to maintain parallel sync and async interfaces for the same business logic, consult `@src/csbot/utils/async_thread.py` for a Protocol-based pattern that:

- Eliminates code duplication between sync and async implementations
- Provides automatic conversion through decorators
- Maintains type safety through protocols
- Creates a single source of truth for business logic
- Allows easy testing of sync logic without async complexity

This pattern is particularly useful when you have business logic that needs to be available in both synchronous and asynchronous contexts without duplicating the implementation.

---

## Related Documentation

- [.agent/docs/PATTERNS.md](.agent/docs/PATTERNS.md) - All code examples for patterns in this file
- [.agent/docs/EXCEPTION_HANDLING.md](.agent/docs/EXCEPTION_HANDLING.md) - Complete exception handling guide
- [.agent/docs/README.md](.agent/docs/README.md) - Documentation index and navigation guide
- [tests/CLAUDE.md](tests/CLAUDE.md) - Testing patterns and practices
- [README.md](README.md) - Project overview and getting started
