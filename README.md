# workstack

**A global git worktree manager that keeps your repository clean while enabling parallel development workflows.**

Manage git worktrees in a centralized directory with automatic environment setup, per-worktree configuration, and seamless integration with AI coding assistants.

## Why?

Traditional git workflows force you to stash changes and switch branches constantly. Git worktrees solve this, but managing them manually is tedious. `workstack`:

- **Centralizes worktrees** in `~/worktrees/<repo>/<feature>/` (configurable)
- **Auto-configures environments** with `.env`, virtual environments, and activation scripts
- **Runs setup commands** automatically (install dependencies, migrations, etc.)
- **Supports multiple repos** with different configurations per repository
- **Integrates with AI assistants** via `.PLAN.md` file support
- **Works with Graphite** for stacked diffs (optional)

## Installation

```bash
# From PyPI
pip install workstack

# With uv (recommended)
uv tool install workstack

# From source
uv tool install git+https://github.com/schrockn/workstack.git
```

## Quick Start

```bash
# 1. Initialize in your repository
cd /path/to/your/repo
workstack init

# 2. Create a worktree
workstack create user-auth

# 3. Switch to it
source <(workstack switch user-auth --script)

# 4. Work on your feature...

# 5. Switch back
source <(workstack switch . --script)

# 6. Clean up
workstack rm user-auth
```

## Core Concepts

### Architecture

```
~/.workstack/config.toml          # Global config (worktree root location)
~/worktrees/
  your-repo/
    config.toml                   # Repo-specific config
    user-auth/                    # Worktree
      .git, .env, .venv/, activate.sh, .PLAN.md, <source>
    refactor-api/
      ...
```

### Configuration

**Global** (`~/.workstack/config.toml`):
```toml
workstacks_root = "/Users/you/worktrees"
use_graphite = true  # Auto-detected (requires gt CLI)
```

**Per-Repo** (`~/worktrees/<repo>/config.toml`):
```toml
[env]
# Variables: {worktree_path}, {repo_root}, {name}
DATABASE_URL = "postgresql://localhost/{name}_db"

[post_create]
shell = "bash"
commands = [
  "uv venv",
  "uv pip install -e .",
]
```

## Commands

### `workstack init [--preset auto|generic|dagster]`
Initialize workstack for current repository. Creates config, adds to `.gitignore`.

### `workstack create NAME [--branch BRANCH] [--ref REF] [--plan FILE]`
Create worktree with new branch.

```bash
workstack create feature-x                          # Branch: work/feature-x
workstack create fix --branch hotfix/bug --ref main
workstack create --plan Add_Auth.md                 # Moves plan to .PLAN.md
```

### `workstack co BRANCH [--name NAME]`
Checkout existing branch into worktree.

```bash
workstack co feature/login
workstack co feature/login --name login-work
```

### `workstack move [NAME] [--to-branch BRANCH]`
Move current branch to worktree, switch to different branch.

```bash
workstack move                     # Move to worktree, switch to main
workstack move feat --to-branch develop
```

### `workstack switch NAME [--script]`
Switch to worktree (or `.` for root repo).

```bash
source <(workstack switch feature-x --script)
source <(workstack switch . --script)
```

**Alias:**
```bash
alias ws='source <(workstack switch --script'
```

### `workstack list` / `workstack ls`
List all worktrees.

### `workstack rm NAME [-f]`
Remove worktree (with optional force).

### `workstack completion [bash|zsh|fish]`
Generate shell completions.

```bash
source <(workstack completion bash)  # Add to ~/.bashrc
```

## Workflows

### AI Development with Claude

```bash
# 1. Create plan (Claude generates this)
claude "Create plan for user auth"  # Saves Add_User_Auth.md

# 2. Create worktree from plan
workstack create --plan Add_User_Auth.md

# 3. Switch and launch Claude
source <(workstack switch add-user-auth --script)
claude  # Reads .PLAN.md automatically
```

### Parallel Features

```bash
workstack create feature-a
source <(workstack switch feature-a --script)
# ... work ...

workstack create feature-b
source <(workstack switch feature-b --script)
# ... work ...

source <(workstack switch feature-a --script)  # Back to A
```

### Testing PRs

```bash
git fetch origin pull/123/head:pr-123
workstack co pr-123
source <(workstack switch pr-123 --script)
pytest
workstack rm pr-123 -f
```

### Repository-Specific Setup

**Django:**
```toml
[env]
DATABASE_URL = "postgresql://localhost/myproject_{name}"

[post_create]
shell = "bash"
commands = [
  "python -m venv .venv",
  "source .venv/bin/activate && pip install -e .[dev]",
  "createdb myproject_{name}",
  "python manage.py migrate",
]
```

**Dagster:**
```toml
[env]
DAGSTER_GIT_REPO_DIR = "{worktree_path}"

[post_create]
shell = "bash"
commands = ["uv venv", "uv run make dev_install"]
```

## Environment Variables

**Template Variables** (use in `config.toml`):
- `{worktree_path}` - Absolute path to worktree
- `{repo_root}` - Absolute path to repository root
- `{name}` - Worktree name

**Always Available** (exported in `activate.sh`):
- `WORKTREE_PATH`, `REPO_ROOT`, `WORKTREE_NAME`

## Graphite Integration

If [Graphite CLI](https://graphite.dev/) (`gt`) is installed, `workstack` uses `gt create` instead of `git branch` for new worktrees, ensuring proper stack tracking.

```bash
brew install withgraphite/tap/graphite
workstack init  # Auto-detects gt
```

Manual override in `~/.workstack/config.toml`:
```toml
use_graphite = false  # Disable even if gt is installed
```

## Tips

**Shell aliases:**
```bash
alias ws='source <(workstack switch --script'
alias wc='workstack create'
alias wl='workstack list'
source <(workstack completion bash)
```

**Naming:** Use lowercase with hyphens: `add-user-auth`, `fix-login-bug`

**Cleanup:** `workstack list` → `workstack rm old-feature -f`

## Development

```bash
git clone https://github.com/schrockn/workstack.git
cd workstack
uv sync --group dev
uv run pytest
uv run ruff check
uv run pyright
```

## FAQ

**vs git worktree?** Adds centralized management, auto environment setup, templates, and AI integration.

**Python version?** 3.13+ (earlier may work).

**Non-Python projects?** Yes! Configure `post_create` for any stack.

**Without Graphite?** Works fine, uses standard git commands.

## Links

- **PyPI:** https://pypi.org/project/workstack/
- **GitHub:** https://github.com/schrockn/workstack
- **Issues:** https://github.com/schrockn/workstack/issues

## License

MIT - Nick Schrock ([@schrockn](https://github.com/schrockn))
