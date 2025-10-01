workstack — Global Git Worktree Manager
=========================================

Click-based CLI to manage git worktrees in a centralized global directory.

## Overview

`workstack` manages git worktrees in a global directory structure (e.g., `~/worktrees/<repo-name>/<worktree-name>/`), keeping your repository root clean. Each worktree gets its own environment, virtual environment, and activation script.

## Quickstart

**Development:**
```bash
uv sync              # Install dependencies
uv sync --group dev  # Include dev dependencies
uv run workstack --help
```

**Install as a uv tool:**
```bash
# From local checkout
uv tool install --path .

# From Git URL
uv tool install git+https://github.com/schrockn/workstack.git

# From Git URL with ref
uv tool install git+https://github.com/schrockn/workstack.git@v0.1.0

# Use it
workstack --help

# Upgrade
uv tool upgrade workstack

# Uninstall
uv tool uninstall workstack
```

## Configuration

### Global Config

First-time `init` prompts for a global worktrees directory. This creates `~/.workstack/config.toml`:

```toml
workstacks_root = "/Users/you/worktrees"
```

All repository worktrees will be stored under `<workstacks_root>/<repo-name>/`.

### Repo-local Config

After running `workstack init` in a repository, edit `<workstacks_root>/<repo-name>/config.toml`:

```toml
[env]
# Template variables: {worktree_path}, {repo_root}, {name}
DAGSTER_GIT_REPO_DIR = "{worktree_path}"

[post_create]
shell = "bash"
commands = [
  "uv venv",
  "uv run make dev_install",
]
```

Variables available in `[env]` templates:
- `{worktree_path}` — absolute path to the worktree
- `{repo_root}` — absolute path to the repository root
- `{name}` — worktree name

## Commands

### `workstack init [--preset auto|generic|dagster] [--force]`

Initialize workstack for the current repository.
- Prompts for global config (`~/.workstack/config.toml`) if not present
- Creates repo config directory at `<workstacks_root>/<repo-name>/`
- Writes `config.toml` template
- Adds `activate.sh` and `.PLAN.md` to `.gitignore`

**Presets:**
- `auto` (default) — detects Dagster repos, otherwise uses generic template
- `generic` — basic commented template
- `dagster` — Dagster-specific environment and post-create commands

### `workstack create [NAME] [options]`

Create a new worktree with a new branch.

**Options:**
- `NAME` — worktree name (or use `--plan` to derive from filename)
- `--branch BRANCH` — custom branch name (default: `work/<name>`)
- `--ref REF` — base ref for branch (default: `HEAD`)
- `--plan FILE` — derive name from plan file and move to `.PLAN.md` in worktree
- `--no-post` — skip post-create commands

**Examples:**
```bash
# Create worktree "feature-x" with branch "work/feature-x"
workstack create feature-x

# Create with custom branch and base ref
workstack create bugfix --branch fix/auth --ref origin/main

# Create from plan file
workstack create --plan Add_Auth_Feature.md
# Creates worktree "add-auth-feature" and moves plan to .PLAN.md
```

**What it does:**
1. Creates worktree at `<workstacks_root>/<repo-name>/<name>/`
2. Creates and checks out new branch
3. Writes `.env` file with configured environment variables
4. Writes `activate.sh` script (executable)
5. Moves plan file to `.PLAN.md` if `--plan` specified
6. Runs post-create commands from config

### `workstack co BRANCH [--name NAME] [--no-post]`

Create a worktree by checking out an existing branch.

**Examples:**
```bash
# Checkout existing branch "feature/login"
workstack co feature/login

# Checkout with custom worktree name
workstack co feature/login --name login-work
```

### `workstack move [NAME] [--to-branch BRANCH] [--no-post]`

Move the current branch to a new worktree and switch current directory to a different branch.

**Examples:**
```bash
# Move current branch to worktree, switch to main
workstack move

# Move with custom name and target branch
workstack move my-feature --to-branch develop
```

**What it does:**
1. Detects current branch
2. Switches current worktree to target branch (defaults to `main` or `master`)
3. Creates new worktree with the original branch
4. Sets up environment and runs post-create commands

### `workstack switch NAME [--script]`

Print shell code to switch to a worktree.

**Usage:**
```bash
# With instructions (default)
workstack switch feature-x

# Direct activation
source <(workstack switch feature-x --script)

# Switch to root repo
source <(workstack switch . --script)
```

**Special case:** Use `.` as name to switch to root repository.

### `workstack list` / `workstack ls`

List all worktrees with activation hints.

**Output:**
```
. (root repo: /path/to/repo)
feature-x (source /path/to/worktrees/repo/feature-x/activate.sh)
bugfix (source /path/to/worktrees/repo/bugfix/activate.sh)
```

### `workstack activate-script NAME`

Print activation script for a worktree (useful for regeneration or debugging).

### `workstack rm NAME [-f|--force]`

Remove a worktree directory.

**Examples:**
```bash
# Remove with confirmation prompt
workstack rm feature-x

# Force remove without prompt
workstack rm feature-x -f
```

Runs `git worktree remove` first, then deletes the directory.

### `workstack completion [bash|zsh|fish]`

Generate shell completion scripts for tab-completing worktree names.

**Setup examples:**
```bash
# Bash — add to ~/.bashrc
source <(workstack completion bash)

# Zsh — add to ~/.zshrc
source <(workstack completion zsh)

# Fish — run once
workstack completion fish > ~/.config/fish/completions/workstack.fish
```

After setup, `workstack switch <TAB>` completes worktree names.

## Workflows

### Plan-based Development with Claude

1. Create a plan file in your Claude session:
   ```bash
   # Claude creates: Add_User_Authentication.md
   ```

2. Create worktree from plan:
   ```bash
   workstack create --plan Add_User_Authentication.md
   ```
   This:
   - Derives name: `add-user-authentication`
   - Creates worktree at `<workstacks_root>/<repo>/add-user-authentication/`
   - Moves plan to `<worktree>/.PLAN.md`

3. Switch to worktree:
   ```bash
   source <(workstack switch add-user-authentication --script)
   ```

4. Launch Claude:
   ```bash
   claude
   ```
   Claude automatically reads `.PLAN.md` on launch.

### Branch-based Development

```bash
# Create worktree for new feature
workstack create user-auth --ref origin/main

# Switch to it
source <(workstack switch user-auth --script)

# Work on feature...

# When done, switch back to root
source <(workstack switch . --script)

# Clean up
workstack rm user-auth
```

### Moving Existing Work

If you're already on a branch and want to move it to a worktree:

```bash
# Currently on branch "experimental-feature"
workstack move

# Current directory switches to main
# Branch moved to worktree at experimental-feature/
```

## Activation Scripts

Each worktree gets an `activate.sh` that:
1. Changes to the worktree directory
2. Activates `.venv/bin/activate` if present
3. Exports variables from `.env`

**Always-available environment variables:**
- `WORKTREE_PATH` — absolute path to worktree
- `REPO_ROOT` — absolute path to repository root
- `WORKTREE_NAME` — worktree name

## Architecture

```
~/.workstack/
  config.toml              # Global config

~/worktrees/               # Configurable root
  my-repo/
    config.toml            # Repo config
    feature-a/             # Worktree
      .git                 # Git worktree metadata
      .env                 # Environment variables
      .venv/               # Virtual environment (if created)
      activate.sh          # Activation script
      .PLAN.md             # Optional plan file
      <source files>
    feature-b/
      ...

/path/to/my-repo/          # Original repository
  .git/                    # Git metadata
  <source files>
```

## Development

**Tools:**
- Package manager: `uv`
- Linting/formatting: Ruff
- Type checking: Pyright
- Testing: Pytest

**Run tests:**
```bash
uv run pytest
uv run pytest --cov=workstack
```

**Type checking:**
```bash
uv run pyright
```

**Linting:**
```bash
uv run ruff check
uv run ruff format
```
