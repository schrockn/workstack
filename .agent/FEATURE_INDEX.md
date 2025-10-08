# Feature Index

Quick reference for locating feature implementations, tests, and related code.

**Purpose**: Fast lookup table for "where is feature X implemented?" questions. Use line numbers to jump directly to code.

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

| Feature            | Implementation                                                         | Tests                               | Notes                               |
| ------------------ | ---------------------------------------------------------------------- | ----------------------------------- | ----------------------------------- |
| Create worktree    | `src/workstack/commands/create.py:1-365`                               | `tests/commands/test_plan.py`       | Plan file support, branch creation  |
| Switch worktree    | `src/workstack/commands/switch.py:1-222`                               | `tests/commands/test_switch.py`     | Shell activation, env loading       |
| List worktrees     | `src/workstack/commands/list.py:1-371`                                 | `tests/commands/list/test_basic.py` | PR status optional, graphite stacks |
| Remove worktree    | `src/workstack/commands/remove.py:1-305`                               | `tests/commands/test_rm.py`         | Branch deletion, force flag         |
| Rename worktree    | `src/workstack/commands/rename.py:1-69`                                | `tests/commands/test_rename.py`     | Directory move + git update         |
| Tree visualization | `src/workstack/commands/tree.py:1-44`<br>`src/workstack/tree.py:1-410` | `tests/commands/test_tree.py`       | Graphite stack hierarchy            |
| Initialize config  | `src/workstack/commands/init.py:1-373`                                 | N/A                                 | Presets, shell integration          |
| Manage config      | `src/workstack/commands/config.py:1-179`                               | N/A                                 | Get/set/list operations             |
| Garbage collection | `src/workstack/commands/gc.py:1-90`                                    | N/A                                 | Merged PR identification            |
| Sync with graphite | `src/workstack/commands/sync.py:1-181`                                 | `tests/test_sync.py`                | PR detection, cleanup               |
| Shell completion   | `src/workstack/commands/completion.py:1-112`                           | `tests/commands/test_completion.py` | Bash/zsh/fish support               |

---

## Git Operations

All git operations are defined in `src/workstack/gitops.py`.

| Operation             | ABC Interface       | Real Implementation | Fake Implementation            | Description                                 |
| --------------------- | ------------------- | ------------------- | ------------------------------ | ------------------------------------------- |
| List worktrees        | `gitops.py:41-43`   | `gitops.py:147-177` | `tests/fakes/gitops.py:43-45`  | Parse `git worktree list --porcelain`       |
| Add worktree          | `gitops.py:60-79`   | `gitops.py:179-206` | `tests/fakes/gitops.py:62-74`  | `git worktree add -b <branch> <path>`       |
| Remove worktree       | `gitops.py:86-95`   | `gitops.py:208-223` | `tests/fakes/gitops.py:87-92`  | `git worktree remove <path> [--force]`      |
| Move worktree         | `gitops.py:81-84`   | `gitops.py:225-233` | `tests/fakes/gitops.py:76-85`  | `git worktree move <source> <dest>`         |
| Get current branch    | `gitops.py:45-48`   | `gitops.py:122-137` | `tests/fakes/gitops.py:47-49`  | `git branch --show-current`                 |
| Checkout branch       | `gitops.py:97-99`   | `gitops.py:235-242` | `tests/fakes/gitops.py:94-96`  | `git checkout <branch>`                     |
| Detect default branch | `gitops.py:50-53`   | `gitops.py:139-145` | `tests/fakes/gitops.py:51-56`  | `git symbolic-ref refs/remotes/origin/HEAD` |
| Delete branch         | `gitops.py:101-111` | `gitops.py:244-267` | `tests/fakes/gitops.py:98-100` | Branch deletion with graphite support       |
| Get git common dir    | `gitops.py:55-58`   | `gitops.py:113-120` | `tests/fakes/gitops.py:58-60`  | Worktree support via `git rev-parse`        |

**Integration Tests**: `tests/integration/test_gitops_integration.py`

---

## GitHub Operations

All GitHub operations are defined in `src/workstack/github_ops.py`.

| Operation     | ABC Interface         | Real Implementation     | Fake Implementation               | Description                           |
| ------------- | --------------------- | ----------------------- | --------------------------------- | ------------------------------------- |
| Get all PRs   | `github_ops.py:58-66` | `github_ops.py:94-146`  | `tests/fakes/github_ops.py:15-20` | `gh pr list --json` with full PR data |
| Get PR status | `github_ops.py:68-85` | `github_ops.py:148-228` | `tests/fakes/github_ops.py:22-27` | Parse PR state, checks, reviews       |

**Notes**:

- Gracefully handles missing `gh` CLI (returns `None`)
- Used for PR status display and merged PR detection

---

## Graphite Operations

All graphite operations are defined in `src/workstack/graphite_ops.py`.

| Operation        | ABC Interface           | Real Implementation     | Fake Implementation                 | Description                |
| ---------------- | ----------------------- | ----------------------- | ----------------------------------- | -------------------------- |
| Get graphite URL | `graphite_ops.py:22-34` | `graphite_ops.py:53-67` | `tests/fakes/graphite_ops.py:9-11`  | Construct web URL for repo |
| Sync             | `graphite_ops.py:36-44` | `graphite_ops.py:69-84` | `tests/fakes/graphite_ops.py:13-15` | Run `gt repo sync` command |

**Related**:

- Graphite metadata loading: `src/workstack/graphite.py:1-241`
- Stack parsing and branch relationships

---

## Configuration

| Feature        | Implementation                                                           | Tests                               | Description                           |
| -------------- | ------------------------------------------------------------------------ | ----------------------------------- | ------------------------------------- |
| Global config  | `src/workstack/global_config_ops.py:1-248`                               | N/A                                 | `~/.workstack/config.toml` management |
| Repo config    | `src/workstack/config.py:1-41`                                           | `tests/core/test_config_and_env.py` | `{work_dir}/config.toml` loading      |
| Config presets | `src/workstack/presets/dagster.py`<br>`src/workstack/presets/generic.py` | `tests/core/test_setup_template.py` | Template configurations               |

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

| Feature           | Implementation                           | Tests                                      | Description                        |
| ----------------- | ---------------------------------------- | ------------------------------------------ | ---------------------------------- |
| Repo discovery    | `src/workstack/core.py:18-50`            | N/A                                        | Walk tree to find `.git` directory |
| Path construction | `src/workstack/core.py:59-61`            | N/A                                        | `worktree_path_for()` helper       |
| Work dir creation | `src/workstack/core.py:53-56`            | N/A                                        | `ensure_work_dir()` helper         |
| Name validation   | `src/workstack/core.py:64-94`            | N/A                                        | Safety checks for removal          |
| Worktree naming   | `src/workstack/commands/create.py:14-64` | `tests/core/test_naming.py`                | Generate names from branches       |
| Branch detection  | `src/workstack/gitops.py:139-145`        | `tests/core/test_detect_default_branch.py` | Detect main vs master              |
| Dagster detection | `src/workstack/commands/init.py:42-55`   | `tests/core/test_detect_dagster.py`        | Auto-detect dagster projects       |
| Stack loading     | `src/workstack/graphite.py:1-241`        | N/A                                        | Load graphite metadata             |
| Tree building     | `src/workstack/tree.py:1-410`            | N/A                                        | Build visualization tree           |

**Key Types**:

- `RepoContext` - Repo root + work dir (`src/workstack/core.py:9-15`)
- `WorkstackContext` - DI container (`src/workstack/context.py:11-23`)
- `LoadedConfig` - Parsed config (`src/workstack/config.py`)

---

## Shell Integration

| Feature               | Implementation                                  | Description                         |
| --------------------- | ----------------------------------------------- | ----------------------------------- |
| Bash activation       | `src/workstack/shell_integration/activate.bash` | Source in `.bashrc`                 |
| Zsh activation        | `src/workstack/shell_integration/activate.zsh`  | Source in `.zshrc`                  |
| Fish activation       | `src/workstack/shell_integration/activate.fish` | Source in `config.fish`             |
| Completion generation | `src/workstack/commands/completion.py:1-112`    | Generate shell-specific completions |

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
2. **Use line numbers** to jump directly to code in your editor
3. **Check tests** for usage examples and edge cases

**Example**: Find where worktree removal is implemented

- Search for "Remove worktree"
- See: `src/workstack/commands/remove.py:1-305`
- Tests: `tests/commands/test_rm.py`

---

### Understanding a Feature

1. **Find ABC interface** (for ops-related features)
   - Example: `gitops.py:86-95` for remove operation
2. **Read interface docstrings** to understand contract
3. **Check real implementation** for actual behavior
4. **Review tests** for edge cases and examples

**Example**: Understand how branch deletion works

- Interface: `gitops.py:101-111` (abstract method)
- Real impl: `gitops.py:244-267` (subprocess logic)
- Fake impl: `tests/fakes/gitops.py:98-100` (test double)

---

### Modifying a Feature

1. **Locate implementation** in this index
2. **Read [ARCHITECTURE.md](ARCHITECTURE.md)** to understand design
3. **Check [GLOSSARY.md](GLOSSARY.md)** for terminology
4. **Modify code** following patterns in [CLAUDE.md](CLAUDE.md)
5. **Update corresponding tests**

**Example**: Add `--json` output to `workstack list`

- Find: `commands/list.py:1-371`
- Understand: Read command structure
- Modify: Add `--json` flag, format output
- Test: Update `tests/commands/list/test_basic.py`

---

### Adding a New Feature

**For new command**:

- See: [docs/guides/ADDING_A_COMMAND.md](docs/guides/ADDING_A_COMMAND.md)
- Pattern: Study `commands/rename.py` (simple) or `commands/create.py` (complex)

**For new ops interface**:

- See: [docs/guides/ADDING_AN_OPS_INTERFACE.md](docs/guides/ADDING_AN_OPS_INTERFACE.md)
- Pattern: Study `gitops.py` (ABC + Real + DryRun)

---

## Cross-References

### By Module

- **CLI entry** → `src/workstack/cli.py`
- **Commands** → `src/workstack/commands/*.py` (see [.agent/docs/MODULE_MAP.md](.agent/docs/MODULE_MAP.md))
- **Operations** → `src/workstack/*_ops.py` (see [ARCHITECTURE.md](ARCHITECTURE.md))
- **Testing** → `tests/fakes/*.py` (see [tests/CLAUDE.md](tests/CLAUDE.md))

### By Task

- **Add command** → [docs/guides/ADDING_A_COMMAND.md](docs/guides/ADDING_A_COMMAND.md)
- **Add ops interface** → [docs/guides/ADDING_AN_OPS_INTERFACE.md](docs/guides/ADDING_AN_OPS_INTERFACE.md)
- **Write tests** → [docs/guides/TESTING_GUIDE.md](docs/guides/TESTING_GUIDE.md)
- **Understand patterns** → [.agent/docs/PATTERNS.md](.agent/docs/PATTERNS.md)

### By Concept

- **Architecture overview** → [ARCHITECTURE.md](ARCHITECTURE.md)
- **Module organization** → [.agent/docs/MODULE_MAP.md](.agent/docs/MODULE_MAP.md)
- **Terminology** → [GLOSSARY.md](GLOSSARY.md)
- **Coding standards** → [CLAUDE.md](CLAUDE.md)

---

## Maintenance

When adding or modifying features, keep this index current:

1. **Add new features** to appropriate table
2. **Update line numbers** if code moves significantly
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
