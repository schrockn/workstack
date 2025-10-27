# dot-agent

CLI tool for managing Claude Code agent kits.

## Installation

```bash
# Install from PyPI (when published)
uv pip install dot-agent

# Install from source
uv pip install -e packages/dot-agent
```

## Usage

### Search for kits in the registry

Search for available kits by keyword:

```bash
dot-agent search graphite
# Output:
# gt-dot-agent-kit  https://github.com/dagsterlabs/gt-dot-agent-kit
#   Graphite (gt) CLI tool support for Claude Code

dot-agent search work
# Output:
# workstack-dot-agent-kit  https://github.com/workstack/workstack-dot-agent-kit
#   Workstack worktree management for Claude Code
```

### Install a kit

There are three ways to install a kit:

1. **From a Python package (already installed)**:

```bash
# First install the package
uv pip install gt-dot-agent-kit

# Then initialize it
dot-agent init --package gt-dot-agent-kit
```

2. **From a GitHub repository**:

```bash
# First install from GitHub
uv pip install git+https://github.com/dagsterlabs/gt-dot-agent-kit

# Then initialize it
dot-agent init --github https://github.com/dagsterlabs/gt-dot-agent-kit
```

3. **From the registry by name**:

```bash
# Install the package first
uv pip install git+https://github.com/dagsterlabs/gt-dot-agent-kit

# Then initialize by registry name
dot-agent init --kit gt-dot-agent-kit
```

Use `--force` to overwrite existing files:

```bash
dot-agent init --package gt-dot-agent-kit --force
```

### Check installed kits

Check the status of all installed kits:

```bash
dot-agent check
# Output:
# ✓ gt-dot-agent-kit v1.0.0 - synchronized
# ✓ workstack-dot-agent-kit v2.1.0 - synchronized

# With validation
dot-agent check --validate
```

### Sync kits to latest versions

Update all installed kits to their latest versions:

```bash
# Preview what would be updated
dot-agent sync --dry-run

# Perform the sync
dot-agent sync
# Output:
# ✓ Updated gt-dot-agent-kit 1.0.0 → 1.1.0
# ✓ workstack-dot-agent-kit v2.1.0 - up to date
```

## Configuration

dot-agent stores its configuration in `dot-agent.toml` in your project root:

```toml
version = "1.0.0"
root_dir = ".claude"
conflict_policy = "error"  # Options: error, skip, overwrite, merge
disabled_artifacts = []

[kits.gt-dot-agent-kit]
kit_id = "gt-dot-agent-kit"
package_name = "gt-dot-agent-kit"
version = "1.0.0"
artifacts = ["commands/gt.md", "skills/graphite.md"]
install_date = "2024-01-01T00:00:00"
source_type = "standalone"
```

## Kit Structure

A dot-agent kit must contain:

1. **kit.yaml** - Kit manifest file:

```yaml
kit_id: my-dot-agent-kit
version: 1.0.0
description: My custom Claude Code kit
artifacts:
  - source: commands/my-command.md
    dest: commands/my-command.md
    type: command
  - source: skills/my-skill.md
    dest: skills/my-skill.md
    type: skill
requires_python: ">=3.11"
dependencies: []
```

2. **Artifact files** - Commands, skills, scripts with optional frontmatter:

```markdown
<!-- dot-agent-kit:
kit_id: my-dot-agent-kit
version: 1.0.0
type: command
tags: [utility, automation]
-->

# My Command

Command documentation here...
```

## Development

```bash
# Install for development with test dependencies
uv pip install -e "packages/dot-agent[test]"

# Run tests
python -m pytest tests

# Run specific test
python -m pytest tests/test_search.py -xvs

# Run with coverage
python -m pytest tests --cov=dot_agent --cov-report=html

# Type checking
uv run pyright src/

# Format code
uv run ruff format src/ tests/

# Lint code
uv run ruff check src/ tests/
```

## Creating a Kit

To create your own dot-agent kit:

1. Create a Python package with the following structure:

```
my-dot-agent-kit/
├── pyproject.toml
├── kit.yaml
├── commands/
│   └── my-command.md
└── skills/
    └── my-skill.md
```

2. Add the kit manifest (`kit.yaml`)
3. Add your artifacts with proper frontmatter
4. Publish to PyPI or GitHub
5. Submit to the registry via PR

## License

MIT
