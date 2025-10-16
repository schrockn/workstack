# dot-agent-kit

dot-agent-kit is a CLI companion that manages the `.agent/` documentation directory in a repository. It installs the `dot-agent` command, ships curated mental-model documentation for tools like Graphite (`gt`), GitHub CLI (`gh`), and Workstack, and keeps local copies synchronized with the versions distributed by the package.

## Installation

```bash
pip install dot-agent-kit
# or
uv add dot-agent-kit
```

## Quick Start

```bash
# Initialize a repository with the default .agent layout
dot-agent init

# Update bundled documentation in the current .agent directory
dot-agent sync

# Preview updates without writing
dot-agent sync --dry-run

# List available documentation files
dot-agent list

# Display contents of a local file in .agent directory
dot-agent show ARCHITECTURE.md

# Review sync status and pending updates
dot-agent check
```

## Understanding the Package System

### What is a Package?

A **package** is a directory under `.agent/packages/` containing related documentation files. Packages organize curated documentation by theme or tool, making it easy for AI agents to discover and load relevant context.

**Package Structure:**

```
.agent/
  packages/                    # All installed packages live here
    tools/                     # Namespace for CLI tool documentation
      gt/                      # Package for Graphite CLI
        gt.md                  # Documentation files
      gh/                      # Package for GitHub CLI
        gh.md
    agentic_programming_guide/ # Root-level package (no namespace)
      AGENTIC_PROGRAMMING.md
```

### Installed Packages vs Local Files

**Installed Packages** (`packages/`):

- Managed by `dot-agent-kit`
- Synced from bundled resources, local paths, or git repositories
- Should not be edited directly (changes will be overwritten on next sync)
- Updated via `dot-agent sync`

**Local Files** (`.agent/` root):

- User-created project-specific documentation
- Never touched by `dot-agent sync`
- Can be any markdown or text files (e.g., `ARCHITECTURE.md`, `CUSTOM_RULES.md`)
- Read via `dot-agent show FILENAME.md`

### Namespaces

Packages can be organized into **namespaces** for logical grouping:

- **`tools/`**: Special namespace for CLI tool documentation
  - Convention: `tools/{name}/` provides docs for CLI command `{name}`
  - Example: `tools/gt/` contains documentation for the `gt` command
  - Enables automatic tool detection by AI agents

- **Custom namespaces**: You can create your own (e.g., `frameworks/`, `apis/`)

- **Root-level packages**: Packages without a namespace (e.g., `agentic_programming_guide/`)

**How namespaces work:**

- A directory is a namespace if it contains only subdirectories (no files)
- Each subdirectory within a namespace is a separate package
- Full package name format: `namespace/package` (e.g., `tools/gt`)

### Tool Registry

The package system includes a **Tool Registry** that automatically detects CLI tool mentions and loads relevant documentation.

**How it works:**

1. Agent detects a tool mention in conversation (e.g., "use `gt submit`")
2. Registry checks for matching package in `packages/tools/{tool-name}/`
3. If found, loads documentation files for that tool
4. Agent gains tool-specific context automatically

**Supported detection:**

- Word boundary matching: "use gt" → detects `gt`
- Command examples: "`gt log`" → detects `gt`
- Case-insensitive matching

**Programmatic usage:**

```python
from dot_agent_kit.packages.registry import ToolRegistry
from pathlib import Path

registry = ToolRegistry(Path(".agent"))

# Detect tools mentioned in text
tools = registry.detect_tool_mention("Use gt to submit your stack")
# Returns: ["gt"]

# Get tool context
context = registry.get_tool_context("gt")
# Returns: ToolContext with package info and file list
```

### Package Discovery

The `PackageManager` automatically discovers all packages:

```python
from dot_agent_kit.packages.manager import PackageManager
from pathlib import Path

manager = PackageManager(Path(".agent"))
packages = manager.discover_packages()

for name, pkg in packages.items():
    print(f"{name}: {len(pkg.files)} files at {pkg.install_path}")
```

**Discovery algorithm:**

1. Scans `.agent/packages/` directory
2. Identifies namespace directories (contain only subdirs, no files)
3. Loads package metadata for each package directory
4. Computes file hashes and metadata for all files in each package

## Configuration File

Location: `.agent/.dot-agent-kit.yml`

**Schema:**

```yaml
version: "0.2.0" # dot-agent-kit version that last updated
installed_files: # Files to install from bundled resources
  - AGENTIC_PROGRAMMING.md
  - tools/gt.md
  - tools/gh.md
  - tools/workstack.md
exclude: [] # Patterns to skip during sync
custom_files: # User-created files (tracked but never modified)
  - ARCHITECTURE.md
  - docs/guide.md
```

**Fields:**

- **`version`**: Version of dot-agent-kit that last updated the directory
- **`installed_files`**: List of bundled files to install (uses flat paths for backward compatibility with old structure)
- **`exclude`**: File patterns to skip during sync operations
- **`custom_files`**: User-created files that should be preserved across syncs

**Backward compatibility:** The config supports both `installed_files` (new) and `managed_files` (old) keys.

## Front Matter Support

Documentation files can include YAML front matter for metadata:

```markdown
---
description: "Mental model and command reference for Graphite (gt) CLI"
url: "https://graphite.dev/docs"
---

# Graphite (gt) Documentation

...
```

**Supported fields:**

- `description`: Short description (shown in `dot-agent list` output)
- `url`: Reference URL for external documentation

**Validation:** Run `dot-agent check` to validate front matter syntax in all files.

## Common Workflows

### First Time Setup

```bash
cd my-project
dot-agent init                    # Creates .agent/ with default packages
```

### Updating Installed Packages

```bash
dot-agent check                   # See what's out of date
dot-agent sync --dry-run          # Preview changes
dot-agent sync                    # Apply updates
```

### Working with Local Files

```bash
# Create custom documentation
echo "# Project Architecture" > .agent/ARCHITECTURE.md
echo "# Custom Rules" > .agent/CUSTOM_RULES.md

# Read local files
dot-agent show ARCHITECTURE.md

# List everything (installed + local)
dot-agent list
```

### Understanding What Changed

```bash
# Check status of all files
dot-agent check

# Shows:
# - Up-to-date files
# - Missing files (in config but not on disk)
# - Modified files (local changes vs bundled version)
# - Excluded files
# - Unavailable files (in config but not in bundled resources)
```

## Local File Discovery

The `LocalFileDiscovery` API helps discover user-created files in `.agent/`:

```python
from dot_agent_kit.local import LocalFileDiscovery
from pathlib import Path

discovery = LocalFileDiscovery(Path(".agent"))

# Discover all local files (excludes packages/)
local_files = discovery.discover_local_files()

# Filter by pattern
md_files = discovery.discover_local_files(pattern="*.md")

# Read a local file
content = discovery.read_file("ARCHITECTURE.md")

# Categorize by directory
categories = discovery.categorize_files(local_files)
for category, files in categories.items():
    print(f"{category}: {len(files)} files")
```

**What's discovered:**

- All files in `.agent/` root and subdirectories
- Excludes `packages/` (installed packages)
- Excludes hidden files (starting with `.`)
- Excludes `.dot-agent-kit.yml` config file

## CLI Commands Reference

| Command                    | Description                                              |
| -------------------------- | -------------------------------------------------------- |
| `dot-agent init`           | Initialize `.agent/` directory with default packages     |
| `dot-agent sync`           | Update installed packages from bundled resources         |
| `dot-agent sync --dry-run` | Preview sync changes without writing                     |
| `dot-agent list`           | List all available documentation files with descriptions |
| `dot-agent show FILE`      | Display contents of a local file (not in packages/)      |
| `dot-agent check`          | Check sync status and validate front matter              |

## Development

```bash
uv run pytest packages/dot-agent-kit/tests
uv run ruff format packages/dot-agent-kit
uv run pyright packages/dot-agent-kit/src
```

The package targets Python 3.13 and follows the Workstack coding standards (LBYL exception handling, absolute imports, Click for CLI output).

## Architecture Summary

**Core Components:**

- **`PackageManager`** (`packages/manager.py`) - Discovers and loads packages
- **`ToolRegistry`** (`packages/registry.py`) - Maps CLI tools to packages
- **`LocalFileDiscovery`** (`local.py`) - Discovers user-created files
- **`DotAgentConfig`** (`config.py`) - Manages `.dot-agent-kit.yml` configuration
- **`sync`** module (`sync.py`) - Handles file synchronization

**Data Models:**

- **`Package`** - Represents an installed package with namespace, name, path, and files
- **`FileInfo`** - Metadata for a file within a package (hash, size, mtime)
- **`LocalFile`** - Metadata for a user-created file in `.agent/` root
- **`ToolContext`** - Context for a specific CLI tool (package + files)
