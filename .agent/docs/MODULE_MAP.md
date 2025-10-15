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
├── cli/ .......................... User-facing CLI package
│   ├─ cli.py ..................... Entry point, Click group registration
│   ├─ core.py .................... Repo discovery + worktree path helpers
│   ├─ config.py .................. Repository config loader
│   ├─ tree.py .................... Tree rendering helpers
│   ├─ graphite.py ................ Graphite stack helpers
│   ├─ shell_utils.py ............. Shared shell helpers
│   ├─ commands/ .................. Individual Click commands
│   │   ├─ create.py .............. Create worktrees
│   │   ├─ move.py ................ Move/swap branches across worktrees
│   │   ├─ switch.py .............. Switch between worktrees
│   │   ├─ list.py ................ List worktrees
│   │   ├─ status.py .............. Aggregate worktree status
│   │   ├─ remove.py .............. Remove worktrees
│   │   ├─ rename.py .............. Rename worktrees
│   │   ├─ init.py ................ Initialize configuration
│   │   ├─ config.py .............. Manage configuration
│   │   ├─ prepare_cwd_recovery.py  Print shell snippet for dir recovery
│   │   ├─ gc.py .................. Garbage collection
│   │   ├─ sync.py ................ Sync with graphite
│   │   ├─ tree.py ................ Tree visualization command
│   │   ├─ completion.py .......... Shell completion
│   │   └─ shell_integration.py ... Hidden __shell command for wrappers
│   └─ shell_integration/ ......... Shell wrapper scripts + handler
│       ├─ bash_wrapper.sh ........ Bash shell function wrapper
│       ├─ zsh_wrapper.sh ......... Zsh shell function wrapper
│       ├─ fish_wrapper.fish ...... Fish shell function wrapper
│       └─ handler.py ............. Unified shell integration handler
│
├── core/ ........................ External operations + DI
│   ├─ context.py ................. Dependency injection container + factory
│   ├─ gitops.py .................. Git operations (ABC + Real + DryRun)
│   ├─ global_config_ops.py ....... Global config operations (ABC + Real)
│   ├─ github_ops.py .............. GitHub operations (ABC + Real)
│   ├─ graphite_ops.py ............ Graphite operations (ABC + Real + DryRun)
│   └─ file_utils.py .............. Shared filesystem helpers
│
├── status/ ...................... Aggregated status system
│   ├─ orchestrator.py ............ Coordinates collectors and renderers
│   ├─ collectors/ ................ Git, Graphite, GitHub, plan file collectors
│   └─ renderers/ ................. Rendering strategies (SimpleRenderer, etc.)
│
└── dev_cli/ ..................... Developer PEP 723 scripts
    └─ commands/ ................. Maintenance scripts invoked via `workstack-dev`
```

---

## Module Responsibilities

### CLI Layer

#### `cli/cli.py`

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

- `core/context.py` - For `create_context()`
- `cli/commands/*` - All command modules

**Example**:

```python
@click.group()
@click.option("--dry-run", is_flag=True)
@click.pass_context
def cli(click_ctx, dry_run):
    click_ctx.obj = create_context(dry_run=dry_run)
```

---

#### `cli/commands/create.py`

**Purpose**: Implements `workstack create` command.

**Responsibilities**:

- Create new worktree with branch
- Support plan file (`--plan` flag)
- Set up environment variables
- Run post-create commands
- Handle branch naming conflicts
- Generate directory change script (via `--script` flag)

**Key Functions**:

- `create_cmd()` - Main command handler with optional `--script` flag
- `_generate_worktree_name()` - Generate name from branch
- `_render_cd_script()` - Generate shell cd script to new worktree
- Various validation helpers

**Shell Integration**: Supports `--script` flag for automatic directory change to newly created worktree

**Dependencies**:

- `cli/core.py` - For `discover_repo_context()`, `ensure_work_dir()`, `worktree_path_for()`
- `cli/config.py` - For `load_config()`
- Context ops: `git_ops`, `global_config_ops`

**Usage**:

```bash
workstack create my-feature
workstack create --plan plan.md my-feature
workstack create --branch existing-branch my-worktree
```

---

#### `cli/commands/switch.py`

**Purpose**: Implements `workstack switch` command.

**Responsibilities**:

- Switch between worktrees
- Generate shell activation scripts (via `--script` flag)
- Display available worktrees if name ambiguous

**Key Functions**:

- `switch_cmd()` - Main command handler with optional `--script` flag
- `_render_activation_script()` - Generate shell activation script

**Shell Integration**: Works through unified `__shell` handler (see `shell_integration.py`)

**Dependencies**:

- `cli/core.py` - For `discover_repo_context()`, `worktree_path_for()`
- Context ops: `git_ops`, `global_config_ops`

**Usage**:

```bash
workstack switch my-feature
# Shell sources output to activate environment
```

---

#### `cli/commands/list.py`

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

- `cli/core.py` - For `discover_repo_context()`
- `cli/graphite.py` - For `get_branch_stack()`
- Context ops: `git_ops`, `github_ops`, `global_config_ops`, `graphite_ops`

**Usage**:

```bash
workstack list
workstack ls  # alias
```

---

#### `cli/commands/status.py`

**Purpose**: Implements `workstack status` command.

**Responsibilities**:

- Discover current repository and active worktree
- Collect git status, graphite stack data, GitHub PR info, and local plan file details
- Present aggregated status via renderer (currently `SimpleRenderer`)
- Exit with friendly error if not inside a managed worktree

**Key Functions**:

- `status_cmd()` - Click command entry point
- `StatusOrchestrator.collect_status()` - Orchestrator invoked by command

**Dependencies**:

- `cli/core.py` - For `discover_repo_context()`
- `status/orchestrator.py` - Collector orchestration
- `status/collectors/*` - Git, Graphite, GitHub, plan collectors
- Context ops: `git_ops`, `github_ops`, `graphite_ops`

**Usage**:

```bash
workstack status
```

**Notes**: Integration-level behavior covered by `tests/commands/test_status.py`.

---

#### `cli/commands/remove.py`

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

- `cli/core.py` - For `discover_repo_context()`, `validate_worktree_name_for_removal()`, `worktree_path_for()`
- Context ops: `git_ops`, `global_config_ops`

**Usage**:

```bash
workstack rm my-feature
workstack rm my-feature --delete-branch
workstack rm my-feature --force
```

---

#### `cli/commands/rename.py`

**Purpose**: Implements `workstack rename` command.

**Responsibilities**:

- Rename worktree (move directory)
- Update git worktree registration
- Validate new name doesn't conflict

**Key Functions**:

- `rename_cmd()` - Main command handler

**Dependencies**:

- `cli/core.py` - For `discover_repo_context()`, `worktree_path_for()`
- Context ops: `git_ops`, `global_config_ops`

**Usage**:

```bash
workstack rename old-name new-name
```

**Note**: Simplest command, good reference for adding new commands.

---

#### `cli/commands/move.py`

**Purpose**: Implements `workstack move` command.

**Responsibilities**:

- Resolve source worktree via `--current`, `--branch`, or `--worktree`
- Detect whether to create, move, or swap based on target state
- Enforce clean working state unless `--force` is provided
- Print human-friendly progress for each operation (checkout, creation, swap)

**Key Functions**:

- `resolve_source_worktree()` - Flag resolution helper
- `detect_operation_type()` - Determine move vs swap vs create
- `execute_move()/execute_swap()` - Perform git operations and messaging

**Dependencies**:

- `cli/core.py` - For repo discovery, ensuring work dir, path helpers
- Context ops: `git_ops` (list, add, checkout worktrees)
- Uses `subprocess.run` only for read-only `git status --porcelain`

**Usage**:

```bash
workstack move target-wt            # Move current worktree branch into target
workstack move --branch feature-x wt-new
workstack move --worktree wt-old wt-new --force
```

**Notes**: Tested via `tests/test_move.py` covering move, swap, and branch detection flows.

---

#### `cli/commands/tree.py`

**Purpose**: Implements `workstack tree` command.

**Responsibilities**:

- Display tree visualization of worktrees
- Show graphite stack relationships
- Hierarchical branch display

**Key Functions**:

- `tree_cmd()` - Main command handler

**Dependencies**:

- `cli/tree.py` - For `build_worktree_tree()`
- `cli/core.py` - For `discover_repo_context()`
- Context ops: `git_ops`, `global_config_ops`, `graphite_ops`

**Usage**:

```bash
workstack tree
```

---

#### `cli/commands/sync.py`

**Purpose**: Implements `workstack sync` command.

**Responsibilities**:

- Sync with graphite repository
- Identify merged PRs
- Suggest cleanup of merged worktrees
- Interactive removal prompts
- Generate directory change script when worktree deleted (via `--script` flag)

**Key Functions**:

- `sync_cmd()` - Main command handler with optional `--script` flag
- `_emit()` - Output messages to stdout or stderr based on script mode
- `_render_return_to_root_script()` - Generate cd script to return to root

**Shell Integration**: Supports `--script` flag for automatic directory change when current worktree is deleted during sync

**Dependencies**:

- `cli/core.py` - For `discover_repo_context()`
- Context ops: `git_ops`, `github_ops`, `graphite_ops`, `global_config_ops`

**Usage**:

```bash
workstack sync
workstack sync --yes  # auto-confirm removals
```

---

#### `cli/commands/init.py`

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

- `cli/core.py` - For `discover_repo_context()`, `ensure_work_dir()`
- `presets/` - For configuration templates
- Context ops: `global_config_ops`

**Usage**:

```bash
workstack init
workstack init --preset dagster
workstack init --shell-only
```

---

#### `cli/commands/config.py`

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

#### `cli/commands/gc.py`

**Purpose**: Implements `workstack gc` command (garbage collection).

**Responsibilities**:

- Identify worktrees with merged PRs
- Suggest safe-to-delete worktrees
- Display cleanup candidates

**Key Functions**:

- `gc_cmd()` - Main command handler

**Dependencies**:

- `cli/core.py` - For `discover_repo_context()`
- Context ops: `git_ops`, `github_ops`, `global_config_ops`

**Usage**:

```bash
workstack gc
```

**Note**: Non-destructive, only suggests deletions.

---

#### `cli/commands/completion.py`

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

- `cli/core.py` - For `discover_repo_context()`
- Context ops: `git_ops`, `global_config_ops`

**Usage**:

```bash
workstack completion bash > ~/.workstack-completion.bash
workstack completion zsh > ~/.workstack-completion.zsh
```

---

#### `cli/commands/shell_integration.py`

**Purpose**: Implements hidden `workstack __shell` command for shell integration.

**Responsibilities**:

- Unified entry point for shell wrapper scripts
- Routes commands to appropriate handlers with `--script` flag
- Emits passthrough marker for help/error cases
- Supports `switch`, `sync`, and `create` commands

**Key Functions**:

- `hidden_shell_cmd()` - Main hidden command handler
- Uses `handler.py` for routing logic

**Dependencies**:

- `cli/shell_integration/handler.py` - For `handle_shell_request()`

**Usage** (internal, called by shell wrappers):

```bash
workstack __shell switch my-feature
workstack __shell sync
workstack __shell create new-feature
```

**Note**: Hidden command (not in `--help`), used only by shell wrapper functions.

**Rationale**: Provides unified shell integration protocol, avoiding per-command hidden variants. See [Shell Integration Pattern](#shell-integration-pattern) for details.

---

#### `cli/commands/prepare_cwd_recovery.py`

**Purpose**: Implements hidden `workstack __prepare_cwd_recovery` command.

**Responsibilities**:

- Generate a one-time shell script that returns to repo root if cwd disappears
- Defensively handle races where `Path.cwd()` fails or directories vanish
- Emit script path (without newline) for wrapper consumption

**Key Functions**:

- `generate_recovery_script()` - Core helper performing guarded detection + script creation
- `prepare_cwd_recovery_cmd()` - Hidden Click command emitting the script path

**Dependencies**:

- `cli/core.py` - For `discover_repo_context()`
- `cli/shell_utils.py` - For `render_cd_script()` and `write_script_to_temp()`

**Usage**: Hidden helper invoked by shell wrappers before passthrough operations.

---

### Core Layer

#### `core/context.py`

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

#### `cli/core.py`

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

- `core/context.py` - For `WorkstackContext` type
- Uses ops through context parameter (no direct imports)

**Used By**: Nearly all commands

**Note**: Pure functions only, no side effects. All external interactions through context.

---

#### `cli/config.py`

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

**Used By**: `cli/commands/create.py`, `cli/commands/init.py`

---

#### `cli/tree.py`

**Purpose**: Tree visualization logic.

**Responsibilities**:

- Build tree structure from graphite stacks
- Format tree for display
- Handle complex branch relationships

**Key Functions**:

- `build_worktree_tree()` - Build tree structure from worktrees and stacks

**Dependencies**:

- `cli/graphite.py` - For stack loading

**Used By**: `cli/commands/tree.py`, `cli/commands/list.py`

**Note**: Complex logic, separate module for maintainability.

---

#### `cli/graphite.py`

**Purpose**: Graphite integration logic.

**Responsibilities**:

- Load graphite metadata from `.git/.graphite_cache/`
- Parse graphite stacks
- Extract branch parent relationships

**Key Functions**:

- `get_branch_stack(ctx, repo, branch)` - Get stack for specific branch
- `_load_graphite_cache()` - Load graphite metadata

**Dependencies**:

- `core/context.py` - For `WorkstackContext` type
- Uses `graphite_ops` through context

**Used By**: `cli/commands/list.py`, `cli/tree.py`

---

#### `cli/shell_integration/handler.py`

**Purpose**: Unified shell integration handler logic (Core Layer).

**Responsibilities**:

- Route shell wrapper requests to appropriate command handlers
- Add `--script` flag to commands for shell integration mode
- Determine when to passthrough vs. return script
- Handle help flags and error cases

**Key Types**:

```python
@dataclass(frozen=True)
class ShellIntegrationResult:
    passthrough: bool    # If true, shell wrapper calls regular command
    script: str | None   # Shell code to eval (cd commands, etc.)
    exit_code: int
```

**Key Functions**:

- `handle_shell_request(args)` - Main dispatcher for shell requests
  - Takes: Command args from shell wrapper
  - Returns: `ShellIntegrationResult` with passthrough decision and script
- `_invoke_hidden_command(command_name, args)` - Invoke command with `--script` flag
  - Detects help/error cases → passthrough
  - Otherwise runs command with `--script` → returns shell code

**Constants**:

- `PASSTHROUGH_MARKER: Final[str] = "__WORKSTACK_PASSTHROUGH__"` - Special marker that signals shell wrapper to call regular command instead of eval'ing output

**Dependencies**:

- `click.testing.CliRunner` - For invoking commands programmatically
- `cli/commands/create.py` - For `create` command with `--script`
- `cli/commands/switch.py` - For `switch_cmd` with `--script`
- `cli/commands/sync.py` - For `sync_cmd` with `--script`
- `core/context.py` - For `create_context()`

**Used By**: `cli/commands/shell_integration.py`

**Pattern**: Provides clean separation between shell integration logic and command logic. Commands only need to support `--script` flag; handler manages the routing and passthrough protocol.

**Example Flow**:

```
Shell wrapper → __shell switch my-feature
    ↓
handler.handle_shell_request(["switch", "my-feature"])
    ↓
_invoke_hidden_command("switch", ("my-feature",))
    ↓
CliRunner.invoke(switch_cmd, ["my-feature", "--script"])
    ↓
Returns ShellIntegrationResult(passthrough=False, script="cd ...; export ...", exit_code=0)
    ↓
Shell wrapper evals script
```

---

### Operations Layer

#### `core/gitops.py`

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

#### `core/github_ops.py`

**Purpose**: GitHub API operations.

**Interfaces/Classes**:

- `GitHubOps` (ABC) - 2 abstract methods
- `RealGitHubOps` - Production implementation using `gh` CLI

**Operations**:

- `get_prs_for_repo(repo_root)` - Fetch all PRs via `gh pr list --json`
- `get_pr_status(branch, prs)` - Get PR state, checks, reviews for branch

**Dependencies**: None (uses `gh` CLI via `subprocess`)

**Graceful Degradation**: Returns `None` if `gh` not available

**Used By**: `cli/commands/list.py`, `cli/commands/sync.py`, `cli/commands/gc.py`

---

#### `core/graphite_ops.py`

**Purpose**: Graphite CLI operations.

**Interfaces/Classes**:

- `GraphiteOps` (ABC) - 2 abstract methods
- `RealGraphiteOps` - Production implementation using `gt` CLI
- `DryRunGraphiteOps` - Dry-run wrapper

**Operations**:

- `get_graphite_url(repo_root)` - Construct graphite web URL
- `sync(repo_root)` - Run `gt repo sync`

**Dependencies**: None (uses `gt` CLI via `subprocess`)

**Used By**: `cli/commands/list.py`, `cli/commands/sync.py`

---

#### `core/global_config_ops.py`

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
3. Check `cli/core.py` if command uses core functions
4. Check relevant ops interface if interacting with git/github/graphite

**Example**: Modify how worktrees are listed

- Read: `cli/commands/list.py`
- Check: `cli/core.py` for `discover_repo_context()`
- Check: `core/gitops.py` for `list_worktrees()`

---

### "I want to add a new git operation"

1. Add abstract method to `GitOps` in `core/gitops.py`
2. Implement in `RealGitOps`
3. Implement in `FakeGitOps` (`tests/fakes/gitops.py`)
4. Add to `DryRunGitOps` if destructive operation

---

### "I want to add a new command"

1. Create new file in `commands/`
2. Follow pattern from existing commands (e.g., `cli/commands/rename.py` is simple)
3. Register in `cli/cli.py`
4. Add tests in `tests/commands/`

---

### "I want to understand configuration"

1. **Global config**: Read `core/global_config_ops.py`
   - Location: `~/.workstack/config.toml`
   - Keys: `workstacks_root`, `use_graphite`, `show_pr_info`
2. **Repo config**: Read `cli/config.py`
   - Location: `{work_dir}/config.toml`
   - Sections: `[env]`, `[[post_create]]`
3. **How configs are created**: See `cli/commands/init.py`
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

## Shell Integration Pattern

### Overview

Commands that need to modify the parent shell's environment (cd, export) cannot do so from a subprocess. The shell integration pattern solves this by having commands output shell code that the wrapper function evals.

### Components

1. **Shell Wrappers** (`cli/shell_integration/*.sh`, `*.fish`)
   - Intercept `workstack` commands in the user's shell
   - Call `workstack __shell <command> <args>`
   - Eval the output (unless passthrough marker detected)

2. **Hidden Command** (`cli/commands/shell_integration.py`)
   - Single entry point: `workstack __shell`
   - Routes to handler for processing

3. **Handler** (`cli/shell_integration/handler.py`)
   - Core routing logic
   - Invokes commands with `--script` flag
   - Returns `ShellIntegrationResult`

4. **Command Support** (commands with `--script` flag)
   - `switch` - Outputs cd + env activation
   - `sync` - Outputs cd to root if worktree deleted
   - `create` - Outputs cd to new worktree

### Protocol

**Normal Flow**:

```
User: workstack switch my-feature
  ↓
Wrapper: output=$(workstack __shell switch my-feature)
  ↓
Handler: Invokes switch_cmd --script
  ↓
switch_cmd: Outputs "cd /path/to/worktree; export ..."
  ↓
Wrapper: eval "$output"
  ↓
Result: User's shell is now in the worktree
```

**Passthrough Flow**:

```
User: workstack switch --help
  ↓
Wrapper: output=$(workstack __shell switch --help)
  ↓
Handler: Detects --help, returns PASSTHROUGH_MARKER
  ↓
Wrapper: Detects marker, calls regular command
  ↓
Calls: workstack switch --help
  ↓
Result: Normal help output displayed
```

### Adding Shell Integration to a New Command

```python
@click.command("my-command")
@click.option("--script", is_flag=True, hidden=True)
@click.pass_obj
def my_cmd(ctx: WorkstackContext, script: bool) -> None:
    # Do normal work
    result = do_something()

    if script:
        # Output shell code for wrapper to eval
        click.echo(f"cd {some_path}")
    else:
        # Normal user-facing output
        click.echo(f"Done! You can now run: cd {some_path}")
```

That's it! The handler will automatically route `workstack __shell my-command args` to your command with `--script`.

### Why This Pattern?

**Before** (per-command hidden variants):

```
commands/switch.py:
  - switch_cmd()
  - hidden_switch_cmd()  # Duplicate logic

commands/sync.py:
  - sync_cmd()
  - hidden_sync_cmd()  # Duplicate logic

commands/create.py:
  - create()
  - hidden_create_cmd()  # Duplicate logic
```

**After** (unified handler):

```
commands/switch.py:
  - switch_cmd(script: bool)  # Single function

commands/sync.py:
  - sync_cmd(script: bool)  # Single function

commands/create.py:
  - create(script: bool)  # Single function

cli/shell_integration/handler.py:
  - handle_shell_request()  # Single routing function
```

Benefits:

- Less code duplication
- Consistent behavior across commands
- Easier to add new shell-integrated commands
- Single source of truth for passthrough logic

---

## Related Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) - High-level system design
- [GLOSSARY.md](../GLOSSARY.md) - Terminology reference
- [FEATURE_INDEX.md](../FEATURE_INDEX.md) - Feature → file mapping
- [CLAUDE.md](../../CLAUDE.md) - Coding standards
