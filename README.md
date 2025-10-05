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
workstack switch main
workstack rm user-auth
```

## Overview

`workstack` solves the pain of managing multiple `git` worktrees - essential for parallel development with AI agents or working on multiple features simultaneously.

**Key features:**

- Centralized worktrees in `~/worktrees/<repo>/<feature>/`
- Automatic environment setup (`.env`, virtual environments, activation scripts)
- Simple CLI: `create`, `switch`, `rm`, `ls`
- Plan-based development workflow
- Optional Graphite integration for stacked diffs

Traditional `git` workflows require branch switching in a single location. With AI agents and parallel development needs, `workstack` makes managing multiple worktrees effortless.

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
workstack switch NAME            # Switch between worktrees (or 'main'/'master')
workstack ls                     # List all worktrees
workstack rename OLD NEW         # Rename a worktree
workstack rm NAME                # Remove worktree
workstack gc                     # Find safe-to-delete worktrees (merged PRs)
```

### Configuration

```bash
workstack init                   # Initialize in repository
workstack config list            # Show all configuration
workstack config get KEY         # Get config value
workstack config set KEY VALUE  # Set config value
```

## Configuration Files

**Global** (`~/.workstack/config.toml`):

```toml
workstacks_root = "/Users/you/worktrees"
use_graphite = true  # Auto-detected if gt CLI installed
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
# 1. Stay in main branch for planning
workstack switch main

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
# Creates worktree with current branch, switches you back to main
```

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

## Links

- **GitHub:** https://github.com/schrockn/workstack
- **Issues:** https://github.com/schrockn/workstack/issues

## License

MIT - Nick Schrock ([@schrockn](https://github.com/schrockn))
