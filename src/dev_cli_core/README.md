# dev_cli_core

**Framework for building development CLIs with automatic command discovery and PEP 723 script support.**

A lightweight, opinionated framework for creating Click-based development CLIs that automatically discover and load commands from a directory structure.

## Features

- **Automatic command discovery** - Load commands from directory structure (`commands/*/command.py`)
- **PEP 723 script execution** - Run inline dependency scripts with `uv run`
- **Shell completion** - Built-in bash/zsh/fish completion support
- **Zero configuration** - Sensible defaults with optional customization
- **Type-safe** - Full type annotations for Python 3.13+

## Examples

See [examples/](examples/) for complete working examples:

- **[hello_world](examples/hello_world/)** - Simple CLI demonstrating core concepts

## Quick Start

### Creating a CLI

```python
from dev_cli_core import create_cli

# Create CLI with automatic command discovery
cli = create_cli(
    name="myproject-dev",
    description="Development tools for myproject",
    commands_dir="./dev_cli/commands",
    version="1.0.0",
)

if __name__ == "__main__":
    cli()
```

### Directory Structure

```
dev_cli/
├── commands/
│   ├── test/
│   │   └── command.py      # Implements 'test' command
│   ├── format/
│   │   └── command.py      # Implements 'format' command
│   └── build/
│       └── command.py      # Implements 'build' command
└── __main__.py             # CLI entry point
```

### Command Implementation

Each `command.py` must export a Click command or group:

```python
"""Test command."""

import click

@click.command()
@click.option("--verbose", "-v", is_flag=True)
def command(verbose: bool) -> None:
    """Run test suite."""
    click.echo("Running tests...")
```

The framework looks for:

1. An attribute named `command`
2. Any `click.Command` or `click.Group` instance

## Core Modules

### cli_factory

High-level API for creating CLIs:

```python
from dev_cli_core.cli_factory import create_cli

cli = create_cli(
    name="my-cli",
    description="My development CLI",
    commands_dir="./commands",
    version="1.0.0",              # Optional: adds 'version' command
    add_completion=True,           # Optional: adds 'completion' group
    context_settings=None,         # Optional: Click context settings
)
```

### loader

Command discovery and dynamic loading:

```python
from pathlib import Path
from dev_cli_core.loader import load_commands

# Load all commands from directory
commands = load_commands(
    Path("./commands"),
    verbose=True,    # Print loading progress
    strict=False,    # Warn on errors (vs raise)
)

# Returns: dict[str, click.Command]
```

**Loading behavior:**

- Scans for subdirectories (ignoring `_*` and `.*`)
- Looks for `command.py` in each subdirectory
- Dynamically imports and extracts Click commands
- Directory name becomes command name (underscores converted to hyphens)

### runner

Execute PEP 723 inline scripts with `uv`:

```python
from dev_cli_core.runner import run_pep723_script

# Run script with uv
result = run_pep723_script(
    "scripts/deploy.py",
    args=["--env", "staging"],
    check=True,           # Raise on non-zero exit
    capture_output=False, # Stream output to console
)
```

**PEP 723 validation:**

```python
from dev_cli_core.runner import validate_pep723_script

if validate_pep723_script(Path("script.py")):
    click.echo("Valid PEP 723 script")
```

### completion

Shell completion support:

```python
from dev_cli_core.completion import add_completion_commands

# Adds 'completion bash/zsh/fish' commands
add_completion_commands(cli, "my-cli")
```

**Usage:**

```bash
# Generate and load completion
source <(my-cli completion bash)

# Install permanently
echo 'source <(my-cli completion bash)' >> ~/.bashrc
```

### exceptions

Framework exceptions:

```python
from dev_cli_core.exceptions import (
    DevCliFrameworkError,     # Base exception
    CommandLoadError,         # Command loading failed
    ScriptExecutionError,     # Script execution failed
)
```

### utils

Shared utilities:

```python
from dev_cli_core.utils import ensure_directory, is_valid_command_name

# Create directory if needed
ensure_directory(Path("./output"))

# Validate command names
assert is_valid_command_name("my-command")
assert not is_valid_command_name("My_Command")  # Uppercase not allowed
```

## Command Discovery

The loader scans the commands directory for this structure:

```
commands/
├── command-name/
│   └── command.py      # Must contain Click command
├── another-cmd/
│   └── command.py
└── _internal/          # Ignored (starts with _)
    └── command.py
```

**Naming rules:**

- Directory name becomes command name
- Underscores converted to hyphens (`test_db` → `test-db`)
- Directories starting with `_` or `.` are skipped
- Command names must be lowercase alphanumeric with hyphens

**Command extraction:**

1. Looks for `command` attribute in module
2. Falls back to first `click.Command` or `click.Group` found
3. Skips if no command found (warns in verbose mode)

## PEP 723 Scripts

Execute self-contained Python scripts with inline dependencies:

```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#   "click>=8.1.7",
#   "requests>=2.31.0",
# ]
# requires-python = ">=3.13"
# ///
"""Deploy script with inline dependencies."""

import click
import requests

@click.command()
def deploy():
    click.echo("Deploying...")
```

**Run with uv:**

```python
from dev_cli_core.runner import run_pep723_script

run_pep723_script("deploy.py", args=["--env", "prod"])
```

The framework automatically:

- Validates PEP 723 metadata
- Executes with `uv run`
- Provides helpful error messages if `uv` not installed

## Complete Example

```python
# dev_cli/__main__.py
from pathlib import Path
from dev_cli_core import create_cli

cli = create_cli(
    name="myproject-dev",
    description="Development tools for myproject",
    commands_dir=Path(__file__).parent / "commands",
    version="1.0.0",
)

if __name__ == "__main__":
    cli()
```

```python
# dev_cli/commands/test/command.py
import click
import subprocess

@click.command()
@click.option("--watch", is_flag=True, help="Run in watch mode")
def command(watch: bool) -> None:
    """Run test suite with pytest."""
    cmd = ["pytest"]
    if watch:
        cmd.append("--watch")
    subprocess.run(cmd, check=True)
```

**Usage:**

```bash
python -m dev_cli test --watch
python -m dev_cli version
python -m dev_cli completion bash
```

## Design Principles

### Convention over Configuration

- Standard directory structure (`commands/*/command.py`)
- Automatic command naming from directories
- Zero-config command discovery

### Fail Fast

- Strict mode available for CI/CD
- Clear error messages with actionable guidance
- Validates PEP 723 scripts before execution

### Type Safety

- Full type annotations for all public APIs
- Python 3.13+ native type syntax (`list[str]`, `str | None`)
- pyright-validated type checking

### Error Boundaries

- Framework catches loading errors at boundaries
- Commands fail independently (no cascading failures)
- User-friendly error messages for missing dependencies

## Integration with workstack

This framework powers the `workstack-dev` CLI for workstack development:

```
workstack/
├── dev_cli/
│   ├── __main__.py         # Uses create_cli()
│   └── commands/
│       ├── test/           # Unit tests
│       ├── typecheck/      # pyright
│       ├── format/         # ruff format
│       └── agent-docs/     # Documentation
└── src/dev_cli_core/       # This framework
```

See `.agent/WORKSTACK_DEV.md` for architecture details.

## Templates

The `templates/` directory contains Jinja2 templates for scaffolding:

- `command.py.jinja` - Command template
- `script.py.jinja` - PEP 723 script template
- `__main__.py.jinja` - CLI entry point template
- `README.md.jinja` - Documentation template

These are used by scaffolding tools to generate new commands and CLIs.

## Requirements

- **Python 3.13+** - Native type syntax
- **Click 8.1+** - CLI framework
- **uv** - PEP 723 script execution (optional, runtime check)

## Related Documentation

- **Examples**: [examples/](examples/) - Complete working examples
- Main project: `../../README.md`
- Development CLI: `.agent/WORKSTACK_DEV.md`
- Coding standards: `../../CLAUDE.md`
