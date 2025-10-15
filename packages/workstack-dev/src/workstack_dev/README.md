# workstack-dev - Development CLI

A general-purpose CLI for development tools and scripts used during workstack development.

## Architecture

For detailed architecture documentation, see [.agent/WORKSTACK_DEV.md](../../.agent/WORKSTACK_DEV.md).

## Quick Start

```bash
# View available commands
workstack-dev --help

# Example commands
workstack-dev clean-cache --dry-run
workstack-dev publish-to-pypi
```

## Shell Completions

`workstack-dev` supports tab completion for bash, zsh, and fish shells.

### Quick Setup

**Bash:**

```bash
echo 'source <(workstack-dev completion bash)' >> ~/.bashrc
source ~/.bashrc
```

**Zsh:**

```bash
echo 'source <(workstack-dev completion zsh)' >> ~/.zshrc
source ~/.zshrc
```

**Fish:**

```fish
mkdir -p ~/.config/fish/completions
workstack-dev completion fish > ~/.config/fish/completions/workstack-dev.fish
```

### Temporary Installation (Current Session Only)

Test completions without permanent installation:

**Bash/Zsh:**

```bash
source <(workstack-dev completion [bash|zsh])
```

**Fish:**

```fish
workstack-dev completion fish | source
```

### Verification

After setup, test completions:

```bash
workstack-dev <TAB>  # Should show: clean-cache, completion, create-agents-symlinks, link-dot-agent-resources, publish-to-pypi
```

## Commands

### link-dot-agent-resources

Manage symbolic links between `.agent/tools/` and `packages/dot-agent-kit/src/dot_agent_kit/resources/tools/`.

**Background**: During development in the workstack monorepo, `.agent/tools/` files are symlinks to the dot-agent-kit package resources. This ensures a single source of truth while maintaining development ergonomics. In user repositories (after `dot-agent init`), these are regular files synced by `dot-agent sync`.

**Usage:**

```bash
# Show current status (default)
workstack-dev link-dot-agent-resources
workstack-dev link-dot-agent-resources --status

# Create symlinks
workstack-dev link-dot-agent-resources --create
workstack-dev link-dot-agent-resources --create --dry-run
workstack-dev link-dot-agent-resources --create --force

# Remove symlinks (restore regular files)
workstack-dev link-dot-agent-resources --remove
workstack-dev link-dot-agent-resources --remove --dry-run

# Verify symlinks are valid
workstack-dev link-dot-agent-resources --verify

# Verbose output
workstack-dev link-dot-agent-resources --verbose
```

**Options:**

- `--create`: Create symlinks from `.agent/tools/` to package resources
- `--remove`: Remove symlinks and restore regular files
- `--status`: Show current state (default)
- `--verify`: Check symlinks are valid (exit code 0 = valid, 1 = issues)
- `--dry-run`: Preview changes without executing
- `--verbose`: Show detailed output
- `--force`: Skip confirmation prompts

**When to use:**

- After cloning the repository (if symlinks don't exist)
- After git operations that may break symlinks (merge, rebase)
- When switching between symlink and regular file workflows
- To verify symlinks are correctly configured

**See also:**

- `packages/dot-agent-kit/DEVELOPMENT.md` - Comprehensive development guide
- `packages/dot-agent-kit/CLAUDE.md` - Quick reference for AI assistants
