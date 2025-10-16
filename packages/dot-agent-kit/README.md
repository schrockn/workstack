# dot-agent-kit

dot-agent-kit is a CLI companion that manages the `.agent/` documentation directory in a repository. It installs the `dot-agent` command, ships curated mental-model documentation for tools like Graphite (`gt`), GitHub CLI (`gh`), and Workstack, and keeps local copies synchronized with the versions distributed by the package.

## Installation

```bash
pip install dot-agent-kit
# or
uv add dot-agent-kit
```

## Usage

```bash
# Initialize a repository with the default .agent layout
dot-agent init

# Update bundled documentation in the current .agent directory
dot-agent sync

# Preview updates without writing
dot-agent sync --dry-run

# List available documentation files
dot-agent list

# Extract one file explicitly
dot-agent extract tools/gt.md

# Compare local changes to the packaged version
dot-agent diff tools/gt.md

# Review sync status and pending updates
dot-agent check
```

## Configuration

The tool writes `.agent/.dot-agent-kit.yml` to track which files are installed and the version of dot-agent-kit used the last time the folder was updated. Custom documentation can be added alongside the installed files; the CLI leaves entries listed under `custom_files` untouched.

## Development

```bash
uv run pytest packages/dot-agent-kit/tests
uv run ruff format packages/dot-agent-kit
uv run pyright packages/dot-agent-kit/src
```

The package targets Python 3.13 and follows the Workstack coding standards (LBYL exception handling, absolute imports, Click for CLI output).
