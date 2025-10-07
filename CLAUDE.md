# Workstack Coding Standards

This document defines coding standards for the `workstack` project. These standards should be followed by all contributors, including AI coding assistants.

## Project Structure

This project uses the **src layout**:

- Source code: `src/workstack/`
- Tests: `tests/`
- Configuration: `pyproject.toml`

When adding new modules, place them in `src/workstack/` and add corresponding tests in `tests/`.

## Style and Best Practices

### Python Version Requirements

- **Target Python Version**: Python 3.13 and above only
- **Modern Python Features**: Use all modern Python features available in 3.13+
- **Type Annotations**: Use built-in generic types (e.g., `list[str]`, `dict[str, Any]`) instead of `typing` module equivalents

### Python Typing Conventions

- **NEVER use `from __future__ import annotations`** - This is explicitly forbidden in this codebase and unnecessary for Python 3.13+
- **All functions must have complete type annotations** for parameters and return values
- **Built-in Generic Types**: Use lowercase built-in types (`list`, `dict`, `set`, `tuple`) instead of capitalized `typing` imports
  - ✅ Use: `list[str]`, `dict[str, Any]`, `set[int]`
  - ❌ Avoid: `List[str]`, `Dict[str, Any]`, `Set[int]` (legacy Python <3.9 compatibility)
- **Modern Union Syntax**: Use `X | Y` instead of `Union[X, Y]` for union types
- **Optional Types**: Use `X | None` instead of `Optional[X]`
- **No string quotes in type hints**: Use modern syntax without quotes
  - ✅ `def foo(x: str | None) -> list[str]:`
  - ❌ `def foo(x: "str | None") -> "list[str]":`
- **Return type for void functions**: Use `-> None` for functions with no return value
- **Immutable data structures**: Use `dataclass` with `frozen=True` for immutable data:
  ```python
  @dataclass(frozen=True)
  class GlobalConfig:
      workstacks_root: Path
      use_graphite: bool
  ```

### Abstract Interfaces and Dependency Injection

- **ALWAYS use Abstract Base Classes (ABC) for defining interfaces** - never use `typing.Protocol`
- **Use `from abc import ABC, abstractmethod`** for interface definitions
- **Inject dependencies through dataclass constructors** - use frozen dataclasses for contexts
- **Follow the existing GitOps pattern** - see `src/workstack/gitops.py` as the reference implementation
- **Test implementations must inherit from the ABC** - place fakes in `tests/fakes/`
- **Fakes must be in-memory only** - no filesystem I/O in test implementations

**Preferred pattern:**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

class MyOps(ABC):
    """Abstract interface for my operations.

    All implementations (real and fake) must implement this interface.
    """

    @abstractmethod
    def do_something(self, arg: str) -> bool:
        """Perform operation."""
        ...

class RealMyOps(MyOps):
    """Production implementation."""

    def do_something(self, arg: str) -> bool:
        # real implementation
        return True

@dataclass(frozen=True)
class AppContext:
    """Application context with injected dependencies."""
    my_ops: MyOps
```

**Test implementations (in-memory, no filesystem):**

```python
# tests/fakes/my_ops.py
class FakeMyOps(MyOps):
    """In-memory fake - no filesystem access.

    State is held in memory. Constructor accepts initial state.
    """

    def __init__(self, *, initial_state: SomeState | None = None) -> None:
        self._state = initial_state

    def do_something(self, arg: str) -> bool:
        # In-memory implementation
        return True
```

**Why ABC over Protocol:**

- **Explicit inheritance** makes interfaces discoverable through IDE navigation
- **Runtime validation** that implementations are complete (missing methods caught immediately)
- **Better IDE support** and error messages when implementing interfaces
- **More explicit about design intent** - signals this is a formal interface contract
- **Matches existing codebase patterns** - consistency with GitOps and other abstractions

**Why in-memory fakes:**

- **Faster tests** - no filesystem I/O overhead
- **No cleanup needed** - state automatically discarded
- **Explicit state** - test setup shows all configuration clearly
- **Parallel test execution** - no shared filesystem state

### Import Organization

Imports must be organized in three groups (enforced by isort/ruff):

1. **Standard library imports** (e.g., `import os`, `from pathlib import Path`)
2. **Third-party imports** (e.g., `import click`)
3. **Local imports** (e.g., `from workstack.config import load_config`)

Within each group, imports should be alphabetically sorted.

Example:

```python
import os
import shlex
import subprocess
from pathlib import Path

import click

from workstack.activation import render_activation_script
from workstack.config import load_config
from workstack.core import discover_repo_context
```

#### Import Location and Aliasing

- **ALWAYS use top-level (module-scoped) imports** - avoid function-scoped imports except in very rare cases
- **ALWAYS use absolute imports** - never use relative imports (e.g., use `from workstack.config import load_config` instead of `from .config import load_config`)
- **DO NOT alias imports with `as`** unless strictly required to resolve naming collisions with third-party packages
- **Acceptable exceptions for function-scoped imports:**
  1. **TYPE_CHECKING blocks**: Imports only needed for type annotations
  2. **Circular import resolution**: When imports would create circular dependencies
  3. **Optional dependencies**: When import failure should be handled gracefully
  4. **Expensive lazy loading**: When imports are computationally expensive and conditionally used

**Examples of correct import patterns:**

```python
# ✅ GOOD: Top-level imports
from contextlib import contextmanager
from csbot.contextengine.contextstore_protocol import GitCommitInfo, GitInfo
from csbot.contextengine.file_tree import FilesystemFileTree

@contextmanager
def my_function():
    tree = FilesystemFileTree(path)
    # Use GitCommitInfo, GitInfo directly
```

```python
# ❌ BAD: Function-scoped imports without justification
@contextmanager
def my_function():
    from csbot.contextengine.contextstore_protocol import GitCommitInfo, GitInfo
    from csbot.contextengine.file_tree import FilesystemFileTree
    tree = FilesystemFileTree(path)
```

```python
# ✅ ACCEPTABLE: TYPE_CHECKING imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anthropic import Anthropic
    from csbot.contextengine.file_tree import FileTree
```

```python
# ✅ ACCEPTABLE: Avoiding circular imports
def create_context_engine():
    # Import here to avoid circular dependency:
    # context_engine.py -> github_working_dir.py -> context_engine.py
    from csbot.contextengine.context_engine import ContextEngine
    return ContextEngine(...)
```

### Code Formatting & Type Checking

- **Ruff** for formatting and linting
  - Line length: 100 characters
  - Target version: Python 3.13
  - Run: `make format` or `uv run ruff format`
  - **Enabled lint rules:**
    - E (pycodestyle errors)
    - F (pyflakes)
    - I (isort - import sorting)
    - UP (pyupgrade)
    - B (flake8-bugbear)
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

- **Use early returns and guard clauses** to reduce nesting depth
- **Extract helper functions** when logic becomes deeply nested
- **Prefer early continue/break** over nested conditionals in loops
- **Flatten if-else chains** by handling error cases early

**Anti-pattern (excessive nesting):**

```python
def process_data(data):
    if data:                           # Level 1
        if validate(data):             # Level 2
            result = transform(data)
            if result:                 # Level 3
                if result.is_valid:    # Level 4
                    if save(result):   # Level 5 - TOO DEEP!
                        return True
    return False
```

**Preferred pattern (early returns):**

```python
def process_data(data):
    if not data:
        return False

    if not validate(data):
        return False

    result = transform(data)
    if not result:
        return False

    if not result.is_valid:
        return False

    return save(result)
```

**Preferred pattern (extraction):**

```python
def _validate_and_transform(data):
    """Validate and transform data, returning None on failure."""
    if not validate(data):
        return None

    result = transform(data)
    if not result or not result.is_valid:
        return None

    return result

def process_data(data):
    if not data:
        return False

    result = _validate_and_transform(data)
    if result is None:
        return False

    return save(result)
```

**When extracting functions to reduce nesting:**

- Name extracted functions with descriptive verbs (e.g., `_validate_input`, `_load_configuration`)
- Keep extracted functions close to their usage (typically just above the calling function)
- Document what None/empty returns mean for error handling
- Prefix internal helpers with `_` to indicate they're not part of the public API

### Module Exports

- **DO NOT use `__all__` in `__init__.py` files** - avoid explicit export control in package initialization
- Let imports be naturally available without restricting the module's public API

### File Operations

- **Always use `pathlib.Path`** (never `os.path`)
- Always specify `encoding="utf-8"` when reading/writing text files
- Use `.resolve()` to get absolute paths
- Use `.exists()`, `.is_dir()`, `.is_file()` for path checks
- Use `.expanduser()` for paths with `~`

Example:

```python
config_path = Path.home() / ".workstack" / "config.toml"
content = config_path.read_text(encoding="utf-8")
data = tomllib.loads(content)
```

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

Example:

```python
@cli.command("create")
@click.argument("name", metavar="NAME", required=False)
@click.option("--branch", type=str, help="Branch name to create")
@click.option("--no-post", is_flag=True, help="Skip post-create commands")
def create(name: str | None, branch: str | None, no_post: bool) -> None:
    """Create a worktree and write a .env file."""
    # implementation

# Error handling example
if not wt_path.exists():
    click.echo(f"Worktree not found: {wt_path}", err=True)
    raise SystemExit(1)
```

### Function Arguments

- **NEVER use default arguments** unless there is a nearby comment explaining why the default is appropriate
- **Always be explicit about parameter values** - avoid relying on implicit defaults that may not be obvious to readers
- **Exception**: Default arguments are acceptable when accompanied by a comment that explains the rationale for the default value

```python
# BAD: Unclear why None is the default
def process_data(data, format=None):
    pass

# GOOD: Comment explains the default behavior
def process_data(data, format=None):
    # format=None defaults to auto-detection based on file extension
    pass

# PREFERRED: Explicit parameter passing at call sites
process_data(data, format="json")
process_data(data, format=None)  # Explicitly choosing auto-detection
```

### Context Managers

**DO NOT assign unentered context manager objects to intermediate variables** - use them directly as the target of `with`:

```python
# BAD: Assigning context manager to variable before entering
pr = self.backend.github_working_dir.pull_request(
    f"CRONJOB UPDATE: {existing_cron_job.thread}",
    body,
    False,
)
with pr:
    # work with pr

# GOOD: Use context manager directly in with statement
with self.backend.github_working_dir.pull_request(
    f"CRONJOB UPDATE: {existing_cron_job.thread}",
    body,
    False,
) as pr:
    # work with pr
```

**Rationale**: Assigning an unentered context manager to a variable can lead to resource leaks if the variable is accidentally used outside the context manager, and makes the code less clear about when resources are acquired and released.

**Exception**: When you need to access properties of the context manager object after it exits (e.g., results set during `__exit__`), it's acceptable to assign to a variable:

```python
# ACCEPTABLE: When you need post-exit access to context manager properties
pr = self.backend.github_working_dir.pull_request(title, body, False)
with pr:
    # do work within context
    pass
# Access properties set during __exit__
return SomeResult(url=pr.pr_url)
```

### Resource Management and Cleanup

**DO NOT use `__del__` for resource cleanup** - Python's garbage collection is not deterministic, making `__del__` unreliable for cleanup:

```python
# BAD: Using __del__ for cleanup
class DatabaseConnection:
    def __init__(self, connection_string):
        self.conn = create_connection(connection_string)

    def __del__(self):
        # This may never be called or called at unpredictable times
        if hasattr(self, 'conn'):
            self.conn.close()
```

**DO NOT implement context manager protocol directly on objects** - this tightly couples resource lifecycle to object lifecycle:

```python
# BAD: Context manager protocol on the object itself
class DatabaseConnection:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.conn = None

    def __enter__(self):
        self.conn = create_connection(self.connection_string)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
```

**PREFERRED: Use classmethod factories that return context managers** - this separates object construction from resource management:

```python
# GOOD: Classmethod factory that returns a context manager
from contextlib import contextmanager

class DatabaseConnection:
    @classmethod
    @contextmanager
    def connect(cls, connection_string):
        """Create and manage a database connection."""
        conn = create_connection(connection_string)
        try:
            yield conn
        finally:
            conn.close()

# Usage
with DatabaseConnection.connect("postgresql://...") as conn:
    # Use conn here
    conn.execute("SELECT * FROM users")
# Connection automatically closed
```

**Alternative: Standalone factory functions**:

```python
# GOOD: Standalone context manager factory
@contextmanager
def database_connection(connection_string):
    """Create and manage a database connection."""
    conn = create_connection(connection_string)
    try:
        yield conn
    finally:
        conn.close()

# Usage
with database_connection("postgresql://...") as conn:
    conn.execute("SELECT * FROM users")
```

**Rationale**:

- **Deterministic cleanup**: Context managers guarantee cleanup happens when the `with` block exits
- **Clear resource boundaries**: Resource acquisition and release are explicit and scoped
- **Separation of concerns**: Object lifecycle is separate from resource lifecycle
- **Testing friendly**: Easy to test resource management independently

## Exception Handling Guidelines

This codebase follows specific norms for exception handling to maintain clean, predictable code:

### General Principles

- **By default, exceptions should NOT be used as control flow**
- **Do NOT implement alternative paths in catch blocks** - exceptions should bubble up the stack to be handled at appropriate boundaries
- **Avoid catching broad `Exception` types** unless you have a specific reason
- **Prefer "Look Before You Leap" (LBYL) over "Easier to Ask for Forgiveness than Permission" (EAFP)** - Check conditions before performing operations rather than catching exceptions

#### Look Before You Leap (LBYL) Pattern

**ALWAYS prefer checking conditions proactively** rather than using try/except blocks:

```python
# PREFERRED: LBYL - Check before acting
if has_capability(obj):
    result = use_capability(obj)
else:
    result = use_alternative(obj)

# AVOID: EAFP - Try and catch exceptions
try:
    result = use_capability(obj)
except CapabilityError:
    result = use_alternative(obj)
```

**Benefits of LBYL:**

- More explicit about intent
- Easier to understand control flow
- Better performance (no exception overhead)
- Clearer distinction between errors and normal flow
- Easier to debug (exceptions indicate real problems)

**When EAFP is acceptable:**

- No practical way to check the condition beforehand
- Checking would require duplicating the operation's logic
- Third-party APIs that use exceptions for control flow
- Race conditions where state could change between check and use

### CRITICAL ENFORCEMENT

**Claude Code: You MUST NOT violate these exception handling rules. Specifically:**

1. **NEVER write try/except blocks for alternate execution paths** - Let exceptions bubble up instead of catching them to try alternative approaches
2. **NEVER swallow exceptions silently** - Don't use empty `except:` blocks or `except Exception: pass` patterns
3. **NEVER catch exceptions just to continue with different logic** - This masks real problems and makes debugging impossible
4. **ALWAYS let exceptions propagate to appropriate error boundaries** - Only handle exceptions at CLI level, column analysis boundaries, or when dealing with third-party API quirks

**If you find yourself writing try/except, STOP and ask: "Should this exception bubble up instead?"**

### Acceptable Uses of Exception Handling

1. **Error Boundaries**: Meaningful divisions in software that have sensible default error behavior
   - CLI commands (top-level exception handlers for user-friendly error messages)
   - Column analysis operations (individual column failures shouldn't fail entire table analysis)
2. **API Compatibility**: Compensating for APIs that use exceptions for control flow
   - When third-party APIs use exceptions to indicate missing keys/values
   - When database dialects have different capabilities that can't be detected a priori
3. **Embellishing Exceptions**: Adding context to in-flight exceptions before re-raising

### Implementation Pattern: Encapsulation

When violating exception norms is necessary, **encapsulate the violation within a function**:

```python
# GOOD: Exception handling encapsulated in helper function
def _get_bigquery_sample_with_alternate(sql_client, table_name, percentage, limit):
    """
    Try BigQuery TABLESAMPLE, use alternate approach for views.

    BigQuery's TABLESAMPLE doesn't work on views, so we use exception handling
    to detect this case. This is acceptable because there's no reliable way
    to determine a priori whether a table supports TABLESAMPLE.
    """
    try:
        return sql_client.run_query(f"SELECT * FROM {table_name} TABLESAMPLE...")
    except Exception:
        return sql_client.run_query(f"SELECT * FROM {table_name} ORDER BY RAND()...")
# BAD: Exception control flow exposed in main logic
try:
    sample_rows = sql_client.run_query(f"SELECT * FROM {table_name} TABLESAMPLE...")
except Exception:
    sample_rows = sql_client.run_query(f"SELECT * FROM {table_name} ORDER BY RAND()...")
```

### Preferred Approach: Proactive Checking

When possible, check conditions that cause errors before making calls:

```python
# PREFERRED: Check condition beforehand
if is_view(table_name):
    return get_view_sample(table_name)
else:
    return get_table_sample(table_name)
# AVOID: Using exceptions to discover the condition
try:
    return get_table_sample(table_name)  # Will fail on views
except Exception:
    return get_view_sample(table_name)
```

#### Dictionary/Mapping Access

**ALWAYS use membership testing (`in`) before accessing dictionary keys** instead of catching `KeyError`:

```python
# PREFERRED: Proactive key existence checking
if key in mapping:
    value = mapping[key]
    # process value
else:
    # handle missing key case
    handle_missing_key()

# AVOID: Using KeyError as control flow
try:
    value = mapping[key]
    # process value
except KeyError:
    handle_missing_key()
```

**Rationale**: Membership testing is more explicit about intent, performs better, and avoids using exceptions for control flow. The `in` operator clearly indicates that you're checking for key existence before access.

### Validation and Input Checking

**DO NOT catch exceptions just to re-raise them with different messages** unless you're adding meaningful context:

```python
# BAD: Unnecessary exception transformation
try:
    croniter(cron_string, now).get_next(datetime)
except Exception as e:
    raise ValueError(f"Invalid cron string: {e}")

# GOOD: Let the original exception bubble up with its specific error details
croniter(cron_string, now).get_next(datetime)

# ACCEPTABLE: Adding meaningful context before re-raising
try:
    croniter(cron_string, now).get_next(datetime)
except Exception as e:
    raise ValueError(f"Cron job '{job_name}' has invalid schedule '{cron_string}': {e}") from e
```

**Rationale**: The original exception from third-party libraries (like `croniter`) often contains more precise error information than generic wrapper messages. Only transform exceptions when you're adding valuable context that helps with debugging or user experience.

### File Processing and Data Integrity

**DO NOT catch exceptions during file processing operations** unless at appropriate error boundaries:

```python
# BAD: Silently skipping malformed files
for context_file in files:
    try:
        context_data = yaml.safe_load(read_file(context_file))
        process_context(context_data)
    except (yaml.YAMLError, ValidationError) as e:
        print(f"Warning: Skipping malformed file {context_file}: {e}")
        continue  # This hides real problems

# GOOD: Let exceptions bubble up to reveal systemic issues
for context_file in files:
    context_data = yaml.safe_load(read_file(context_file))  # Will fail fast on corruption
    process_context(context_data)
```

**Rationale**: If files are malformed, it indicates:

- CI/tooling has failed
- Data corruption has occurred
- System is in an untrustworthy state

The problem should be fixed at its source (CI, validation, tooling) rather than masked with exception handling.

### Exception Swallowing Anti-Patterns

**NEVER swallow exceptions silently** - always let them bubble up to appropriate error boundaries:

```python
# BAD: Silently swallowing exceptions
try:
    if not self.is_dir(path):
        return
    for name in self.listdir(path):
        if fnmatch.fnmatch(name, pattern):
            yield f"{path}/{name}" if path else name
except (FileNotFoundError, NotADirectoryError):
    return  # Silently fails, hiding real problems

# GOOD: Let exceptions bubble up
if not self.is_dir(path):
    return
for name in self.listdir(path):
    if fnmatch.fnmatch(name, pattern):
        yield f"{path}/{name}" if path else name
```

**NEVER implement alternate execution paths in exception handlers** unless you're at an appropriate error boundary:

```python
# BAD: Using exceptions for alternate logic
try:
    return PurePosixPath(path).match(pattern)
except ValueError:
    # Alternate path using fnmatch if PurePath.match fails
    return fnmatch.fnmatch(path, pattern)

# GOOD: Let the original exception bubble up
return PurePosixPath(path).match(pattern)
```

**Rationale**: Exception swallowing masks real problems and makes debugging extremely difficult. If an exception occurs, it usually indicates a genuine issue that needs to be addressed, not hidden.

## Async/Sync Interface Pattern

When you need to maintain parallel sync and async interfaces for the same business logic, consult `@src/csbot/utils/async_thread.py` for a Protocol-based pattern that:

- Eliminates code duplication between sync and async implementations
- Provides automatic conversion through decorators
- Maintains type safety through protocols
- Creates a single source of truth for business logic
- Allows easy testing of sync logic without async complexity

This pattern is particularly useful when you have business logic that needs to be available in both synchronous and asynchronous contexts without duplicating the implementation.
