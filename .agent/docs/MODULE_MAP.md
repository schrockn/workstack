# Module Dependency Map

Comprehensive guide to module organization, responsibilities, and dependencies in the workstack codebase.

**Purpose**: Quick reference for understanding what each module does and how modules interact.

See [ARCHITECTURE.md](../ARCHITECTURE.md) for high-level design overview.

---

## Table of Contents

- [Visual Hierarchy](#visual-hierarchy)
- [Module Responsibilities](#module-responsibilities)
  - [CLI Layer](#cli-layer)
  - [Core Layer](#core-layer)
  - [Operations Layer](#operations-layer)
- [Dependency Rules](#dependency-rules)
- [How to Navigate](#how-to-navigate)

---

## Visual Hierarchy

```
workstack (CLI tool)
│
├─── CLI Layer (User Interface)
│    ├─ cli.py ..................... Entry point, command registration
│    └─ commands/ .................. Individual command implementations
│        ├─ create.py .............. Create worktrees
│        ├─ switch.py .............. Switch between worktrees
│        ├─ list.py ................ List worktrees
│        ├─ remove.py .............. Remove worktrees
│        ├─ sync.py ................ Sync with graphite
│        ├─ tree.py ................ Show worktree tree
│        ├─ init.py ................ Initialize configuration
│        ├─ config.py .............. Manage configuration
│        ├─ gc.py .................. Garbage collection
│        ├─ rename.py .............. Rename worktrees
│        └─ completion.py .......... Shell completion
│
├─── Core Layer (Business Logic)
│    ├─ context.py ................. Dependency injection container
│    ├─ core.py .................... Core business logic
│    ├─ config.py .................. Configuration loading
│    ├─ tree.py .................... Tree visualization logic
│    └─ graphite.py ................ Graphite integration logic
│
├─── Operations Layer (External Integrations)
│    ├─ gitops.py .................. Git operations (ABC + Real + DryRun)
│    ├─ github_ops.py .............. GitHub operations (ABC + Real)
│    ├─ graphite_ops.py ............ Graphite operations (ABC + Real + DryRun)
│    └─ global_config_ops.py ....... Global config operations (ABC + Real)
│
└─── Support
     ├─ presets/ ................... Configuration presets (dagster, generic, etc.)
     └─ shell_integration/ ......... Shell completion and activation scripts
```

---

## Module Responsibilities

### CLI Layer

#### `cli.py`

**Purpose**: Application entry point and command registration.

**Responsibilities**:

- Creates `WorkstackContext` with real implementations
- Registers all commands with Click
- Handles `--dry-run` flag
- Entry point for CLI execution

**Key Functions**:

- `cli()` - Main Click group
- Entry point invoked by `python -m workstack`

**Dependencies**:

- `context.py` - For `create_context()`
- `commands/*` - All command modules

**Example**:

```python
@click.group()
@click.option("--dry-run", is_flag=True)
@click.pass_context
def cli(click_ctx, dry_run):
    click_ctx.obj = create_context(dry_run=dry_run)
```

---

#### `commands/create.py`

**Purpose**: Implements `workstack create` command.

**Responsibilities**:

- Create new worktree with branch
- Support plan file (`--plan` flag)
- Set up environment variables
- Run post-create commands
- Handle branch naming conflicts

**Key Functions**:

- `create_cmd()` - Main command handler
- `_generate_worktree_name()` - Generate name from branch
- Various validation helpers

**Dependencies**:

- `core.py` - For `discover_repo_context()`, `ensure_work_dir()`, `worktree_path_for()`
- `config.py` - For `load_config()`
- Context ops: `git_ops`, `global_config_ops`

**Usage**:

```bash
workstack create my-feature
workstack create --plan plan.md my-feature
workstack create --branch existing-branch my-worktree
```

---

#### `commands/switch.py`

**Purpose**: Implements `workstack switch` command.

**Responsibilities**:

- Switch between worktrees
- Generate shell activation scripts
- Hidden `--internal` variant for shell integration
- Display available worktrees if name ambiguous

**Key Functions**:

- `switch_cmd()` - Main command handler
- `_hidden_switch_cmd()` - Internal variant for shell
- Activation script generation logic

**Dependencies**:

- `core.py` - For `discover_repo_context()`, `worktree_path_for()`
- Context ops: `git_ops`, `global_config_ops`

**Usage**:

```bash
workstack switch my-feature
# Shell sources output to activate environment
```

---

#### `commands/list.py`

**Purpose**: Implements `workstack list` and `workstack ls` commands.

**Responsibilities**:

- List all worktrees for current repo
- Display PR status (if `show_pr_info` enabled)
- Show graphite stack relationships
- Filter current worktree with marker
- Color-coded output

**Key Functions**:

- `list_cmd()` - Main command handler
- `ls_cmd()` - Alias for `list_cmd`
- PR status formatting helpers

**Dependencies**:

- `core.py` - For `discover_repo_context()`
- `graphite.py` - For `get_branch_stack()`
- Context ops: `git_ops`, `github_ops`, `global_config_ops`, `graphite_ops`

**Usage**:

```bash
workstack list
workstack ls  # alias
```

---

#### `commands/remove.py`

**Purpose**: Implements `workstack rm` and `workstack remove` commands.

**Responsibilities**:

- Remove worktree directory
- Optionally delete branch
- Support graphite stack deletion
- Safety checks (prevent removing current worktree)
- Force removal support

**Key Functions**:

- `remove_cmd()` - Main command handler
- `rm_cmd()` - Alias for `remove_cmd`
- Branch deletion logic

**Dependencies**:

- `core.py` - For `discover_repo_context()`, `validate_worktree_name_for_removal()`, `worktree_path_for()`
- Context ops: `git_ops`, `global_config_ops`

**Usage**:

```bash
workstack rm my-feature
workstack rm my-feature --delete-branch
workstack rm my-feature --force
```

---

#### `commands/rename.py`

**Purpose**: Implements `workstack rename` command.

**Responsibilities**:

- Rename worktree (move directory)
- Update git worktree registration
- Validate new name doesn't conflict

**Key Functions**:

- `rename_cmd()` - Main command handler

**Dependencies**:

- `core.py` - For `discover_repo_context()`, `worktree_path_for()`
- Context ops: `git_ops`, `global_config_ops`

**Usage**:

```bash
workstack rename old-name new-name
```

**Note**: Simplest command, good reference for adding new commands.

---

#### `commands/tree.py`

**Purpose**: Implements `workstack tree` command.

**Responsibilities**:

- Display tree visualization of worktrees
- Show graphite stack relationships
- Hierarchical branch display

**Key Functions**:

- `tree_cmd()` - Main command handler

**Dependencies**:

- `tree.py` - For `build_worktree_tree()`
- `core.py` - For `discover_repo_context()`
- Context ops: `git_ops`, `global_config_ops`, `graphite_ops`

**Usage**:

```bash
workstack tree
```

---

#### `commands/sync.py`

**Purpose**: Implements `workstack sync` command.

**Responsibilities**:

- Sync with graphite repository
- Identify merged PRs
- Suggest cleanup of merged worktrees
- Interactive removal prompts

**Key Functions**:

- `sync_cmd()` - Main command handler
- Merged PR detection logic

**Dependencies**:

- `core.py` - For `discover_repo_context()`
- Context ops: `git_ops`, `github_ops`, `graphite_ops`, `global_config_ops`

**Usage**:

```bash
workstack sync
workstack sync --yes  # auto-confirm removals
```

---

#### `commands/init.py`

**Purpose**: Implements `workstack init` command.

**Responsibilities**:

- Initialize global configuration (`~/.workstack/config.toml`)
- Initialize repo configuration (`{work_dir}/config.toml`)
- Set up shell integration (bash/zsh/fish)
- Apply configuration presets (dagster, generic)
- Detect dagster projects automatically

**Key Functions**:

- `init_cmd()` - Main command handler
- `_detect_dagster()` - Auto-detect dagster projects
- Shell setup helpers

**Dependencies**:

- `core.py` - For `discover_repo_context()`, `ensure_work_dir()`
- `presets/` - For configuration templates
- Context ops: `global_config_ops`

**Usage**:

```bash
workstack init
workstack init --preset dagster
workstack init --shell-only
```

---

#### `commands/config.py`

**Purpose**: Implements `workstack config` command group.

**Responsibilities**:

- List global configuration
- Get specific config values
- Set config values
- Subcommands: `list`, `get`, `set`

**Key Functions**:

- `config_cmd()` - Command group
- `config_list_cmd()` - List all config
- `config_get_cmd()` - Get specific value
- `config_set_cmd()` - Set value

**Dependencies**:

- Context ops: `global_config_ops`

**Usage**:

```bash
workstack config list
workstack config get workstacks_root
workstack config set workstacks_root ~/worktrees
```

---

#### `commands/gc.py`

**Purpose**: Implements `workstack gc` command (garbage collection).

**Responsibilities**:

- Identify worktrees with merged PRs
- Suggest safe-to-delete worktrees
- Display cleanup candidates

**Key Functions**:

- `gc_cmd()` - Main command handler

**Dependencies**:

- `core.py` - For `discover_repo_context()`
- Context ops: `git_ops`, `github_ops`, `global_config_ops`

**Usage**:

```bash
workstack gc
```

**Note**: Non-destructive, only suggests deletions.

---

#### `commands/completion.py`

**Purpose**: Implements `workstack completion` command group.

**Responsibilities**:

- Generate shell completion scripts (bash/zsh/fish)
- Provide completion functions for command arguments
- Subcommands: `bash`, `zsh`, `fish`

**Key Functions**:

- `completion_cmd()` - Command group
- `_complete_worktree_name()` - Complete worktree names
- Shell-specific completion generators

**Dependencies**:

- `core.py` - For `discover_repo_context()`
- Context ops: `git_ops`, `global_config_ops`

**Usage**:

```bash
workstack completion bash > ~/.workstack-completion.bash
workstack completion zsh > ~/.workstack-completion.zsh
```

---

### Core Layer

#### `context.py`

**Purpose**: Dependency injection container.

**Responsibilities**:

- Define `WorkstackContext` frozen dataclass
- Factory function `create_context()` for production contexts
- Handle dry-run mode wrapping

**Key Types**:

```python
@dataclass(frozen=True)
class WorkstackContext:
    git_ops: GitOps
    global_config_ops: GlobalConfigOps
    github_ops: GitHubOps
    graphite_ops: GraphiteOps
    dry_run: bool
```

**Key Functions**:

- `create_context(*, dry_run: bool) -> WorkstackContext` - Factory for production contexts

**Dependencies**:

- All `*_ops.py` modules (for ABC types)

**Used By**: All commands (receive via `@click.pass_obj`)

---

#### `core.py`

**Purpose**: Core business logic (pure functions).

**Responsibilities**:

- Repository discovery (find `.git` directory)
- Path construction for worktrees
- Work directory creation
- Safety validation for worktree names

**Key Types**:

```python
@dataclass(frozen=True)
class RepoContext:
    root: Path
    repo_name: str
    work_dir: Path
```

**Key Functions**:

- `discover_repo_context(ctx, start)` - Find repo root, construct paths
- `ensure_work_dir(repo)` - Create work directory if needed
- `worktree_path_for(work_dir, name)` - Construct worktree path
- `validate_worktree_name_for_removal(name)` - Safety checks

**Dependencies**:

- `context.py` - For `WorkstackContext` type
- Uses ops through context parameter (no direct imports)

**Used By**: Nearly all commands

**Note**: Pure functions only, no side effects. All external interactions through context.

---

#### `config.py`

**Purpose**: Configuration loading from TOML.

**Responsibilities**:

- Load repo-specific config from `{work_dir}/config.toml`
- Parse environment variables
- Parse post-create commands

**Key Types**:

```python
@dataclass(frozen=True)
class LoadedConfig:
    env: dict[str, str]
    post_create: list[dict[str, Any]]
```

**Key Functions**:

- `load_config(work_dir)` - Load and parse config file

**Dependencies**: None (pure TOML parsing)

**Used By**: `commands/create.py`, `commands/init.py`

---

#### `tree.py`

**Purpose**: Tree visualization logic.

**Responsibilities**:

- Build tree structure from graphite stacks
- Format tree for display
- Handle complex branch relationships

**Key Functions**:

- `build_worktree_tree()` - Build tree structure from worktrees and stacks

**Dependencies**:

- `graphite.py` - For stack loading

**Used By**: `commands/tree.py`, `commands/list.py`

**Note**: Complex logic, separate module for maintainability.

---

#### `graphite.py`

**Purpose**: Graphite integration logic.

**Responsibilities**:

- Load graphite metadata from `.git/.graphite_cache/`
- Parse graphite stacks
- Extract branch parent relationships

**Key Functions**:

- `get_branch_stack(ctx, repo, branch)` - Get stack for specific branch
- `_load_graphite_cache()` - Load graphite metadata

**Dependencies**:

- `context.py` - For `WorkstackContext` type
- Uses `graphite_ops` through context

**Used By**: `commands/list.py`, `tree.py`

---

### Operations Layer

#### `gitops.py`

**Purpose**: Git operations abstraction.

**Interfaces/Classes**:

- `GitOps` (ABC) - 9 abstract methods
- `RealGitOps` - Production implementation using `subprocess`
- `DryRunGitOps` - Dry-run wrapper

**Operations**:

- `list_worktrees(repo_root)` - Parse `git worktree list --porcelain`
- `add_worktree(repo_root, branch, path, ...)` - Create worktree
- `remove_worktree(repo_root, path, force)` - Remove worktree
- `move_worktree(repo_root, source, dest)` - Move worktree
- `get_current_branch(repo_root)` - Get current branch name
- `checkout_branch(repo_root, branch)` - Switch branches
- `detect_default_branch(repo_root)` - Find main/master
- `delete_branch_with_graphite(repo_root, branch, ...)` - Delete branch
- `get_git_common_dir(cwd)` - Find main repo `.git` (worktree support)

**Dependencies**: None (uses `subprocess`)

**Used By**: Most commands (through context)

**Note**: Reference implementation for ABC pattern.

---

#### `github_ops.py`

**Purpose**: GitHub API operations.

**Interfaces/Classes**:

- `GitHubOps` (ABC) - 2 abstract methods
- `RealGitHubOps` - Production implementation using `gh` CLI

**Operations**:

- `get_prs_for_repo(repo_root)` - Fetch all PRs via `gh pr list --json`
- `get_pr_status(branch, prs)` - Get PR state, checks, reviews for branch

**Dependencies**: None (uses `gh` CLI via `subprocess`)

**Graceful Degradation**: Returns `None` if `gh` not available

**Used By**: `commands/list.py`, `commands/sync.py`, `commands/gc.py`

---

#### `graphite_ops.py`

**Purpose**: Graphite CLI operations.

**Interfaces/Classes**:

- `GraphiteOps` (ABC) - 2 abstract methods
- `RealGraphiteOps` - Production implementation using `gt` CLI
- `DryRunGraphiteOps` - Dry-run wrapper

**Operations**:

- `get_graphite_url(repo_root)` - Construct graphite web URL
- `sync(repo_root)` - Run `gt repo sync`

**Dependencies**: None (uses `gt` CLI via `subprocess`)

**Used By**: `commands/list.py`, `commands/sync.py`

---

#### `global_config_ops.py`

**Purpose**: Global configuration management.

**Interfaces/Classes**:

- `GlobalConfigOps` (ABC) - 7 abstract methods
- `RealGlobalConfigOps` - Production implementation

**Operations**:

- `get_workstacks_root()` - Get workstacks root directory
- `get_use_graphite()` - Check if graphite enabled
- `get_show_pr_info()` - Check if PR info should be shown
- `set(key, value)` - Update config value
- `config_path()` - Get config file path
- `config_exists()` - Check if config file exists
- `get_shell_setup_complete()` - Check shell setup status

**Dependencies**: None (direct TOML file I/O)

**Used By**: Most commands (through context)

**Note**: Manages `~/.workstack/config.toml`

---

## Dependency Rules

### Import Direction

```
commands/ ──> core.py ──> context.py ──> *_ops.py
    │           │
    │           └──> config.py
    │
    └──> graphite.py ──> graphite_ops.py (via context)
    └──> tree.py
```

**Rules**:

1. **Commands import core and context** - Never directly import ops
2. **Core imports context** - Uses ops through context parameter
3. **Ops interfaces have no dependencies** - No imports from commands or core
4. **No circular dependencies** - Enforced by architecture

### Testing Dependencies

```
tests/commands/ ──> tests/fakes/ (in-memory implementations)
tests/integration/ ──> src/workstack/ (real implementations)
```

**Fake Implementations**:

- Located in `tests/fakes/`
- Inherit from ABC interfaces
- All state via constructor
- No public setup methods

---

## How to Navigate

### "I want to modify command behavior"

1. Find command in `commands/` directory
2. Read command file to understand current behavior
3. Check `core.py` if command uses core functions
4. Check relevant ops interface if interacting with git/github/graphite

**Example**: Modify how worktrees are listed

- Read: `commands/list.py`
- Check: `core.py` for `discover_repo_context()`
- Check: `gitops.py` for `list_worktrees()`

---

### "I want to add a new git operation"

1. Add abstract method to `GitOps` in `gitops.py`
2. Implement in `RealGitOps`
3. Implement in `FakeGitOps` (`tests/fakes/gitops.py`)
4. Add to `DryRunGitOps` if destructive operation

---

### "I want to add a new command"

1. Create new file in `commands/`
2. Follow pattern from existing commands (e.g., `commands/rename.py` is simple)
3. Register in `cli.py`
4. Add tests in `tests/commands/`

---

### "I want to understand configuration"

1. **Global config**: Read `global_config_ops.py`
   - Location: `~/.workstack/config.toml`
   - Keys: `workstacks_root`, `use_graphite`, `show_pr_info`
2. **Repo config**: Read `config.py`
   - Location: `{work_dir}/config.toml`
   - Sections: `[env]`, `[[post_create]]`
3. **How configs are created**: See `commands/init.py`
4. **Example configurations**: See `presets/`

---

### "I want to understand testing approach"

1. Read `tests/CLAUDE.md` for testing philosophy
2. Look at `tests/fakes/` for fake implementations
3. Study `tests/commands/test_rm.py` for command test pattern
4. Study `tests/integration/test_gitops_integration.py` for integration test pattern

**Key Pattern**:

- Unit tests: Use fakes, `CliRunner.isolated_filesystem()`
- Integration tests: Use real implementations, temporary repos

---

### "I want to find where a feature is implemented"

See: [FEATURE_INDEX.md](../FEATURE_INDEX.md) - Lookup table mapping features to files

---

## Related Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) - High-level system design
- [GLOSSARY.md](../GLOSSARY.md) - Terminology reference
- [FEATURE_INDEX.md](../FEATURE_INDEX.md) - Feature → file mapping
- [CLAUDE.md](../CLAUDE.md) - Coding standards
