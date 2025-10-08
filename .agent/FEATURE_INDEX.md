# Feature Index

Quick reference for locating feature implementations, tests, and related code.

**Purpose**: Fast lookup table for "where is feature X implemented?" questions.

**Format**: All file paths are relative to repository root.

---

## Table of Contents

- [Core Features](#core-features)
- [Git Operations](#git-operations)
- [GitHub Operations](#github-operations)
- [Graphite Operations](#graphite-operations)
- [Configuration](#configuration)
- [Core Business Logic](#core-business-logic)
- [Shell Integration](#shell-integration)
- [How to Use This Index](#how-to-use-this-index)

---

## Core Features

| Feature            | Implementation                                              | Tests                               | Notes                               |
| ------------------ | ----------------------------------------------------------- | ----------------------------------- | ----------------------------------- |
| Create worktree    | `src/workstack/commands/create.py`                          | `tests/commands/test_plan.py`       | Plan file support, branch creation  |
| Switch worktree    | `src/workstack/commands/switch.py`                          | `tests/commands/test_switch.py`     | Shell activation, env loading       |
| List worktrees     | `src/workstack/commands/list.py`                            | `tests/commands/list/test_basic.py` | PR status optional, graphite stacks |
| Remove worktree    | `src/workstack/commands/remove.py`                          | `tests/commands/test_rm.py`         | Branch deletion, force flag         |
| Rename worktree    | `src/workstack/commands/rename.py`                          | `tests/commands/test_rename.py`     | Directory move + git update         |
| Tree visualization | `src/workstack/commands/tree.py`<br>`src/workstack/tree.py` | `tests/commands/test_tree.py`       | Graphite stack hierarchy            |
| Initialize config  | `src/workstack/commands/init.py`                            | N/A                                 | Presets, shell integration          |
| Manage config      | `src/workstack/commands/config.py`                          | N/A                                 | Get/set/list operations             |
| Garbage collection | `src/workstack/commands/gc.py`                              | N/A                                 | Merged PR identification            |
| Sync with graphite | `src/workstack/commands/sync.py`                            | `tests/test_sync.py`                | PR detection, cleanup               |
| Shell completion   | `src/workstack/commands/completion.py`                      | `tests/commands/test_completion.py` | Bash/zsh/fish support               |

---

## Git Operations

All git operations are defined in `src/workstack/gitops.py`.

| Operation             | ABC Interface | Real Implementation | Fake Implementation     | Description                                 |
| --------------------- | ------------- | ------------------- | ----------------------- | ------------------------------------------- |
| List worktrees        | `gitops.py`   | `gitops.py`         | `tests/fakes/gitops.py` | Parse `git worktree list --porcelain`       |
| Add worktree          | `gitops.py`   | `gitops.py`         | `tests/fakes/gitops.py` | `git worktree add -b <branch> <path>`       |
| Remove worktree       | `gitops.py`   | `gitops.py`         | `tests/fakes/gitops.py` | `git worktree remove <path> [--force]`      |
| Move worktree         | `gitops.py`   | `gitops.py`         | `tests/fakes/gitops.py` | `git worktree move <source> <dest>`         |
| Get current branch    | `gitops.py`   | `gitops.py`         | `tests/fakes/gitops.py` | `git branch --show-current`                 |
| Checkout branch       | `gitops.py`   | `gitops.py`         | `tests/fakes/gitops.py` | `git checkout <branch>`                     |
| Detect default branch | `gitops.py`   | `gitops.py`         | `tests/fakes/gitops.py` | `git symbolic-ref refs/remotes/origin/HEAD` |
| Delete branch         | `gitops.py`   | `gitops.py`         | `tests/fakes/gitops.py` | Branch deletion with graphite support       |
| Get git common dir    | `gitops.py`   | `gitops.py`         | `tests/fakes/gitops.py` | Worktree support via `git rev-parse`        |

**Integration Tests**: `tests/integration/test_gitops_integration.py`

---

## GitHub Operations

All GitHub operations are defined in `src/workstack/github_ops.py`.

| Operation     | ABC Interface   | Real Implementation | Fake Implementation         | Description                           |
| ------------- | --------------- | ------------------- | --------------------------- | ------------------------------------- |
| Get all PRs   | `github_ops.py` | `github_ops.py`     | `tests/fakes/github_ops.py` | `gh pr list --json` with full PR data |
| Get PR status | `github_ops.py` | `github_ops.py`     | `tests/fakes/github_ops.py` | Parse PR state, checks, reviews       |

**Notes**:

- Gracefully handles missing `gh` CLI (returns `None`)
- Used for PR status display and merged PR detection

---

## Graphite Operations

All graphite operations are defined in `src/workstack/graphite_ops.py`.

| Operation        | ABC Interface     | Real Implementation | Fake Implementation           | Description                |
| ---------------- | ----------------- | ------------------- | ----------------------------- | -------------------------- |
| Get graphite URL | `graphite_ops.py` | `graphite_ops.py`   | `tests/fakes/graphite_ops.py` | Construct web URL for repo |
| Sync             | `graphite_ops.py` | `graphite_ops.py`   | `tests/fakes/graphite_ops.py` | Run `gt repo sync` command |

**Related**:

- Graphite metadata loading: `src/workstack/graphite.py`
- Stack parsing and branch relationships

---

## Configuration

| Feature        | Implementation                                                               | Tests                               | Description                           |
| -------------- | ---------------------------------------------------------------------------- | ----------------------------------- | ------------------------------------- |
| Global config  | `src/workstack/global_config_ops.py`                                         | N/A                                 | `~/.workstack/config.toml` management |
| Repo config    | `src/workstack/config.py`                                                    | `tests/core/test_config_and_env.py` | `{work_dir}/config.toml` loading      |
| Config presets | `src/workstack/presets/dagster.toml`<br>`src/workstack/presets/generic.toml` | `tests/core/test_setup_template.py` | Template configurations               |

**Global Config Operations** (`global_config_ops.py`):

- `get_workstacks_root()` - Get root directory
- `get_use_graphite()` - Check graphite enabled
- `get_show_pr_info()` - Check PR display setting
- `set(key, value)` - Update config
- `config_path()` - Get config file path
- `config_exists()` - Check if config exists
- `get_shell_setup_complete()` - Check shell setup

**Repo Config** (`config.py`):

- `load_config(work_dir)` - Load TOML config
- Returns `LoadedConfig` with `env` dict and `post_create` list

---

## Core Business Logic

| Feature           | Implementation                     | Tests                                      | Description                        |
| ----------------- | ---------------------------------- | ------------------------------------------ | ---------------------------------- |
| Repo discovery    | `src/workstack/core.py`            | N/A                                        | Walk tree to find `.git` directory |
| Path construction | `src/workstack/core.py`            | N/A                                        | `worktree_path_for()` helper       |
| Work dir creation | `src/workstack/core.py`            | N/A                                        | `ensure_work_dir()` helper         |
| Name validation   | `src/workstack/core.py`            | N/A                                        | Safety checks for removal          |
| Worktree naming   | `src/workstack/commands/create.py` | `tests/core/test_naming.py`                | Generate names from branches       |
| Branch detection  | `src/workstack/gitops.py`          | `tests/core/test_detect_default_branch.py` | Detect main vs master              |
| Dagster detection | `src/workstack/commands/init.py`   | `tests/core/test_detect_dagster.py`        | Auto-detect dagster projects       |
| Stack loading     | `src/workstack/graphite.py`        | N/A                                        | Load graphite metadata             |
| Tree building     | `src/workstack/tree.py`            | N/A                                        | Build visualization tree           |

**Key Types**:

- `RepoContext` - Repo root + work dir (`src/workstack/core.py`)
- `WorkstackContext` - DI container (`src/workstack/context.py`)
- `LoadedConfig` - Parsed config (`src/workstack/config.py`)

---

## Shell Integration

| Feature               | Implementation                                      | Description                         |
| --------------------- | --------------------------------------------------- | ----------------------------------- |
| Bash activation       | `src/workstack/shell_integration/bash_wrapper.sh`   | Source in `.bashrc`                 |
| Zsh activation        | `src/workstack/shell_integration/zsh_wrapper.sh`    | Source in `.zshrc`                  |
| Fish activation       | `src/workstack/shell_integration/fish_wrapper.fish` | Source in `config.fish`             |
| Completion generation | `src/workstack/commands/completion.py`              | Generate shell-specific completions |

**Setup**:

- Automatic setup via `workstack init` command
- Manual setup via `workstack completion <shell>` output

**Activation Script Features**:

- `ws` command for quick worktree switching
- Automatic environment variable loading
- Current directory change to worktree path

---

## How to Use This Index

### Finding Implementation

1. **Search this file** for feature keyword (Cmd+F / Ctrl+F)
2. **Navigate to the referenced file** in your editor
3. **Check tests** for usage examples and edge cases

**Example**: Find where worktree removal is implemented

- Search for "Remove worktree"
- See: `src/workstack/commands/remove.py`
- Tests: `tests/commands/test_rm.py`

---

### Understanding a Feature

1. **Find ABC interface** (for ops-related features)
   - Example: `gitops.py` for remove operation
2. **Read interface docstrings** to understand contract
3. **Check real implementation** for actual behavior
4. **Review tests** for edge cases and examples

**Example**: Understand how branch deletion works

- Interface: `gitops.py` (abstract method)
- Real impl: `gitops.py` (subprocess logic)
- Fake impl: `tests/fakes/gitops.py` (test double)

---

### Modifying a Feature

1. **Locate implementation** in this index
2. **Read [ARCHITECTURE.md](ARCHITECTURE.md)** to understand design
3. **Check [GLOSSARY.md](GLOSSARY.md)** for terminology
4. **Modify code** following patterns in [CLAUDE.md](CLAUDE.md)
5. **Update corresponding tests**

**Example**: Add `--json` output to `workstack list`

- Find: `commands/list.py`
- Understand: Read command structure
- Modify: Add `--json` flag, format output
- Test: Update `tests/commands/list/test_basic.py`

---

### Adding a New Feature

**For new command**:

- Pattern: Study `commands/rename.py` (simple) or `commands/create.py` (complex)

**For new ops interface**:

- Pattern: Study `gitops.py` (ABC + Real + DryRun)

---

## Cross-References

### By Module

- **CLI entry** → `src/workstack/cli.py`
- **Commands** → `src/workstack/commands/*.py` (see [.agent/docs/MODULE_MAP.md](.agent/docs/MODULE_MAP.md))
- **Operations** → `src/workstack/*_ops.py` (see [ARCHITECTURE.md](ARCHITECTURE.md))
- **Testing** → `tests/fakes/*.py` (see [tests/CLAUDE.md](tests/CLAUDE.md))

### By Concept

- **Architecture overview** → [ARCHITECTURE.md](ARCHITECTURE.md)
- **Module organization** → [.agent/docs/MODULE_MAP.md](.agent/docs/MODULE_MAP.md)
- **Terminology** → [GLOSSARY.md](GLOSSARY.md)
- **Coding standards** → [CLAUDE.md](CLAUDE.md)

---

## Maintenance

When adding or modifying features, keep this index current:

1. **Add new features** to appropriate table
2. **Update file paths** if files are moved or renamed
3. **Add new categories** if feature doesn't fit existing ones
4. **Keep test paths current** as tests are added/moved

**Frequency**: Update after each significant feature addition or refactoring.

---

## Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and patterns
- [GLOSSARY.md](GLOSSARY.md) - Terminology reference
- [.agent/docs/MODULE_MAP.md](.agent/docs/MODULE_MAP.md) - Detailed module guide
- [CLAUDE.md](CLAUDE.md) - Coding standards
- [README.md](README.md) - User-facing documentation
