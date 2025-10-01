workstack — Git worktree manager
================================

Click-based CLI to manage git worktrees under a local `.workstack/` directory.

Quickstart
----------

- Install deps: `uv sync`
- Dev deps (with group): `uv sync --group dev`
- See help: `uv run workstack --help`

Install as a uv tool
--------------------

- From this repo checkout: `uv tool install --path .`
- From a Git URL: `uv tool install git+https://github.com/your-org/workstack.git`
  - Optionally pin a ref: `...@v0.1.0` or `...@<commit>`
- Use: `workstack --help`
- Upgrade: `uv tool upgrade workstack`
- Uninstall: `uv tool uninstall workstack`

Repo-local config
-----------------

Create `.workstack/config.toml` at the root of your repo (same level as `.git`):

```
[env]
DAGSTER_GIT_REPO_DIR = "{worktree_path}"

[post_create]
shell = "bash"
commands = [
  "uv venv",
  "uv run make dev_install",
]
```

Commands
--------

- `workstack create NAME [--branch BRANCH] [--ref REF] [--plan PLAN_FILE]`
  - Creates `.workstack/NAME`, writes `.env`, runs post-create commands
  - Creates and checks out a branch in the worktree:
    - Default branch name: `work/<NAME>` (sanitized)
    - Base ref: `--ref REF` (defaults to `HEAD`)
  - Also writes `.workstack/NAME/activate.sh` (executable)
  - `--plan PLAN_FILE` — derives worktree name from plan filename and moves it to `.PLAN.md` in the worktree
    - Example: `workstack create --plan Add_Auth_Feature.md` creates `.workstack/add-auth-feature/` and moves plan to `.workstack/add-auth-feature/.PLAN.md`
- `workstack switch NAME` — prints shell code to cd and activate a worktree (usage: `source <(workstack switch NAME)`)
  - Use `.` for NAME to switch to root repo
- `workstack activate-script NAME` — prints the same activation code (useful for regeneration/piping)
- `workstack list` — lists worktree names with activation hint, e.g. `foo (source /abs/.workstack/foo/activate.sh)`.
- `workstack init [--preset auto|generic|dagster] [--force]` — creates `.workstack/` and scaffolds `.workstack/config.toml`
  - Default `--preset auto` detects Dagster if the root project name is `dagster` (via root `pyproject.toml` or `setup.py`). Otherwise writes the generic template.
  - Adds `.workstack`, `activate.sh`, and `.PLAN.md` to `.gitignore` if present
- `workstack rm NAME [-f|--force]` — removes `.workstack/NAME`. Prompts for confirmation unless `-f`.

Activation
----------

- Direct: `source .workstack/NAME/activate.sh` (tab-completable path)
- Switch: `source <(workstack switch NAME)` (with shell completion)
  - Use `workstack switch .` to switch to root repo
- Alternate: `eval "$(workstack activate-script NAME)"`

Shell completion
----------------

Enable tab completion for worktree names. Run `workstack completion <shell> --help` for detailed setup instructions:

```bash
# Bash
workstack completion bash --help

# Zsh
workstack completion zsh --help

# Fish
workstack completion fish --help
```

Quick setup examples:

```bash
# Bash - add to ~/.bashrc
source <(workstack completion bash)

# Zsh - add to ~/.zshrc
source <(workstack completion zsh)

# Fish - run once
workstack completion fish > ~/.config/fish/completions/workstack.fish
```

After enabling, `workstack switch <TAB>` will complete worktree names.

Plan-based workflow
-------------------

1. Create a plan markdown file in your current Claude session (e.g., `Add_Auth_Feature.md`)
2. Run `workstack create --plan Add_Auth_Feature.md`
   - Derives worktree name from filename: `add-auth-feature` (lowercase, `_` → `-`)
   - Creates worktree at `.workstack/add-auth-feature/`
   - Moves plan to `.workstack/add-auth-feature/.PLAN.md`
3. Switch to the worktree: `source <(workstack switch add-auth-feature)`
4. Launch Claude: `claude`
   - Claude reads `.PLAN.md` automatically on launch
