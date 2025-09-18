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

- `workstack create NAME [--branch BRANCH] [--ref REF]`
  - Creates `.workstack/NAME`, writes `.env`, runs post-create commands
  - Creates and checks out a branch in the worktree:
    - Default branch name: `work/<NAME>` (sanitized)
    - Base ref: `--ref REF` (defaults to `HEAD`)
  - Also writes `.workstack/NAME/activate.sh` (executable)
- `workstack activate-script NAME` — prints the same activation code (useful for regeneration/piping)
- `workstack list` — lists worktree names with activation hint, e.g. `foo (source /abs/.workstack/foo/activate.sh)`.
- `workstack init [--preset auto|generic|dagster] [--force]` — creates `.workstack/` and scaffolds `.workstack/config.toml`
  - Default `--preset auto` detects Dagster if the root project name is `dagster` (via root `pyproject.toml` or `setup.py`). Otherwise writes the generic template.
- `workstack rm NAME [-f|--force]` — removes `.workstack/NAME`. Prompts for confirmation unless `-f`.

Activation
----------

- Preferred: `source .workstack/NAME/activate.sh` (tab-completable path)
- Alternate: `eval "$(uv run workstack activate-script NAME)"`
