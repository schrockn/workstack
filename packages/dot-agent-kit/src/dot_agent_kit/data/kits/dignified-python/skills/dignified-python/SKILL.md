# Dignified Python - Workstack Python Coding Standards

## Purpose

This skill provides workstack's Python coding standards and patterns. These standards emphasize **LBYL (Look Before You Leap)** patterns, explicit type annotations, and deterministic error handling.

**Core Philosophy**: Write explicit, predictable code that fails fast at proper boundaries.

---

## TOP 5 CRITICAL RULES

### 1. Exception Handling - NEVER for Control Flow 🔴

**ALWAYS use LBYL (Look Before You Leap), NEVER EAFP (Easier to Ask for Forgiveness than Permission)**

```python
# ✅ CORRECT: Check before acting
if key in mapping:
    value = mapping[key]
    process(value)
else:
    handle_missing_key()

# ❌ WRONG: Using exceptions for control flow
try:
    value = mapping[key]
    process(value)
except KeyError:
    handle_missing_key()
```

**Only handle exceptions at error boundaries:**

- CLI commands (for user-friendly messages)
- Third-party APIs that force exception handling
- Adding context before re-raising

### 2. Type Annotations - Python 3.13+ Syntax Only 🔴

**FORBIDDEN**: `from __future__ import annotations`

```python
# ✅ CORRECT: Modern Python 3.13+ syntax
def process_items(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

def find_user(user_id: int) -> User | None:
    ...

# ❌ WRONG: Legacy syntax
from typing import List, Dict, Optional
def process_items(items: List[str]) -> Dict[str, int]:
    ...
```

### 3. Path Operations - Check Exists First 🔴

**ALWAYS check `.exists()` BEFORE `.resolve()` or `.is_relative_to()`**

```python
# ✅ CORRECT: Check exists first
for wt_path in worktree_paths:
    if wt_path.exists():
        wt_path_resolved = wt_path.resolve()
        if current_dir.is_relative_to(wt_path_resolved):
            current_worktree = wt_path_resolved
            break

# ❌ WRONG: Using exceptions for path validation
try:
    wt_path_resolved = wt_path.resolve()
    if current_dir.is_relative_to(wt_path_resolved):
        current_worktree = wt_path_resolved
except (OSError, ValueError):
    continue
```

**Why**: `.resolve()` raises `OSError` for invalid paths; `.is_relative_to()` raises `ValueError`

### 4. Dependency Injection - ABC Not Protocol 🔴

```python
# ✅ CORRECT: Use ABC for interfaces
from abc import ABC, abstractmethod

class MyOps(ABC):
    @abstractmethod
    def operation(self) -> None:
        ...

# ❌ WRONG: Using Protocol
from typing import Protocol

class MyOps(Protocol):
    def operation(self) -> None:
        ...
```

**Benefits of ABC:**

- Explicit inheritance for discoverability
- Runtime validation of implementations
- Better IDE support

### 5. Imports - Absolute Only 🟡

```python
# ✅ CORRECT: Absolute imports
from workstack.config import load_config
from workstack.core import discover_repo_context

# ❌ WRONG: Relative imports
from .config import load_config
from .core import discover_repo_context
```

**Organize in three groups:**

1. Standard library imports
2. Third-party imports
3. Local imports

---

## PATTERN REFERENCE

### Dictionary Access

```python
# ✅ CORRECT: Membership testing
if key in mapping:
    value = mapping[key]
    process(value)
else:
    handle_missing()

# ✅ ALSO CORRECT: .get() with default
value = mapping.get(key, default_value)
process(value)

# ❌ WRONG: KeyError as control flow
try:
    value = mapping[key]
except KeyError:
    handle_missing()
```

### File Operations

**Always use pathlib.Path, never os.path:**

```python
from pathlib import Path

# ✅ CORRECT: pathlib operations
config_path = Path.home() / ".workstack" / "config.toml"
content = config_path.read_text(encoding="utf-8")

if config_path.exists():
    data = tomllib.loads(content)

# Path operations
absolute_path = config_path.resolve()  # After checking .exists()
expanded_path = Path("~/.config").expanduser()

# ❌ WRONG: os.path operations
import os
config_path = os.path.join(os.path.expanduser("~"), ".workstack", "config.toml")
```

**Always specify `encoding="utf-8"`** when reading/writing files.

### CLI Development (Click)

```python
import click

# ✅ CORRECT: Use click.echo()
click.echo("Success message")
click.echo("Error message", err=True)

# ✅ CORRECT: Exit with SystemExit
if not valid:
    click.echo("Error: Invalid input", err=True)
    raise SystemExit(1)

# ✅ CORRECT: subprocess with check=True
result = subprocess.run(
    ["git", "status"],
    cwd=repo_root,
    check=True,  # Raises CalledProcessError on failure
    capture_output=True,
    text=True,
)

# ❌ WRONG: Using print()
print("Success message")
```

### Code Style - Reduce Nesting

**Max 4 levels of indentation - use early returns:**

```python
# ✅ CORRECT: Early returns (max 2 levels)
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

# ❌ WRONG: Excessive nesting (5 levels)
def process_data(data):
    if data:
        if validate(data):
            result = transform(data)
            if result:
                if result.is_valid:
                    if save(result):  # 5 levels - TOO DEEP
                        return True
    return False
```

**Extract helper functions when needed:**

```python
def _validate_and_transform(data):
    """Validate and transform data, returning None on failure."""
    if not validate(data):
        return None

    result = transform(data)
    if not result or not result.is_valid:
        return None

    return result
```

### Immutable Data Structures

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class GlobalConfig:
    workstacks_root: Path
    use_graphite: bool
    show_pr_info: bool

# Usage - cannot be modified after creation
config = GlobalConfig(
    workstacks_root=Path("/home/user/workstacks"),
    use_graphite=True,
    show_pr_info=False,
)
```

### Context Managers

```python
# ✅ CORRECT: Use context manager directly in with statement
with self.backend.github_working_dir.pull_request(
    f"CRONJOB UPDATE: {existing_cron_job.thread}",
    body,
    False,
) as pr:
    # work with pr
    pass

# ❌ WRONG: Assigning before entering
pr = self.backend.github_working_dir.pull_request(title, body, False)
with pr:
    pass
```

**Exception**: When you need post-exit access to properties set during `__exit__`.

---

## ANTI-PATTERNS TO AVOID

### 1. Exception Swallowing

```python
# ❌ NEVER swallow exceptions silently
try:
    risky_operation()
except:
    pass

try:
    risky_operation()
except Exception:
    pass

# ✅ Let exceptions bubble up (default)
risky_operation()
```

### 2. Exception Transformation Without Context

```python
# ❌ BAD: Unnecessary transformation
try:
    croniter(cron_string, now).get_next(datetime)
except Exception as e:
    raise ValueError(f"Invalid cron string: {e}")

# ✅ GOOD: Let original exception bubble up
croniter(cron_string, now).get_next(datetime)

# ✅ ACCEPTABLE: Adding meaningful context
try:
    croniter(cron_string, now).get_next(datetime)
except Exception as e:
    raise ValueError(
        f"Cron job '{job_name}' has invalid schedule '{cron_string}': {e}"
    ) from e
```

### 3. Default Arguments Without Documentation

```python
# ❌ BAD: Unclear why None is default
def process_data(data, format=None):
    pass

# ✅ BEST: No defaults - explicit at call sites
def process_data(data, format):
    """Process data in the specified format.

    Args:
        format: Format to use. Use None for auto-detection.
    """
    if format is None:
        format = detect_format(data)

# All call sites are explicit
process_data(data, format="json")
process_data(data, format=None)  # Explicitly choosing auto-detection
```

### 4. Code in `__init__.py`

```python
# ❌ WRONG: Code in __init__.py
"""Configuration module."""
from workstack.config.loader import load_config
from workstack.config.writer import write_config
__all__ = ["load_config", "write_config"]

# ✅ CORRECT: Empty __init__.py
# (file is completely empty or docstring-only)

# ✅ Use absolute imports instead
from workstack.config import load_config
from workstack.core import discover_repo_context
```

**Exception**: Package entry points may contain minimal initialization code.

### 5. Speculative Tests

```python
# ❌ FORBIDDEN: Tests for future features
# def test_feature_we_might_add_next_month():
#     """Placeholder for feature we're considering."""
#     pass

# ✅ CORRECT: TDD for feature being implemented NOW
def test_new_feature_im_building_today():
    """Test for feature I'm about to implement."""
    result = feature_function()  # Will implement after this test
    assert result == expected_value
```

**Rule**: Only write tests for actively implemented code. TDD is encouraged.

---

## WHEN EXCEPTIONS ARE ACCEPTABLE

### 1. Error Boundaries

```python
# ✅ ACCEPTABLE: CLI command error boundary
@click.command("create")
@click.pass_obj
def create(ctx: WorkstackContext, name: str) -> None:
    """Create a worktree."""
    try:
        create_worktree(ctx, name)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error: Git command failed: {e.stderr}", err=True)
        raise SystemExit(1)
```

### 2. API Compatibility

```python
# ✅ ACCEPTABLE: Third-party API forces exception handling
def _get_bigquery_sample(sql_client, table_name):
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
```

### 3. Embellishing Exceptions

```python
# ✅ ACCEPTABLE: Adding context before re-raising
try:
    process_file(config_file)
except yaml.YAMLError as e:
    raise ValueError(f"Failed to parse config file {config_file}: {e}") from e
```

### Encapsulation Pattern

**When violating exception norms is necessary, encapsulate the violation:**

```python
# ✅ GOOD: Exception handling encapsulated in helper function
def _get_bigquery_sample_with_alternate(sql_client, table_name, percentage, limit):
    """Try TABLESAMPLE, use alternate for views (exception documented)."""
    try:
        return sql_client.run_query(f"SELECT * FROM {table_name} TABLESAMPLE...")
    except Exception:
        return sql_client.run_query(f"SELECT * FROM {table_name} ORDER BY RAND()...")

# Usage - caller doesn't see the exception handling
def analyze_table(table_name):
    sample = _get_bigquery_sample_with_alternate(sql_client, table_name, 10, 1000)
    return analyze_sample(sample)
```

---

## CHECKLIST BEFORE WRITING CODE

Before writing `try/except`:

- [ ] Is this at an error boundary? (CLI level, API boundary)
- [ ] Can I check the condition proactively instead? (LBYL approach)
- [ ] Am I adding meaningful context, or just hiding the error?
- [ ] Is a third-party API forcing me to use exceptions? (Document why)
- [ ] Have I encapsulated the violation in a helper function?
- [ ] Am I catching specific exceptions, not broad `Exception`?

**Default answer should be: Let the exception bubble up.**

Before using legacy type syntax:

- [ ] Am I using `list[...]`, `dict[...]`, `str | None`?
- [ ] Have I removed `from __future__ import annotations`?
- [ ] Have I removed `List`, `Dict`, `Optional`, `Union` imports?

Before path operations:

- [ ] Did I check `.exists()` before `.resolve()`?
- [ ] Did I check `.exists()` before `.is_relative_to()`?
- [ ] Am I using `pathlib.Path`, not `os.path`?

---

## COMMON PATTERNS SUMMARY

| Scenario              | Preferred Approach                        | Avoid                                       |
| --------------------- | ----------------------------------------- | ------------------------------------------- |
| **Dictionary access** | `if key in dict:` or `.get(key, default)` | `try: dict[key] except KeyError:`           |
| **File existence**    | `if path.exists():`                       | `try: open(path) except FileNotFoundError:` |
| **Type checking**     | `if isinstance(obj, Type):`               | `try: obj.method() except AttributeError:`  |
| **Value validation**  | `if is_valid(value):`                     | `try: process(value) except ValueError:`    |
| **Optional feature**  | `if has_feature(obj):`                    | `try: use_feature(obj) except:`             |
| **Path resolution**   | `if path.exists(): path.resolve()`        | `try: path.resolve() except OSError:`       |

---

## REFERENCES

For more detailed information, consult:

- **CLAUDE.md** - Core coding standards and quick reference table
- **.agent/docs/EXCEPTION_HANDLING.md** - Complete exception handling guide
- **.agent/docs/PATTERNS.md** - Comprehensive code examples
- **.agent/docs/QUICK_REFERENCE.md** - Quick lookup reference
- **tests/CLAUDE.md** - Testing patterns and practices

---

## QUICK DECISION TREE

**Writing Python code in workstack?**

1. **About to use `try/except`?**
   - → Check [Exception Handling](#1-exception-handling---never-for-control-flow-) section
   - → Can you use LBYL instead?
   - → Is this an error boundary?

2. **Using type hints?**
   - → Use `list[str]`, `dict[str, Any]`, `str | None`
   - → NO `List`, `Dict`, `Optional`, `Union`
   - → NO `from __future__ import annotations`

3. **Working with paths?**
   - → Check `.exists()` first
   - → Always use `pathlib.Path`
   - → Specify `encoding="utf-8"`

4. **Writing CLI code?**
   - → Use `click.echo()`, not `print()`
   - → Use `subprocess.run(..., check=True)`
   - → Exit with `raise SystemExit(1)`

5. **Creating interfaces?**
   - → Use `abc.ABC`, not `Protocol`
   - → Use frozen dataclasses for data

6. **Nesting > 4 levels?**
   - → Extract helper functions
   - → Use early returns

**When in doubt**: Check the references above or ask!
