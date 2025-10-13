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

Defined in `packages/workstack-dev/pyproject.toml`:

```toml
[project.scripts]
workstack-dev = "workstack_dev.__main__:cli"
```

### Core Components

```
packages/workstack-dev/
├── pyproject.toml
├── src/workstack_dev/
│   ├── __main__.py          # Entry point - uses devclikit framework
│   └── commands/            # Auto-discovered commands (examples below)
│       ├── clean_cache/
│       │   ├── command.py   # Click command definition
│       │   └── script.py    # PEP 723 implementation
│       ├── codex_review/
│       │   ├── command.py   # Click command definition
│       │   ├── script.py    # PEP 723 implementation
│       │   └── prompt.txt   # Codex prompt template
│       ├── completion/
│       │   ├── command.py   # Click command definition
│       │   └── script.py    # PEP 723 implementation
│       ├── create_agents_symlinks/
│       │   ├── command.py   # Click command definition
│       │   └── script.py    # PEP 723 implementation
│       ├── publish_to_pypi/
│       │   ├── command.py   # Click command definition
│       │   └── script.py    # PEP 723 implementation
│       └── ...              # Additional commands follow same pattern
└── tests/                   # Tests for workstack-dev commands

packages/devclikit/          # CLI framework (provides discovery & execution)
└── src/devclikit/
    ├── __init__.py          # Public API exports
    ├── cli_factory.py       # create_cli() factory function
    ├── loader.py            # Command discovery and dynamic loading
    ├── runner.py            # PEP 723 script execution
    ├── completion.py        # Shell completion support
    ├── exceptions.py        # Framework exceptions
    └── utils.py             # Shared utilities
```

**Note:** The commands listed above are examples. New commands can be added at any time by creating a new directory under `commands/` with the standard `command.py` and `script.py` files. The CLI framework automatically discovers all commands.

### CLI Initialization

The `__main__.py` uses the `devclikit.create_cli()` factory to construct the CLI:

```python
from pathlib import Path
from devclikit import create_cli

cli = create_cli(
    name="workstack-dev",
    description="Development tools for workstack.",
    commands_dir=Path(__file__).parent / "commands",
    add_completion=True,
)

if __name__ == "__main__":
    cli()
```

The `create_cli()` factory automatically:

- Creates a Click group with the specified name and description
- Discovers and registers all commands from the `commands_dir`
- Adds shell completion support (bash/zsh/fish)
- Returns a ready-to-use Click group

### Command Discovery System

**Provided by: `devclikit` framework**

The `devclikit.loader.load_commands()` function implements automatic command discovery:

1. **Scan** `commands/` directory for subdirectories
2. **Find** `command.py` files in each subdirectory
3. **Import** each command module dynamically using `importlib.util`
4. **Extract** Click command objects via inspection
5. **Register** commands with kebab-case names derived from directory names

```python
def load_commands(
    commands_dir: Path,
    *,
    verbose: bool = False,
    strict: bool = False,
) -> dict[str, click.Command]:
    """Discover and load all commands from a directory."""
    # Scans for subdirectories containing command.py files
    # Dynamically imports and extracts Click commands
    # Returns mapping of command name to Click command object
```

**Error handling:** Broken command modules are caught and logged without breaking the entire CLI (when `strict=False`).

See `packages/devclikit/README.md` for full framework documentation.

### Command Structure Pattern

Each command follows a **two-file pattern**:

#### 1. `command.py` - Click Interface

Defines the CLI interface using Click decorators:

```python
# commands/my_command/command.py
import click
from pathlib import Path
from devclikit import run_pep723_script

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
- Forward arguments to script.py via `devclikit.run_pep723_script()`

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

**Required structure** (see `packages/workstack-dev/src/workstack_dev/CLAUDE.md` for full details):

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

**Provided by: `devclikit.runner`**

The `run_pep723_script()` function provides a standardized way to execute PEP 723 scripts:

```python
def run_pep723_script(
    script_path: Path | str,
    args: list[str] | None = None,
    *,
    check: bool = True,
    capture_output: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Run a PEP 723 inline script using uv run."""
    # Builds command: ["uv", "run", script_path, *args]
    # Executes with subprocess.run()
    # Provides helpful error message if uv not installed
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

1. **Create directory:** `packages/workstack-dev/src/workstack_dev/commands/my_feature/`

2. **Create `command.py`:**

   ```python
   import click
   from pathlib import Path
   from devclikit import run_pep723_script

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
- **workstack-dev** (`packages/workstack-dev/src/workstack_dev/__main__.py`) - Development tools

Both are defined in their respective `pyproject.toml` files as separate entry points.

## Dependencies

**Framework dependencies:**

- `devclikit` - CLI framework package (in `packages/devclikit/`)
- `click>=8.1.7` - CLI framework used by both workstack-dev and devclikit

**Command-specific dependencies:**

- Declared inline via PEP 723 in each `script.py`
- Examples: `rich`, `build`, `twine`, etc.
- Only loaded when running that specific command
- Isolated from main project dependencies

**Architecture note:** The `devclikit` framework is an independent package that provides the command discovery and execution infrastructure. Commands in `workstack_dev.commands` use the framework's facilities but remain organizationally separate.

## Testing

**Location:** `packages/workstack-dev/tests/`

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

## Framework Reusability

The `devclikit` framework is designed to be reusable for other projects. It provides:

- **Zero-config command discovery** - Just drop commands in a directory
- **PEP 723 script execution** - Commands manage their own dependencies
- **Shell completion** - Built-in bash/zsh/fish support
- **Factory function** - Simple `create_cli()` API

See `packages/devclikit/README.md` and `packages/devclikit/src/devclikit/examples/` for documentation and examples on using the framework in other projects.
