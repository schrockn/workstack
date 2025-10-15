# dot-agent Development Guide

## Overview

The `dot-agent` package provides tool documentation and resources for AI coding assistants. This guide explains the development workflow, symlink management, and how changes flow from development to distribution.

## Architecture

### Source of Truth

**All tool documentation lives in the dot-agent package:**

```
packages/dot-agent/src/dot_agent/resources/tools/
├── gt.md         # Graphite (gt) command documentation
├── gh.md         # GitHub (gh) command documentation
└── workstack.md  # Workstack command documentation
```

These files are:

- Distributed via PyPI when `dot-agent` is installed
- The single source of truth for all tool documentation
- Automatically synced to user repositories via `dot-agent sync`

### Why Symlinks in Workstack Repo?

During development in the workstack monorepo, `.agent/tools/` contains **symbolic links** to the package resources:

```
.agent/tools/
├── gt.md        → ../../packages/dot-agent/src/dot_agent/resources/tools/gt.md
├── gh.md        → ../../packages/dot-agent/src/dot_agent/resources/tools/gh.md
└── workstack.md → ../../packages/dot-agent/src/dot_agent/resources/tools/workstack.md
```

**Benefits:**

1. **Single source of truth**: No duplication or manual copying
2. **Automatic sync**: Edit in either location, changes apply everywhere
3. **Development ergonomics**: Tools work the same way in development as production
4. **No manual steps**: Symlinks eliminate copy-paste between locations

**Important**: In user repositories (after `dot-agent init`), these are regular files, not symlinks. Only the workstack development repo uses symlinks.

## Symlink Management

Symlinks in the workstack repo are managed by the `workstack-dev` CLI tool.

### Check Status

```bash
# Show current symlink status
workstack-dev link-dot-agent-resources

# Verbose output
workstack-dev link-dot-agent-resources --verbose
```

### Create Symlinks

```bash
# Preview what will be created
workstack-dev link-dot-agent-resources --create --dry-run

# Create symlinks
workstack-dev link-dot-agent-resources --create

# Force creation even if content differs
workstack-dev link-dot-agent-resources --create --force
```

### Remove Symlinks

```bash
# Preview removal (converts symlinks back to regular files)
workstack-dev link-dot-agent-resources --remove --dry-run

# Remove symlinks and restore regular files
workstack-dev link-dot-agent-resources --remove
```

### Verify Symlinks

```bash
# Check that all symlinks are valid
workstack-dev link-dot-agent-resources --verify
```

Exit code `0` = all valid, `1` = issues found

## Development Workflow

### Making Changes to Tool Documentation

You can edit tool documentation in **either** location:

**Option 1: Edit through symlink (recommended)**

```bash
# Edit the symlink
vim .agent/tools/gt.md

# Changes automatically apply to the package
git diff packages/dot-agent/src/dot_agent/resources/tools/gt.md
```

**Option 2: Edit package directly**

```bash
# Edit source of truth
vim packages/dot-agent/src/dot_agent/resources/tools/gt.md

# Changes visible through symlink
cat .agent/tools/gt.md
```

Both approaches produce identical results because symlinks keep the files in sync.

### Testing Changes

#### 1. Test dot-agent Package

```bash
# Run dot-agent tests
uv run pytest packages/dot-agent/tests

# Type check
uv run pyright packages/dot-agent/
```

#### 2. Test in Development Environment

The `.agent/tools/` symlinks are used by your local AI assistant during development, so you can test changes immediately:

```bash
# Your AI assistant reads from .agent/tools/
# Which are symlinks to packages/dot-agent/src/dot_agent/resources/tools/
# So changes are immediately available
```

#### 3. Test Distribution

```bash
# Install dot-agent locally in editable mode
uv pip install -e packages/dot-agent/

# Test sync command
dot-agent sync

# Verify files are distributed correctly
ls -la .agent/tools/
```

### Committing Changes

When you commit changes, Git sees **both** locations:

```bash
# Stage both the package and symlink
git add packages/dot-agent/src/dot_agent/resources/tools/gt.md
git add .agent/tools/gt.md

# Commit
git commit -m "Update Graphite documentation"
```

**Note**: Git commits symlinks as symlinks, preserving the development workflow for all contributors.

## Publishing

### Publishing to PyPI

```bash
# Build and publish dot-agent
workstack-dev publish-to-pypi

# Follow prompts to select dot-agent package
```

### User Installation

After publishing, users install via:

```bash
# Install dot-agent
uv pip install dot-agent

# Initialize in their repository
dot-agent init

# Sync tool documentation (creates regular files, not symlinks)
dot-agent sync
```

**Important**: User repositories receive **regular files**, not symlinks. The symlinks only exist in the workstack development repository.

## Relationship to workstack-dev

The `workstack-dev` package is a development-only CLI tool for the workstack monorepo. It includes the `link-dot-agent-resources` command specifically for managing symlinks during development.

**Key distinction:**

- `workstack-dev`: Development tool (not published to PyPI)
- `dot-agent`: Published package with tool documentation

Users never interact with `workstack-dev`—they only use `dot-agent`.

## File Flow

```
┌─────────────────────────────────────────────────────────┐
│ Development (workstack repo)                            │
│                                                         │
│ packages/dot-agent/src/dot_agent/resources/tools/      │
│   ├── gt.md         ← SOURCE OF TRUTH                  │
│   ├── gh.md                                            │
│   └── workstack.md                                     │
│                                                         │
│        ↕ (symlink, managed by workstack-dev)           │
│                                                         │
│ .agent/tools/                                          │
│   ├── gt.md        → symlink                           │
│   ├── gh.md        → symlink                           │
│   └── workstack.md → symlink                           │
└─────────────────────────────────────────────────────────┘
                         ↓
                    (PyPI publish)
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Distribution (PyPI)                                     │
│                                                         │
│ dot-agent package includes:                            │
│   dot_agent/resources/tools/                           │
│   ├── gt.md                                            │
│   ├── gh.md                                            │
│   └── workstack.md                                     │
└─────────────────────────────────────────────────────────┘
                         ↓
                    (pip install)
                         ↓
┌─────────────────────────────────────────────────────────┐
│ User Repository                                         │
│                                                         │
│ .agent/tools/                                          │
│   ├── gt.md         ← REGULAR FILE (synced by user)   │
│   ├── gh.md         ← REGULAR FILE                     │
│   └── workstack.md  ← REGULAR FILE                     │
└─────────────────────────────────────────────────────────┘
```

## Common Scenarios

### Scenario 1: Adding a New Tool

```bash
# 1. Create the tool documentation in the package
vim packages/dot-agent/src/dot_agent/resources/tools/new-tool.md

# 2. Create symlink
workstack-dev link-dot-agent-resources --create

# 3. Test
uv run pytest packages/dot-agent/tests

# 4. Commit both
git add packages/dot-agent/src/dot_agent/resources/tools/new-tool.md
git add .agent/tools/new-tool.md
git commit -m "Add new-tool documentation"

# 5. Publish
workstack-dev publish-to-pypi
```

### Scenario 2: Updating Existing Documentation

```bash
# 1. Edit through symlink (or package directly)
vim .agent/tools/gt.md

# 2. Test
uv run pytest packages/dot-agent/tests

# 3. Commit
git add packages/dot-agent/src/dot_agent/resources/tools/gt.md
git add .agent/tools/gt.md
git commit -m "Update Graphite documentation"

# 4. Publish
workstack-dev publish-to-pypi
```

### Scenario 3: Symlinks Broken After Git Operation

```bash
# Check status
workstack-dev link-dot-agent-resources --status

# Recreate symlinks
workstack-dev link-dot-agent-resources --create
```

### Scenario 4: Working Without Symlinks (Local Experimentation)

```bash
# 1. Remove symlinks
workstack-dev link-dot-agent-resources --remove

# 2. Edit as regular files
vim .agent/tools/gt.md

# 3. Make experimental changes

# 4. When ready to merge:
# Option A: Copy to package
cp .agent/tools/gt.md packages/dot-agent/src/dot_agent/resources/tools/

# Option B: Recreate symlinks (warns if content differs)
workstack-dev link-dot-agent-resources --create
```

### Scenario 5: Content Mismatch Between Locations

If `.agent/tools/` contains regular files with different content than the package:

```bash
# Will fail with error message
workstack-dev link-dot-agent-resources --create

# Review differences manually
diff .agent/tools/gt.md packages/dot-agent/src/dot_agent/resources/tools/gt.md

# Choose:
# - Fix manually then retry
# - Use --force to overwrite local changes
workstack-dev link-dot-agent-resources --create --force
```

## Troubleshooting

### Symlinks Not Working

```bash
# Check status
workstack-dev link-dot-agent-resources --status

# Verify symlinks
workstack-dev link-dot-agent-resources --verify

# Recreate if needed
workstack-dev link-dot-agent-resources --create
```

### Git Shows Symlinks as Modified

This is normal if you're on a system that doesn't support symlinks (e.g., Windows without developer mode). Consider:

1. Remove symlinks and work with regular files
2. Enable Windows developer mode
3. Use WSL for development

### Changes Not Appearing in Distribution

Ensure you:

1. Committed changes to `packages/dot-agent/src/dot_agent/resources/tools/`
2. Published to PyPI with updated version number
3. Users ran `dot-agent sync` to update their local copies

## Best Practices

1. **Always use symlinks during development** - Eliminates sync issues
2. **Test before publishing** - Run `uv run pytest packages/dot-agent/tests`
3. **Commit both locations** - Git tracks both package and symlink
4. **Verify after git operations** - Run `--verify` after merge/rebase
5. **Document breaking changes** - Tool documentation changes affect all users

## Related Documentation

- `CLAUDE.md` - Quick reference for AI assistants
- `workstack-dev/README.md` - CLI command reference
- `.agent/README.md` - Agent documentation overview
