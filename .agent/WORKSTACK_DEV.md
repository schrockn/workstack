# workstack-dev CLI Architecture

## Overview

`workstack-dev` is a **general-purpose development CLI** for tools and scripts used during workstack development. It provides a plugin-style architecture where new commands can be added without modifying the core CLI code.

**Key characteristics:**

- **Auto-discovery**: Commands are automatically discovered and registered
- **PEP 723 inline scripts**: Each command's implementation uses inline dependency declarations
- **Isolation**: Commands manage their own dependencies independently
- **Extensibility**: Adding new commands requires no changes to the CLI framework

## Purpose

The `workstack-dev` CLI serves as a centralized home for development-time tools that don't belong in the main `workstack` user-facing CLI. These include:

- Build and release automation (e.g., `publish-to-pypi`)
- Maintenance tasks (e.g., `clean-cache`)
- Development utilities
- Project-specific tooling

## Architecture

### Entry Point

Defined in `pyproject.toml:16`:

```toml
[project.scripts]
workstack-dev = "workstack.dev_cli.__main__:cli"
```

### Core Components

```
src/workstack/dev_cli/
├── __main__.py          # Entry point - creates Click group and auto-registers commands
├── loader.py            # Command discovery and dynamic loading
├── utils.py             # Shared utilities (PEP 723 script runner)
└── commands/
    ├── clean_cache/
    │   ├── command.py   # Click command definition
    │   └── script.py    # PEP 723 implementation
    └── publish_to_pypi/
        ├── command.py   # Click command definition
        └── script.py    # PEP 723 implementation
```

### Command Discovery System

**File: `src/workstack/dev_cli/loader.py`**

The `load_commands()` function implements automatic command discovery:

1. **Scan** `commands/` directory for subdirectories
2. **Find** `command.py` files in each subdirectory
3. **Import** each command module dynamically using `importlib.util`
4. **Extract** Click command objects via inspection
5. **Register** commands with kebab-case names derived from directory names

```python
def load_commands() -> dict[str, click.Command]:
    """Discover and load all commands from the commands directory."""
    discovered_commands: dict[str, click.Command] = {}
    commands_dir = Path(__file__).parent / "commands"

    for cmd_dir in commands_dir.iterdir():
        if not cmd_dir.is_dir() or cmd_dir.name.startswith("_"):
            continue

        command_file = cmd_dir / "command.py"
        if not command_file.exists():
            continue

        # Dynamic import and inspection...
        # (see src/workstack/dev_cli/loader.py:32-52 for full implementation)
```

**Error handling:** Broken command modules are caught and logged without breaking the entire CLI (`loader.py:41-45`).

### Command Structure Pattern

Each command follows a **two-file pattern**:

#### 1. `command.py` - Click Interface

Defines the CLI interface using Click decorators:

```python
# commands/my_command/command.py
import click
from pathlib import Path
from workstack.dev_cli.utils import run_pep723_script

@click.command(name="my-command")
@click.option("--dry-run", is_flag=True, help="Show what would be done")
def command(dry_run: bool) -> None:
    """Command description."""
    script_path = Path(__file__).parent / "script.py"

    args = []
    if dry_run:
        args.append("--dry-run")

    run_pep723_script(script_path, args)
```

**Responsibilities:**

- Define Click command name and options
- Parse CLI flags/arguments
- Forward arguments to script.py

#### 2. `script.py` - PEP 723 Implementation

Contains the actual implementation using PEP 723 inline dependencies:

```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#   "click>=8.1.7",
#   "rich>=13.0.0",
# ]
# requires-python = ">=3.13"
# ///
"""Implementation logic."""

# pyright: reportMissingImports=false

import click
from rich.console import Console

@click.command()
@click.option("--dry-run", is_flag=True)
def main(dry_run: bool) -> None:
    """Execute the command logic."""
    # Implementation here...

if __name__ == "__main__":
    main()
```

**Responsibilities:**

- Implement the command logic
- Declare inline dependencies via PEP 723
- Run via `uv run script.py`

### PEP 723 Inline Script Architecture

**PEP 723** (Inline script metadata) allows scripts to declare their dependencies directly in the file using a special comment block.

**Required structure** (`src/workstack/dev_cli/CLAUDE.md:8-18`):

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

**Critical directive:** `# pyright: reportMissingImports=false`

This suppresses false positive import warnings because pyright performs static analysis without running `uv`, so it doesn't see the PEP 723 dependencies. The directive MUST appear after the docstring and before imports.

### Script Execution Utility

**File: `src/workstack/dev_cli/utils.py:9-27`**

The `run_pep723_script()` function provides a standardized way to execute PEP 723 scripts:

```python
def run_pep723_script(script_path: Path, args: list[str] | None = None) -> None:
    """Run a PEP 723 inline script using uv run."""
    cmd = ["uv", "run", str(script_path)]
    if args:
        cmd.extend(args)

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Command failed with exit code {e.returncode}", err=True)
        raise SystemExit(1) from e
```

**Why `uv run`?**

`uv run` automatically:

1. Parses the PEP 723 metadata block
2. Creates a temporary virtual environment
3. Installs declared dependencies
4. Executes the script with those dependencies available

## Design Rationale

### Why Two Files Per Command?

**Separation of concerns:**

1. **`command.py`** - CLI interface layer
   - Uses project dependencies (click from main pyproject.toml)
   - Defines user-facing interface
   - Thin wrapper around script execution

2. **`script.py`** - Implementation layer
   - Declares its own dependencies via PEP 723
   - Can use specialized libraries without polluting main project
   - Can be run directly during development: `uv run script.py`

**Benefits:**

- Command implementations don't bloat main project dependencies
- Scripts can be tested independently
- Clear separation between interface and implementation
- Easy to extract scripts for standalone use

### Why Auto-Discovery?

**Eliminates boilerplate:**

- No manual command registration in `__main__.py`
- Adding a command = create directory with two files
- No central import or decorator registry

**Convention-based:**

- Directory name → command name (with underscores converted to hyphens)
- Standard file names (`command.py`, `script.py`)
- Predictable structure across all commands

## Adding New Commands

To add a new command:

1. **Create directory:** `src/workstack/dev_cli/commands/my_feature/`

2. **Create `command.py`:**

   ```python
   import click
   from pathlib import Path
   from workstack.dev_cli.utils import run_pep723_script

   @click.command(name="my-feature")
   def command() -> None:
       """Brief description."""
       script_path = Path(__file__).parent / "script.py"
       run_pep723_script(script_path)
   ```

3. **Create `script.py`:**

   ```python
   #!/usr/bin/env python3
   # /// script
   # dependencies = ["click>=8.1.7"]
   # requires-python = ">=3.13"
   # ///
   """Implementation."""

   # pyright: reportMissingImports=false

   import click

   @click.command()
   def main() -> None:
       """Execute the command."""
       pass

   if __name__ == "__main__":
       main()
   ```

4. **Test:** `workstack-dev my-feature`

No other changes needed - the command is automatically discovered and registered.

## Integration with Main CLI

The `workstack-dev` CLI is **completely separate** from the main `workstack` CLI:

- **workstack** (`src/workstack/__main__.py`) - User-facing worktree management
- **workstack-dev** (`src/workstack/dev_cli/__main__.py`) - Development tools

Both are defined in `pyproject.toml:14-16` as separate entry points.

## Dependencies

**Main project dependencies** (`pyproject.toml:10-12`):

```toml
dependencies = ["click>=8.1.7"]
```

**Command-specific dependencies:**

- Declared inline via PEP 723 in each `script.py`
- Examples: `rich`, `build`, `twine`, etc.
- Only loaded when running that specific command

## Testing

**Location:** `tests/dev_cli/`

Commands can be tested at two levels:

1. **Script level:** Test `script.py` implementation directly
2. **Command level:** Test full CLI integration via Click's testing utilities

See `tests/CLAUDE.md` for testing patterns.

## Future Extensions

The plugin architecture enables easy addition of:

- Code generation tools
- Database migration helpers
- Documentation generators
- Release automation variants
- Custom linters/analyzers

All without modifying the core CLI framework.
