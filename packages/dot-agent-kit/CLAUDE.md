# dot-agent - AI Assistant Quick Reference

## What is dot-agent?

The `dot-agent` package distributes tool documentation for AI coding assistants via PyPI. When users run `dot-agent init` and `dot-agent sync`, tool documentation files are copied to their repository's `.agent/tools/` directory.

## Key Concepts for Agents

### Source of Truth

**All tool documentation lives in the dot-agent package:**

```
packages/dot-agent/src/dot_agent/resources/tools/
├── gt.md         # Graphite (gt) command documentation
├── gh.md         # GitHub (gh) command documentation
└── workstack.md  # Workstack command documentation
```

This is the **only** location where tool documentation should be edited.

### Symlinks in Workstack Repo

In the workstack development repository, `.agent/tools/` contains **symbolic links** to the package resources:

```
.agent/tools/gt.md → ../../packages/dot-agent/src/dot_agent/resources/tools/gt.md
```

**Important distinctions:**

- **Workstack repo (development)**: Symlinks managed by `workstack-dev link-dot-agent-resources`
- **User repos (production)**: Regular files synced by `dot-agent sync`

### Editing Tool Documentation

You can edit in **either** location—changes automatically sync:

```bash
# Edit through symlink
vim .agent/tools/gt.md

# Or edit source directly
vim packages/dot-agent/src/dot_agent/resources/tools/gt.md

# Both approaches produce identical results
```

### Managing Symlinks

Use `workstack-dev` CLI to manage symlinks:

```bash
# Check status
workstack-dev link-dot-agent-resources

# Create symlinks
workstack-dev link-dot-agent-resources --create

# Remove symlinks (restore regular files)
workstack-dev link-dot-agent-resources --remove

# Verify symlinks are valid
workstack-dev link-dot-agent-resources --verify
```

## Common Agent Tasks

### Task 1: Update Tool Documentation

```bash
# 1. Edit through symlink (recommended)
vim .agent/tools/gt.md

# 2. Verify change applied to package
git diff packages/dot-agent/src/dot_agent/resources/tools/gt.md

# 3. Test
uv run pytest packages/dot-agent/tests

# 4. Commit both locations
git add packages/dot-agent/src/dot_agent/resources/tools/gt.md
git add .agent/tools/gt.md
git commit -m "Update Graphite documentation"
```

### Task 2: Add New Tool Documentation

```bash
# 1. Create file in package (source of truth)
vim packages/dot-agent/src/dot_agent/resources/tools/new-tool.md

# 2. Create symlink
workstack-dev link-dot-agent-resources --create

# 3. Test
uv run pytest packages/dot-agent/tests

# 4. Commit both
git add packages/dot-agent/src/dot_agent/resources/tools/new-tool.md
git add .agent/tools/new-tool.md
git commit -m "Add new-tool documentation"
```

### Task 3: Fix Broken Symlinks

```bash
# 1. Check status
workstack-dev link-dot-agent-resources --status

# 2. Recreate symlinks
workstack-dev link-dot-agent-resources --create
```

### Task 4: Handle Content Mismatch

If regular files exist with different content than package:

```bash
# 1. Preview differences
diff .agent/tools/gt.md packages/dot-agent/src/dot_agent/resources/tools/gt.md

# 2. Choose approach:
# Option A: Manually resolve and retry
# Option B: Force overwrite
workstack-dev link-dot-agent-resources --create --force
```

## Development vs Production

| Aspect     | Workstack Repo (Development)                        | User Repos (Production)       |
| ---------- | --------------------------------------------------- | ----------------------------- |
| File type  | Symbolic links                                      | Regular files                 |
| Management | `workstack-dev link-dot-agent-resources`            | `dot-agent sync`              |
| Source     | `packages/dot-agent/src/dot_agent/resources/tools/` | Copied from PyPI package      |
| Editing    | Edit either symlink or source                       | Edit `.agent/tools/` directly |
| Updates    | Automatic via symlinks                              | Manual via `dot-agent sync`   |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ SOURCE OF TRUTH                                         │
│ packages/dot-agent/src/dot_agent/resources/tools/      │
│   ├── gt.md                                            │
│   ├── gh.md                                            │
│   └── workstack.md                                     │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ symlink (dev only)
                         │ managed by: workstack-dev
                         ↓
┌─────────────────────────────────────────────────────────┐
│ DEVELOPMENT SYMLINKS                                    │
│ .agent/tools/                                          │
│   ├── gt.md        → symlink to package               │
│   ├── gh.md        → symlink to package               │
│   └── workstack.md → symlink to package               │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ PyPI distribution
                         │ managed by: workstack-dev publish-to-pypi
                         ↓
┌─────────────────────────────────────────────────────────┐
│ USER REPOSITORIES                                       │
│ .agent/tools/                                          │
│   ├── gt.md         (regular file)                     │
│   ├── gh.md         (regular file)                     │
│   └── workstack.md  (regular file)                     │
└─────────────────────────────────────────────────────────┘
```

## Relationship to workstack-dev

**workstack-dev** = Development CLI tool (not published to PyPI)

- Manages symlinks in workstack repo
- Command: `workstack-dev link-dot-agent-resources`

**dot-agent** = Published package with tool documentation

- Distributed via PyPI
- Command: `dot-agent sync`

**Users never see `workstack-dev`**—they only interact with `dot-agent`.

## Testing Procedures

### Test Before Committing

```bash
# Run dot-agent tests
uv run pytest packages/dot-agent/tests

# Type check
uv run pyright packages/dot-agent/

# Verify symlinks
workstack-dev link-dot-agent-resources --verify
```

### Test Distribution Locally

```bash
# Install in editable mode
uv pip install -e packages/dot-agent/

# Test sync command
dot-agent sync

# Verify files distributed correctly
cat .agent/tools/gt.md
```

## Important Files

| File                                                    | Purpose                         | When to Edit                                     |
| ------------------------------------------------------- | ------------------------------- | ------------------------------------------------ |
| `packages/dot-agent/src/dot_agent/resources/tools/*.md` | Source of truth                 | All tool documentation changes                   |
| `.agent/tools/*.md`                                     | Symlinks (dev only)             | Never directly (edit package or through symlink) |
| `packages/dot-agent/DEVELOPMENT.md`                     | Comprehensive dev guide         | When development workflow changes                |
| `packages/dot-agent/CLAUDE.md`                          | This file—agent quick reference | When agent workflow changes                      |

## Quick Reference Commands

```bash
# Status and verification
workstack-dev link-dot-agent-resources                    # Show status
workstack-dev link-dot-agent-resources --verify           # Verify symlinks valid

# Create symlinks
workstack-dev link-dot-agent-resources --create           # Create symlinks
workstack-dev link-dot-agent-resources --create --force   # Force creation

# Remove symlinks
workstack-dev link-dot-agent-resources --remove           # Convert to regular files

# Preview changes
workstack-dev link-dot-agent-resources --create --dry-run # Preview creation
workstack-dev link-dot-agent-resources --remove --dry-run # Preview removal

# Testing
uv run pytest packages/dot-agent/tests                    # Run tests
uv run pyright packages/dot-agent/                        # Type check
```

## Best Practices for AI Assistants

1. **Always edit through symlinks or package directly** - Never manually copy files
2. **Verify symlinks after git operations** - Run `--verify` after merge/rebase
3. **Test before committing** - Run pytest and pyright
4. **Commit both locations** - Git tracks package source AND symlink
5. **Check status first** - Run `link-dot-agent-resources` to understand current state

## When to Read Full Documentation

This file provides a quick reference. Read `DEVELOPMENT.md` for:

- Detailed workflow explanations
- Comprehensive troubleshooting guide
- Publishing procedures
- Common scenarios with step-by-step instructions

## Summary

- **Source of truth**: `packages/dot-agent/src/dot_agent/resources/tools/`
- **Dev symlinks**: `.agent/tools/` → package resources
- **Management**: `workstack-dev link-dot-agent-resources`
- **Editing**: Edit through symlink or package directly (identical results)
- **Testing**: `uv run pytest packages/dot-agent/tests`
- **Distribution**: Users get regular files via `dot-agent sync`
