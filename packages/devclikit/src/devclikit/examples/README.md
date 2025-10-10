# dev_cli_core Examples

This directory contains example implementations demonstrating how to use the dev_cli_core framework.

## Hello World

A simple hello world CLI that demonstrates the core concepts of dev_cli_core.

### Directory Structure

```
hello_world/
├── __main__.py              # CLI entry point
└── commands/
    └── hello/
        ├── command.py       # Click command definition
        └── script.py        # PEP 723 implementation
```

### Running the Example

From the `src/` directory:

```bash
cd src

# Run the hello command
python -m dev_cli_core.examples.hello_world hello

# With a custom name
python -m dev_cli_core.examples.hello_world hello --name Alice

# With uppercase flag
python -m dev_cli_core.examples.hello_world hello --name Bob --uppercase

# Get help
python -m dev_cli_core.examples.hello_world hello --help

# Show version
python -m dev_cli_core.examples.hello_world version

# Shell completion
python -m dev_cli_core.examples.hello_world completion bash
```

### What This Example Demonstrates

1. **CLI Creation**: Using `create_cli()` to set up a CLI with automatic command discovery
2. **Command Structure**: Organizing commands in the `commands/` directory
3. **Click Integration**: Defining commands with options and flags
4. **PEP 723 Scripts**: Using inline script dependencies for command implementation
5. **Framework Features**: Built-in version and completion commands

### Key Files Explained

#### `__main__.py`

The entry point that creates the CLI using `create_cli()`:

```python
from pathlib import Path
from dev_cli_core import create_cli

cli = create_cli(
    name="hello-world",
    description="Simple hello world CLI example",
    commands_dir=Path(__file__).parent / "commands",
    version="1.0.0",
)
```

#### `commands/hello/command.py`

The Click command definition that handles CLI options:

- Defines the command interface with Click decorators
- Passes options to the PEP 723 script using `run_pep723_script()`
- Keeps CLI logic separate from implementation

#### `commands/hello/script.py`

The PEP 723 script with the actual implementation:

- Contains inline dependencies (`click`, `rich`)
- Implements the greeting logic
- Can be run directly with `uv run script.py`

### Customizing This Example

To add a new command:

1. Create a new directory under `commands/`: `commands/goodbye/`
2. Add `command.py` with your Click command definition
3. Add `script.py` with your PEP 723 implementation
4. The framework will automatically discover and load it

Example:

```bash
mkdir -p commands/goodbye
# Create command.py and script.py following the pattern
python -m dev_cli_core.examples.hello_world goodbye
```

## Creating Your Own CLI

To create a new CLI based on this example:

1. Copy the `hello_world/` structure to your project
2. Update `__main__.py` with your CLI name and description
3. Add commands in the `commands/` directory
4. Run with `python -m your_module`

See the main [dev_cli_core README](../README.md) for more details on the framework.
