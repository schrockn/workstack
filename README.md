# `workstack`

**Effortless `git` worktree management for parallel development.**

Create, switch, and manage multiple worktrees from a centralized location with automatic environment setup.

## Installation

```bash
# With uv (recommended)
uv tool install workstack

# From source
uv tool install git+https://github.com/schrockn/workstack.git
```

## Quick Start

```bash
# Initialize in your repo
cd /path/to/your/repo
workstack init
source ~/.zshrc  # or ~/.bashrc

# Create and switch to a worktree
workstack create user-auth
workstack switch user-auth

# Switch back and clean up
workstack switch root
workstack rm user-auth
```

## Overview

`workstack` solves the pain of managing multiple `git` worktrees for parallel agenetic coding sessions.

**Key features:**

- Centralized worktrees in `~/worktrees/<repo>/<feature>/`
- Automatic environment setup (`.env`, virtual environments, activation scripts)
- Simple CLI: `create`, `switch`, `rm`, `ls`
- Plan-based development workflow
- Optional Graphite integration for stacked diffs

## Core Commands

### Creating Worktrees

```bash
# New feature branch
workstack create feature-x                          # Creates worktree 'feature-x' with branch 'feature-x'
workstack create fix --branch hotfix/bug           # Creates worktree 'fix' with branch 'hotfix/bug'

# From existing branch
workstack create --from-branch feature/login       # Creates worktree from existing branch 'feature/login'
workstack create login --from-branch feature/login # Creates worktree 'login' from branch 'feature/login'

# Move current work
workstack create --from-current-branch             # Move current branch to new worktree

# From a plan file
workstack create --plan Add_Auth.md                # Creates worktree, moves plan to .PLAN.md
```

### Managing Worktrees

```bash
workstack switch NAME            # Switch between worktrees (or 'root' for repo root)
workstack list                   # List all worktrees (alias: ls)
workstack list --stacks          # List with graphite stacks and PR status
workstack tree                   # Show tree of worktrees with dependencies
workstack rename OLD NEW         # Rename a worktree
workstack rm NAME                # Remove worktree
workstack gc                     # Find safe-to-delete worktrees (merged PRs)
workstack sync                   # Sync with Graphite, show cleanup candidates
workstack sync -f                # Sync and auto-remove merged workstacks
```

Example output:

```bash
$ workstack list
root [master]
feature-a [feature-a]
feature-b [work/feature-b]

$ workstack list --stacks
root [master]
  ◉  master

feature-a [feature-a]
  ◯  master
  ◉  feature-a ✅ #123

feature-b [work/feature-b]
  ◯  master
  ◉  work/feature-b 🚧 #456
```

**PR Status Indicators:**

- ✅ Checks passing
- ❌ Checks failing
- 🟣 Merged
- 🚧 Draft
- ⭕ Closed
- ◯ Open (no checks)

Note: The repository root is displayed as `root` and can be accessed with `workstack switch root`.

### Visualizing Worktrees

```bash
workstack tree               # Show tree of worktrees with dependencies
```

Example output:

```bash
$ workstack tree
main [@root]
├─ feature-a [@feature-a]
│  └─ feature-a-2 [@feature-a-2]
└─ feature-b [@feature-b]
```

The `tree` command shows:

- **Only branches with active worktrees** (not all branches)
- **Dependency relationships** from Graphite stacks
- **Current worktree** highlighted in bright green
- **Worktree names** in brackets `[@name]`

**Note:** Requires Graphite to be enabled.

### Configuration

```bash
workstack init                   # Initialize in repository
workstack init --shell           # Set up shell integration (completion + auto-activation)
workstack init --list-presets    # List available config presets
workstack init --repo            # Initialize repo config only (skip global)
workstack config list            # Show all configuration
workstack config get KEY         # Get config value
workstack config set KEY VALUE   # Set config value
workstack completion bash/zsh/fish  # Generate shell completion script
```

## Configuration Files

**Global** (`~/.workstack/config.toml`):

```toml
workstacks_root = "/Users/you/worktrees"
use_graphite = true     # Auto-detected if gt CLI installed
show_pr_info = true     # Display PR status in list --stacks (requires gh CLI)
```

**Per-Repository** (`~/worktrees/<repo>/config.toml`):

```toml
[env]
# Template variables: {worktree_path}, {repo_root}, {name}
DATABASE_URL = "postgresql://localhost/{name}_db"

[post_create]
shell = "bash"
commands = [
  "uv venv",
  "uv pip install -e .",
]
```

## Common Workflows

### Parallel Feature Development

```bash
workstack create feature-a
workstack switch feature-a
# ... work on feature A ...

workstack create feature-b
workstack switch feature-b
# ... work on feature B ...

workstack switch feature-a  # Instantly back to feature A
```

### Plan-Based Development

`workstack` promotes an opinionated workflow that separates planning from implementation:

**Core principles:**

- **Plan in main/master** - Keep your main branch "read-only" for planning. Since planning doesn't modify code, you can create multiple plans in parallel without worktrees.
- **Execute in worktrees** - All code changes happen in dedicated worktrees, keeping work isolated and switchable.
- **Plans as artifacts** - Each plan is a markdown file that travels with its worktree.

**Workflow:**

```bash
# 1. Stay in root repo for planning
workstack switch root

# 2. Create your plan and save it to disk (e.g. Add_User_Auth.md)

# 3. Create worktree from plan
workstack create --plan Add_User_Auth.md
# This automatically:
#   - Creates worktree named 'add-user-auth'
#   - Moves Add_User_Auth.md to worktree as .PLAN.md
#   - .PLAN.md is already in .gitignore (added by workstack init)

# 4. Switch and execute
workstack switch add-user-auth
# Your plan is now at .PLAN.md for reference during implementation
```

**Why this works:**

- Plans don't clutter PR reviews (`.PLAN.md` in `.gitignore`)
- Each worktree has its own plan context
- Clean separation between thinking and doing
- Workflow guides user to start implementation with clean context with just the .PLAN.md.

This workflow emerged from experience - checking in planning documents created noise in reviews and maintenance overhead without clear benefits.

### Moving Current Work

```bash
# Started work on main by accident?
workstack create --from-current-branch
# Creates worktree with current branch, switches you back to root
```

### Syncing and Cleanup

After merging PRs, sync your local branches and clean up:

```bash
workstack sync
# This will:
# 1. Switch to root (avoiding git conflicts)
# 2. Run gt sync to update branch tracking
# 3. Identify merged/closed PR workstacks
# 4. Prompt for confirmation before removing them
# 5. Switch back to your original worktree

# Or use -f to skip confirmation:
workstack sync -f
```

Options:

```bash
workstack sync                   # Sync and show cleanup candidates
workstack sync -f                # Force gt sync and auto-remove merged workstacks
workstack sync --dry-run         # Preview without executing
```

Requires Graphite CLI (`gt`) and GitHub CLI (`gh`) installed.

## Command Reference

### `create` Options

| Option                  | Description                         |
| ----------------------- | ----------------------------------- |
| `--branch BRANCH`       | Specify branch name (default: NAME) |
| `--ref REF`             | Base ref (default: current HEAD)    |
| `--plan FILE`           | Create from plan file               |
| `--from-current-branch` | Move current branch to worktree     |
| `--from-branch BRANCH`  | Create from existing branch         |
| `--no-post`             | Skip post-create commands           |

### `list` / `ls` Options

| Option         | Description                        |
| -------------- | ---------------------------------- |
| `-s, --stacks` | Show graphite stacks and PR status |

### `remove` / `rm` Options

| Option               | Description                               |
| -------------------- | ----------------------------------------- |
| `-f, --force`        | Do not prompt for confirmation            |
| `-s, --delete-stack` | Delete all branches in Graphite stack     |
| `--dry-run`          | Show what would be done without executing |

### `rename` Options

| Option      | Description                               |
| ----------- | ----------------------------------------- |
| `--dry-run` | Show what would be done without executing |

### `sync` Options

| Option        | Description                                     |
| ------------- | ----------------------------------------------- |
| `-f, --force` | Force gt sync and auto-remove merged workstacks |
| `--dry-run`   | Show what would be done without executing       |

### `init` Options

| Option           | Description                                |
| ---------------- | ------------------------------------------ |
| `--force`        | Overwrite existing repo config             |
| `--preset NAME`  | Config template (auto/generic/dagster/etc) |
| `--list-presets` | List available presets and exit            |
| `--repo`         | Initialize repo config only (skip global)  |
| `--shell`        | Set up shell integration only              |

### Environment Variables

Always exported when switching:

- `WORKTREE_PATH` - Absolute path to current worktree
- `REPO_ROOT` - Absolute path to repository root
- `WORKTREE_NAME` - Name of current worktree

## Advanced Features

### Graphite Integration

If [Graphite CLI](https://graphite.dev/) is installed, `workstack` automatically uses `gt create` for proper stack tracking.

```bash
brew install withgraphite/tap/graphite
workstack init  # Auto-detects gt
```

Disable in `~/.workstack/config.toml`: `use_graphite = false`

### Repository Presets

**Dagster:**

```toml
[env]
DAGSTER_GIT_REPO_DIR = "{worktree_path}"

[post_create]
commands = ["uv venv", "uv run make dev_install"]
```

### Garbage Collection

Find and clean up merged/closed PR branches:

```bash
workstack gc
# Output:
#   feature-x [work/feature-x] - merged (PR #123)
#     → workstack rm feature-x
```

Requires GitHub CLI (`gh`) installed and authenticated.

## FAQ

**Q: How is this different from `git worktree`?**  
A: Adds centralized management, automatic environment setup, and seamless switching.

**Q: Does it work with non-Python projects?**  
A: Yes! Configure `post_create` commands for any stack.

**Q: What if I don't use Graphite?**  
A: Works perfectly with standard git commands.

## Documentation

### For Developers

Core documentation for contributors:

- **[CLAUDE.md](CLAUDE.md)** - Coding standards and conventions (required reading)
- **[tests/CLAUDE.md](tests/CLAUDE.md)** - Testing patterns and practices

### For AI Assistants

Comprehensive, agent-optimized documentation is available in the `.agent/` directory:

- **[Architecture](.agent/ARCHITECTURE.md)** - System design, patterns, and component relationships
- **[Feature Index](.agent/FEATURE_INDEX.md)** - Complete feature catalog with implementation locations
- **[Glossary](.agent/GLOSSARY.md)** - Terminology and concept definitions
- **[Module Map](.agent/docs/MODULE_MAP.md)** - Module structure and exports
- **[Coding Patterns](.agent/docs/PATTERNS.md)** - Detailed implementation patterns with examples
- **[Exception Handling](.agent/docs/EXCEPTION_HANDLING.md)** - Complete exception handling guide

See [`.agent/README.md`](.agent/README.md) for more details.

## Links

- **GitHub:** https://github.com/schrockn/workstack
- **Issues:** https://github.com/schrockn/workstack/issues

## License

MIT - Nick Schrock ([@schrockn](https://github.com/schrockn))
