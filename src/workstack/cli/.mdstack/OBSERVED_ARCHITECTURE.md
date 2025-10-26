# Observed Architecture

## Overview

The `cli` package provides the command-line interface for workstack, a tool for managing git worktrees in a global worktrees directory. It is organized into two main layers:

1. **Top-level modules** (`cli.py`, `core.py`, `config.py`, `tree.py`, `graphite.py`, `activation.py`, `debug.py`, `shell_utils.py`) that provide shared utilities, data structures, and orchestration logic
2. **`commands/` subpackage** containing Click command implementations for user-facing workflows

The architecture emphasizes separation of concerns: core utilities handle data transformation and pure computation, while commands handle user interaction, validation, and orchestration. All commands receive a `WorkstackContext` dependency via Click's context object, providing access to git operations, GitHub operations, and configuration management.

## Module Organization

### cli.py
**Responsibility**: Main CLI entry point and command registration
**Key exports**: `cli` (Click group), `main()` (console script entry point)
**Key patterns**:
- Centralizes all command registration in one place
- Creates `WorkstackContext` on first invocation (allows test injection)
- Uses terse help flags (`-h`, `--help`)

### core.py
**Responsibility**: Repository context discovery and worktree path utilities
**Key exports**: `RepoContext` (dataclass), `discover_repo_context()`, `ensure_workstacks_dir()`, `worktree_path_for()`, `validate_worktree_name_for_removal()`
**Key patterns**:
- Pure functions for path resolution and validation
- Handles git worktree edge cases (finding common git directory)
- Defensive validation with clear error messages

### config.py
**Responsibility**: Configuration file loading and parsing
**Key exports**: `LoadedConfig` (frozen dataclass), `load_config()`
**Key patterns**:
- Reads `.workstack/config.toml` with sensible defaults
- Supports environment variables, post-create commands, and shell selection
- Immutable configuration objects

### tree.py
**Responsibility**: Tree visualization for worktrees and Graphite dependencies
**Key exports**: `TreeNode`, `WorktreeMapping`, `BranchGraph`, `build_workstack_tree()`, `render_tree()`
**Key patterns**:
- Pure data structures (frozen dataclasses) for tree representation
- Orchestration function (`build_workstack_tree()`) that coordinates multi-step process
- Filtering logic to show only branches with active worktrees
- Unicode box-drawing characters for ASCII art rendering
- Requires Graphite cache (hard fail if missing)

### graphite.py
**Responsibility**: Graphite integration for reading branch relationships and stack information
**Key exports**: `BranchInfo` (TypedDict), `get_branch_stack()`, `get_parent_branch()`, `get_child_branches()`, `find_worktrees_containing_branch()`, `find_worktree_for_branch()`
**Key patterns**:
- Reads `.git/.graphite_cache_persist` JSON file
- Builds parent-child relationship graphs from cache data
- Linear stack extraction (traverses up to trunk, then down following first child)
- Graceful degradation: returns None if cache doesn't exist
- Handles git worktree common directory correctly

### activation.py
**Responsibility**: Shell activation script generation for worktree environments
**Key exports**: `render_activation_script()`
**Key patterns**:
- Pure function generating shell code
- Creates virtual environment with `uv sync` if needed
- Loads `.env` files with `set -a` / `set +a` for environment variable export
- Works in bash and zsh

### debug.py
**Responsibility**: Debug logging utilities
**Key exports**: `is_debug()`, `debug_log()`
**Key patterns**:
- Controlled by `WORKSTACK_DEBUG=1` environment variable
- Logs to `/tmp/workstack-debug.log` with timestamps
- No-op if debug mode disabled

### shell_utils.py
**Responsibility**: Shell script generation and temporary file management
**Key exports**: `render_cd_script()`, `write_script_to_temp()`, `cleanup_stale_scripts()`
**Key patterns**:
- Generates shell scripts with proper quoting and metadata headers
- Writes to temp directory with UUID-based filenames
- Automatic cleanup of stale scripts (default 1 hour)
- Debug logging for troubleshooting

## Subpackages

### commands/
Contains Click command implementations for all user-facing workflows. Each module represents a distinct command or command group. See `.mdstack/OBSERVED_ARCHITECTURE.md` in the commands package for detailed architecture of individual commands.

**Key organizational principles**:
- One command per module (or command group)
- Shared navigation logic in `switch.py` (used by `up.py`, `down.py`)
- Shared worktree removal logic in `remove.py` (used by `sync.py`)
- Consistent error handling and user messaging
- Script mode support for shell integration across multiple commands

### shell_integration/
Contains shell integration handler logic (see `handler.py`). Provides unified entry point for shell wrapper coordination.

## Core Abstractions

### TreeNode
**Location**: tree.py
**Purpose**: Represents a single node in the worktree tree hierarchy
**Type**: Frozen dataclass
**Fields**:
- `branch_name`: Git branch name
- `worktree_name`: Worktree directory name (or "root")
- `children`: List of child TreeNode objects
- `is_current`: True if this is the current working directory
**Key insight**: Immutable structure enables pure tree rendering functions

### WorktreeMapping
**Location**: tree.py
**Purpose**: Encapsulates all mappings between branches, worktrees, and filesystem paths
**Type**: Frozen dataclass
**Fields**:
- `branch_to_worktree`: Map of branch name → worktree name
- `worktree_to_path`: Map of worktree name → filesystem path
- `current_worktree`: Name of current worktree (None if not in a worktree)
**Key insight**: Centralizes worktree discovery logic; used by tree building and rendering

### BranchGraph
**Location**: tree.py
**Purpose**: Represents branch relationships from Graphite cache
**Type**: Frozen dataclass
**Fields**:
- `parent_of`: Map of branch name → parent branch name
- `children_of`: Map of branch name → list of child branch names
- `trunk_branches`: List of trunk branch names
**Key insight**: Filtered version used for tree building contains only branches with active worktrees

### BranchInfo
**Location**: graphite.py
**Purpose**: Metadata for a single branch in the Graphite stack
**Type**: TypedDict
**Fields**:
- `parent`: Parent branch name or None
- `children`: List of child branch names
- `is_trunk`: True if this is a trunk branch
**Key insight**: Extracted from Graphite cache; used for stack traversal

### LoadedConfig
**Location**: config.py
**Purpose**: In-memory representation of `.workstack/config.toml`
**Type**: Frozen dataclass
**Fields**:
- `env`: Dictionary of environment variables
- `post_create_commands`: List of shell commands to run after worktree creation
- `post_create_shell`: Shell to use for post-create commands (bash, zsh, etc.)
**Key insight**: Immutable; loaded once and passed through context

### RepoContext
**Location**: core.py
**Purpose**: Encapsulates repository root and workstacks directory information
**Type**: Frozen dataclass
**Fields**:
- `root`: Path to repository root
- `repo_name`: Repository name (derived from root directory name)
- `workstacks_dir`: Path to global workstacks directory for this repo
**Key insight**: Discovered once per command invocation; used for path resolution

## Critical Functions

### build_workstack_tree
**Location**: tree.py
**Purpose**: Main orchestration function that builds tree structure of branches with active worktrees
**Signature**: `build_workstack_tree(ctx: WorkstackContext, repo_root: Path) -> list[TreeNode]`
**Algorithm**:
1. Get all worktrees and their branches from git
2. Load Graphite cache for parent-child relationships (required)
3. Build branch graph from cache data
4. Filter graph to only branches that have worktrees
5. Build tree starting from trunk branches
6. Return list of root nodes
**Key insight**: Requires Graphite cache; hard fails if missing with clear error message

### render_tree
**Location**: tree.py
**Purpose**: Renders tree structure as ASCII art with Unicode box-drawing characters
**Signature**: `render_tree(roots: list[TreeNode]) -> str`
**Output format**:
- `├─` for middle children (branch continues below)
- `└─` for last child (no more branches below)
- `│` for continuation lines (vertical connection)
- Current worktree highlighted in bright green
- Worktree names shown in dimmed annotation `[@name]`
**Key insight**: Pure function; no I/O or side effects

### _get_worktree_mapping
**Location**: tree.py
**Purpose**: Gets mapping of branches to worktrees from git
**Signature**: `_get_worktree_mapping(ctx: WorkstackContext, repo_root: Path) -> WorktreeMapping`
**Key logic**:
- Queries git for all worktrees
- Skips worktrees with detached HEAD
- Detects current worktree by checking if cwd is within worktree path
- Handles "root" worktree specially (main repo directory)
**Key insight**: Handles subdirectory detection correctly (cwd can be anywhere within worktree)

### _load_graphite_branch_graph
**Location**: tree.py
**Purpose**: Loads branch graph from Graphite cache file
**Signature**: `_load_graphite_branch_graph(ctx: WorkstackContext, repo_root: Path) -> BranchGraph | None`
**Returns**: BranchGraph if cache exists and is valid, None otherwise
**Key logic**:
- Uses `git rev-parse --git-common-dir` to find shared git directory
- Reads `.git/.graphite_cache_persist` JSON file
- Extracts parent-child relationships and trunk branches
**Key insight**: Graceful degradation; returns None if cache missing (allows other operations to continue)

### _filter_graph_to_active_branches
**Location**: tree.py
**Purpose**: Filters branch graph to only include branches with active worktrees
**Signature**: `_filter_graph_to_active_branches(graph: BranchGraph, active_branches: set[str]) -> BranchGraph`
**Key logic**:
- Removes branches without worktrees from graph
- Preserves tree structure for remaining branches
- Filters children lists to only active branches
**Key insight**: Pure function; enables clean separation between data loading and filtering

### _build_tree_from_graph
**Location**: tree.py
**Purpose**: Builds TreeNode structure from filtered branch graph
**Signature**: `_build_tree_from_graph(graph: BranchGraph, mapping: WorktreeMapping) -> list[TreeNode]`
**Key logic**:
- Recursively builds tree nodes starting from trunk branches
- Follows parent-child relationships to create full tree structure
- Annotates nodes with current worktree information
**Key insight**: Recursive structure mirrors tree hierarchy; enables clean rendering

### get_branch_stack
**Location**: graphite.py
**Purpose**: Gets the linear Graphite stack for a given branch
**Signature**: `get_branch_stack(ctx: WorkstackContext, repo_root: Path, branch: str) -> list[str] | None`
**Returns**: List of branch names from trunk to leaf, or None if cache missing or branch not tracked
**Algorithm**:
1. Load branch info from Graphite cache
2. Traverse DOWN to trunk (collecting ancestors)
3. Traverse UP following first child (collecting descendants)
4. Combine into linear chain
**Key insight**: Returns linear chain even if full graph has branching; follows first child only

### discover_repo_context
**Location**: core.py
**Purpose**: Walks up from start path to find repository root and workstacks directory
**Signature**: `discover_repo_context(ctx: WorkstackContext, start: Path) -> RepoContext`
**Returns**: RepoContext with repo root and workstacks directory
**Raises**: FileNotFoundError if not in a git repo or if global config missing
**Key logic**:
- Uses `git rev-parse --git-common-dir` to handle worktrees correctly
- Falls back to walking up directory tree looking for `.git`
- Derives workstacks directory from global config
**Key insight**: Handles git worktree edge case where `.git` is a file, not directory

### load_config
**Location**: config.py
**Purpose**: Loads configuration from `.workstack/config.toml`
**Signature**: `load_config(config_dir: Path) -> LoadedConfig`
**Returns**: LoadedConfig with defaults if file doesn't exist
**Key logic**:
- Parses TOML format
- Extracts `[env]` section for environment variables
- Extracts `[post_create]` section for commands and shell
- Type-converts all values to strings
**Key insight**: Graceful degradation; returns empty config if file missing

### render_activation_script
**Location**: activation.py
**Purpose**: Generates shell script that activates worktree environment
**Signature**: `render_activation_script(*, worktree_path: Path, final_message: str = ..., comment: str = ...) -> str`
**Returns**: Shell script as string with newlines
**Script behavior**:
- Changes directory to worktree
- Creates `.venv` with `uv sync` if not present
- Sources `.venv/bin/activate` if present
- Exports variables from `.env` if present
- Runs final message command
**Key insight**: Pure function; works in bash and zsh

### write_script_to_temp
**Location**: shell_utils.py
**Purpose**: Writes shell script to temp file with unique UUID
**Signature**: `write_script_to_temp(script_content: str, *, command_name: str, comment: str | None = None) -> Path`
**Returns**: Path to temp file
**Filename format**: `workstack-{command}-{uuid}.sh`
**Key logic**:
- Adds metadata header with timestamp, UUID, user, working directory
- Makes file executable
- Logs to debug log if enabled
**Key insight**: UUID-based naming prevents collisions; metadata aids debugging

## Architectural Patterns

### Pure Functions with Immutable Data Structures
**Used in**: tree.py, graphite.py, core.py, config.py, activation.py, shell_utils.py
**Purpose**: Enables testability and reasoning about code behavior
**Implementation**:
- Frozen dataclasses for all data structures
- Functions that don't modify input or have side effects
- Clear separation between data loading and transformation
**Example**: `_filter_graph_to_active_branches()` takes graph and returns new filtered graph without modifying input

### Graceful Degradation
**Used in**: graphite.py, tree.py, core.py
**Purpose**: Allows operations to continue when optional dependencies (like Graphite) are missing
**Implementation**:
- Functions return None when optional data unavailable
- Callers check for None and handle appropriately
- Hard failures only when data is truly required
**Example**: `_load_graphite_branch_graph()` returns None if cache missing; `build_workstack_tree()` hard fails because tree requires Graphite

### Orchestration Pattern
**Used in**: tree.py, commands (see child package docs)
**Purpose**: Coordinates multi-step workflows with clear separation of concerns
**Implementation**:
- High-level function calls sequence of lower-level functions
- Each step has clear input/output contract
- Errors propagate up for centralized handling
**Example**: `build_workstack_tree()` orchestrates: get worktrees → load cache → build graph → filter → build tree

### Dependency Injection via Context
**Used in**: All commands, tree.py, graphite.py, core.py
**Purpose**: Provides access to git operations, GitHub operations, and configuration without tight coupling
**Implementation**:
- `WorkstackContext` passed through function parameters
- Commands receive context via Click's `@click.pass_obj`
- Enables test injection of mock context
**Example**: `build_workstack_tree(ctx: WorkstackContext, repo_root: Path)` receives context for git operations

### Script