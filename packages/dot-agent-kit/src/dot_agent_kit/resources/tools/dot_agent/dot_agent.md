---
description: CLI tool for managing .agent/ documentation directories
url: https://github.com/anthropics/dot-agent-kit
---

# dot-agent CLI Reference

`dot-agent` is a command-line tool for managing `.agent/` directories containing curated documentation and context for AI agents.

## Core Concepts

### Package System

The `.agent/packages/` directory contains documentation installed and managed by dot-agent-kit:

- **Bundled packages**: Synced from dot-agent-kit releases
- **Tool packages**: Documentation for CLI tools at `packages/tools/{tool-name}/`
- **Guide packages**: General documentation like `packages/agentic_programming_guide/`

### Immutability of Package Files

🔴 **CRITICAL**: Files in `.agent/packages/` are managed by dot-agent and should never be edited directly.

- Modifications will be overwritten by `dot-agent sync`
- Use `dot-agent check` to verify package integrity
- Root-level files in `.agent/` are project-specific and safe to edit

## Commands

### `dot-agent init`

Initialize a new `.agent/` directory in the current repository.

```bash
dot-agent init
```

Creates:

- `.agent/` directory
- `.agent/packages/` with all available documentation

**When to use**: First-time setup in a new repository.

### `dot-agent sync`

Update installed packages to match the current dot-agent-kit version.

```bash
dot-agent sync              # Update all packages
dot-agent sync --dry-run    # Preview changes without writing
dot-agent sync --force      # Update without showing diffs
```

**Behavior**:

- Creates missing package files
- Updates modified package files to bundled versions
- Shows diffs for changed files (unless --force)

**When to use**:

- After upgrading dot-agent-kit
- To restore modified package files
- To add newly available packages

### `dot-agent check`

Verify that installed packages match bundled versions.

```bash
dot-agent check
```

**Reports**:

- Up-to-date files (matching bundled version)
- Missing files (should exist but don't)
- Modified files (differ from bundled version)
- Unavailable files (in config but not shipped)
- Front matter validation errors

**Exit codes**:

- `0`: All package files are up-to-date
- `1`: Package files have been modified or are missing

**When to use**:

- Before committing changes
- In CI/CD pipelines
- To verify package integrity

### `dot-agent list`

Show all available documentation packages.

```bash
dot-agent list
```

Displays:

- File paths relative to `.agent/packages/`
- Descriptions from YAML front matter
- Documentation URLs

**When to use**: To discover available packages and their purposes.

## Common Workflows

### Initial Setup

```bash
# Initialize .agent directory
cd /path/to/repository
dot-agent init

# Verify installation
dot-agent check
```

### Updating Packages

```bash
# Preview what would change
dot-agent sync --dry-run

# Apply updates
dot-agent sync

# Verify integrity
dot-agent check
```

### Restoring Modified Files

If you accidentally edit package files:

```bash
# Check what's been modified
dot-agent check

# Restore to bundled versions
dot-agent sync
```

### CI/CD Integration

```yaml
# .github/workflows/validate.yml
- name: Verify .agent integrity
  run: |
    uv tool install dot-agent-kit
    dot-agent check
```

## File Organization

```
.agent/
├── packages/                   # Managed by dot-agent (DO NOT EDIT)
│   ├── agentic_programming_guide/
│   │   └── AGENTIC_PROGRAMMING.md
│   └── tools/
│       ├── dot_agent/
│       │   ├── dot_agent.md
│       │   └── MANAGING_DOT_AGENT.md
│       ├── gh/
│       │   └── gh.md
│       ├── gt/
│       │   └── gt.md
│       └── workstack/
│           └── workstack.md
├── CUSTOM_RULES.md            # Your project rules (safe to edit)
├── ARCHITECTURE.md            # Your docs (safe to edit)
└── *.md                       # Any project-specific files
```

## Best Practices

### DO

✅ Use `dot-agent sync` to update packages regularly
✅ Run `dot-agent check` before committing
✅ Create project-specific files at `.agent/` root level

### DON'T

❌ Edit files in `.agent/packages/` directly
❌ Commit modified package files
❌ Manually copy package files between projects

## Troubleshooting

### "Modified files" reported by check

**Cause**: Package files have been edited directly.

**Solution**: Run `dot-agent sync` to restore bundled versions.

### Missing packages after upgrade

**Cause**: New packages added in dot-agent-kit release.

**Solution**: Run `dot-agent sync` to install new packages.

### Conflicts during sync

**Cause**: Local modifications conflict with bundled updates.

**Solution**: Review diffs, then run `dot-agent sync --force` to overwrite.

## Version Compatibility

Running `dot-agent sync` updates packages to match the currently installed dot-agent-kit version.

**Upgrading**:

```bash
# Upgrade dot-agent-kit
uv tool upgrade dot-agent-kit

# Update packages to new version
cd /path/to/repository
dot-agent sync
```

## Integration with AI Agents

The `.agent/` directory provides curated context for AI coding assistants:

1. **Tool Discovery**: When using `gt`, `gh`, or `workstack`, agents can load documentation from `packages/tools/{tool-name}/`
2. **Consistent Patterns**: Agents reference shared documentation rather than making assumptions
3. **Token Efficiency**: Pre-materialized knowledge reduces repeated discovery
4. **Project Context**: Root-level files provide project-specific guidance

See `../../agentic_programming_guide/AGENTIC_PROGRAMMING.md` for comprehensive best practices.
