# Dev CLI Implementation Guidelines

## PEP 723 Script Files

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

## Command Structure

Each command lives in its own directory under `commands/`:

```
commands/
├── my-command/
│   ├── command.py    # Click command definition
│   └── script.py     # PEP 723 inline script with implementation
```

### command.py

- Defines the Click command interface
- Uses `subprocess.run(["uv", "run", script_path], check=True)` to execute script.py
- Passes CLI options/flags to script.py

### script.py

- Contains the actual implementation logic
- PEP 723 inline script with its own dependencies
- Can be run directly with `uv run script.py`
- Must follow structure outlined above
