# Dev CLI Implementation Guidelines

## Command Structure Patterns

There are two patterns for workstack-dev commands:

### Pattern 1: Direct Command (Recommended for Simple Commands)

For commands with simple logic that don't need external dependencies:

```
commands/
├── my-command/
│   ├── __init__.py   # Empty or docstring only
│   └── command.py    # Click command with all logic
```

**When to use:**

- Logic fits in a single file with standard dependencies
- No need for external packages beyond workstack-dev's dependencies
- Performance-critical operations that benefit from being directly imported

**Example:** `land-branch` command - all logic in `command.py`

### Pattern 2: PEP 723 Script (For Complex Commands)

For commands that need external dependencies or are self-contained scripts:

```
commands/
├── my-command/
│   ├── __init__.py   # Empty or docstring only
│   ├── command.py    # Click command that executes script.py
│   └── script.py     # PEP 723 inline script with implementation
```

**When to use:**

- Command needs external packages not in workstack-dev dependencies
- Logic is complex and benefits from isolation
- Script should be runnable independently

**Example:** `codex-review` command - uses script.py for independent execution

## PEP 723 Script Files (Pattern 2 Only)

**All `script.py` files in `commands/` subdirectories MUST follow this structure:**

```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#   "click>=8.1.7",
#   # ... other dependencies
# ]
# requires-python = ">=3.13"
# ///
"""Module docstring."""

# pyright: reportMissingImports=false

import ...
```

### Required Elements

1. **Shebang**: `#!/usr/bin/env python3`
2. **PEP 723 metadata block**: Inline script dependencies
3. **Module docstring**: Brief description of script purpose
4. **Pyright directive**: `# pyright: reportMissingImports=false` (after docstring, before imports)

### Why the Pyright Directive?

PEP 723 inline script dependencies are executed by `uv run` but aren't recognized by pyright during static analysis. The module-level directive suppresses false positive import warnings for script-declared dependencies.

### command.py (Pattern 2)

- Defines the Click command interface
- Uses `subprocess.run(["uv", "run", script_path], check=True)` to execute script.py
- Passes CLI options/flags to script.py

### script.py (Pattern 2)

- Contains the actual implementation logic
- PEP 723 inline script with its own dependencies
- Can be run directly with `uv run script.py`
- Must follow structure outlined above
