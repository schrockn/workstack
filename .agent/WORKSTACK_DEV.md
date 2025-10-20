# workstack-dev CLI Architecture

## Overview

`workstack-dev` is a **general-purpose development CLI** for tools and scripts used during workstack development. Commands are statically registered in `cli.py` to enable shell completion support.

**Key characteristics:**

- **Static imports**: Commands are explicitly imported and registered in `cli.py`
- **Single-file commands**: Each command's logic lives in one `command.py` file
- **Shell completion**: Click's completion requires static imports (not dynamic discovery)
- **Extensibility**: Adding new commands requires updating both the command file and `cli.py`

## Purpose

The `workstack-dev` CLI serves as a centralized home for development-time tools that don't belong in the main `workstack` user-facing CLI. These include:

- Build and release automation (e.g., `publish-to-pypi`)
- Maintenance tasks (e.g., `clean-cache`)
- Development utilities (e.g., `branch-commit-count`)
- Code review tooling (e.g., `codex-review`)
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
│   ├── __main__.py          # Entry point - imports cli from cli.py
│   ├── cli.py               # Static CLI definition with all command imports
│   ├── CLAUDE.md            # Implementation guidelines for AI assistants
│   └── commands/            # Command implementations
│       ├── branch_commit_count/
│       │   ├── __init__.py  # Optional docstring
│       │   └── command.py   # Full Click command implementation
│       ├── clean_cache/
│       │   └── command.py   # Full Click command implementation
│       ├── codex_review/
│       │   ├── command.py   # Full Click command implementation
│       │   └── prompt.txt   # Codex prompt template
│       ├── completion/
│       │   └── command.py   # Command group with subcommands
│       ├── create_agents_symlinks/
│       │   └── command.py   # Full Click command implementation
│       ├── land_branch/
│       │   ├── __init__.py  # Optional docstring
│       │   └── command.py   # Full Click command implementation
│       ├── publish_to_pypi/
│       │   └── command.py   # Full Click command implementation
│       └── reserve_pypi_name/
│           └── command.py   # Full Click command implementation
└── tests/                   # Tests for workstack-dev commands
```

### CLI Initialization

The `cli.py` module uses **static imports** to enable shell completion:

```python
"""Static CLI definition for workstack-dev.

This module uses static imports instead of dynamic command loading to enable
shell completion. Click's completion mechanism requires all commands to be
available at import time for inspection.
"""

import click

from workstack_dev.commands.branch_commit_count.command import branch_commit_count_command
from workstack_dev.commands.clean_cache.command import clean_cache_command
from workstack_dev.commands.codex_review.command import codex_review_command
# ... more imports

@click.group(name="workstack-dev")
def cli() -> None:
    """Development tools for workstack."""
    pass

# Register all commands
cli.add_command(branch_commit_count_command)
cli.add_command(clean_cache_command)
cli.add_command(codex_review_command)
# ... more registrations
```

**Why static imports?** Click's shell completion system inspects the CLI at import time to generate completion scripts. Dynamic command loading breaks this inspection mechanism.

### Command Structure Pattern

Each command follows a **single-file pattern** with all logic in `command.py`:

```python
# commands/my_command/command.py
"""Command description."""

import subprocess
from pathlib import Path

import click


@click.command(name="my-command")
@click.option("--dry-run", is_flag=True, help="Show what would be done")
def my_command_command(dry_run: bool) -> None:
    """Command description shown in --help."""
    # All implementation logic goes here
    if dry_run:
        click.echo("Would perform action...")
    else:
        click.echo("Performing action...")
```

**Critical naming convention:** The function MUST be named `{command_name}_command` (e.g., `my_command_command`) to match the import in `cli.py`.

### Command Types

#### Standard Commands

Most commands use `@click.command()`:

```python
@click.command(name="branch-commit-count")
def branch_commit_count_command() -> None:
    """Count commits on current branch since Graphite parent."""
    # Implementation
```

#### Command Groups (Subcommands)

Commands with subcommands use `@click.group()`:

```python
@click.group(name="completion")
def completion_command() -> None:
    """Generate shell completion scripts."""
    pass

@completion_command.command(name="bash")
def bash() -> None:
    """Generate bash completion script."""
    # Implementation
```

## Adding a New Command

To add a new command to `workstack-dev`:

1. **Create command directory:**

   ```bash
   mkdir -p packages/workstack-dev/src/workstack_dev/commands/my_command
   ```

2. **Create `command.py`:**

   ```python
   """Command description."""

   import click

   @click.command(name="my-command")
   def my_command_command() -> None:
       """Command help text."""
       click.echo("Hello from my-command!")
   ```

3. **Update `cli.py`:**

   ```python
   # Add import
   from workstack_dev.commands.my_command.command import my_command_command

   # Add registration
   cli.add_command(my_command_command)
   ```

4. **Optionally add `__init__.py`:**
   ```python
   """My command."""
   ```

## Implementation Guidelines

See `packages/workstack-dev/src/workstack_dev/CLAUDE.md` for detailed implementation guidelines including:

- Function naming conventions (`{command_name}_command`)
- Static import architecture requirements
- Click usage patterns
- Command group patterns
- Examples of existing commands

## Testing

Tests for workstack-dev commands follow standard pytest patterns and are located in the `tests/` directory.
