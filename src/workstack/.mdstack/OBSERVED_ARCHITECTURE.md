# Observed Architecture

## Overview

The `workstack` package is a Click-based CLI tool for managing git worktrees in a global worktrees directory. It is organized into three main layers:

1. **Entry point modules** (`__init__.py`, `__main__.py`) that provide console script and module execution support
2. **Core package** (`core/`) providing foundational abstractions for git operations, GitHub API interactions, Graphite integration, and configuration management
3. **CLI package** (`cli/`) providing the command-line interface with shared utilities and command implementations
4. **Status package** (`status/`) providing comprehensive status collection and rendering for worktrees

The architecture emphasizes separation of concerns through dependency injection: all operational dependencies (git, GitHub, Graphite, config) are abstracted behind interfaces in the `core` package, enabling testability, dry-run mode support, and clean separation between business logic and system interactions.

## Module Organization

### __init__.py
**Responsibility**: Package entry point for console script execution
**Key exports**: `main()` function
**Key patterns**:
- Imports and delegates to `cli.cli` module
- Provides entry point for `workstack` console script defined in setup.py

### __main__.py
**Responsibility**: Enables module execution via `python -m workstack`
**Key patterns**:
- Imports and calls `main()` from package
- Standard Python module execution pattern

## Subpackages

### core/
**Purpose**: Foundational abstraction layer for all external system interactions
**Organization**: Abstract interfaces with multiple implementations (real, dry-run)
**Key modules**:
- `gitops.py` - Git operations (worktree management, branch operations)
- `github_ops.py` - GitHub API interactions via gh CLI
- `graphite_ops.py` - Graphite CLI operations and cache parsing
- `global_config_ops.py` - Global configuration file management
- `shell_ops.py` - Shell detection and tool availability
- `context.py` - Dependency injection container
- `branch_metadata.py` - Branch metadata data structures
- `file_utils.py` - File operation utilities

**Key architectural principle**: Three-implementation pattern for each operational domain:
1. Abstract base class (ABC) defining the interface
2. Real implementation using subprocess/file I/O
3. Dry-run wrapper for preview mode

### cli/
**Purpose**: Command-line interface and user-facing workflows
**Organization**: Top-level utilities and `commands/` subpackage
**Key modules**:
- `cli.py` - Main CLI entry point and command registration
- `core.py` - Repository context discovery and worktree path utilities
- `config.py` - Configuration file loading and parsing
- `tree.py` - Tree visualization for worktrees and Graphite dependencies
- `graphite.py` - Graphite integration for branch relationships
- `activation.py` - Shell activation script generation
- `debug.py` - Debug logging utilities
- `shell_utils.py` - Shell script generation and temp file management

**Key architectural principle**: Pure functions with immutable data structures for testability and reasoning

### status/
**Purpose**: Comprehensive status collection and rendering system for worktrees
**Organization**: Orchestrator coordinating parallel collectors with graceful degradation
**Key modules**:
- `orchestrator.py` - Central coordinator for parallel status collection
- `__init__.py` - Package initialization and public API

**Key architectural principle**: Plugin-based collector architecture with error boundaries for graceful degradation

## Core Abstractions

### WorkstackContext (Dependency Container)
**Location**: core/context.py
**Purpose**: Immutable container holding all operational dependencies for the application
**Type**: Frozen dataclass with 6 fields
**Fields**: `git_ops`, `global_config_ops`, `github_ops`, `graphite_ops`, `shell_ops`, `dry_run`
**Key insight**: Created once at CLI entry point via `create_context()`, threaded through application to enable dependency injection and testability

### GitOps (Abstract Base Class)
**Location**: core/gitops.py
**Purpose**: Defines complete interface for git operations. All git interactions go through this abstraction.
**Type**: ABC with 15 abstract methods
**Key methods**:
- Worktree operations: `list_worktrees`, `add_worktree`, `move_worktree`, `remove_worktree`, `prune_worktrees`
- Branch operations: `checkout_branch`, `delete_branch_with_graphite`, `is_branch_checked_out`
- Query operations: `get_current_branch`, `get_branch_head`, `get_commit_message`
- Status operations: `has_staged_changes`, `get_file_status`, `get_ahead_behind`

### RealGitOps (Production Implementation)
**Location**: core/gitops.py
**Purpose**: Executes actual git commands via subprocess
**Type**: Concrete class implementing GitOps
**Key pattern**: Subprocess calls with `check=True` for error handling, `capture_output=True` for output capture

### DryRunGitOps (Dry-Run Wrapper)
**Location**: core/gitops.py
**Purpose**: Intercepts destructive operations to print dry-run messages instead of executing
**Type**: Decorator pattern wrapping any GitOps implementation
**Destructive operations**: `add_worktree`, `move_worktree`, `remove_worktree`, `delete_branch_with_graphite`, `prune_worktrees`

### GraphiteOps (Abstract Base Class)
**Location**: core/graphite_ops.py
**Purpose**: Defines interface for Graphite CLI operations and cache reading
**Type**: ABC with 5 abstract methods
**Key methods**:
- `get_graphite_url()` - Construct Graphite URL from GitHub PR info
- `sync()` - Run gt sync with optional force flag
- `get_prs_from_graphite()` - Read .graphite_pr_info cache
- `get_all_branches()` - Read .graphite_cache_persist and enrich with git data
- `get_branch_stack()` - Build linear stack of branches from trunk to leaf

### RealGraphiteOps (Production Implementation)
**Location**: core/graphite_ops.py
**Purpose**: Executes gt CLI commands and reads Graphite cache files
**Type**: Concrete class implementing GraphiteOps
**Key pattern**: Reads JSON files from .git directory, parses with helper functions, enriches with git branch heads

### GitHubOps (Abstract Base Class)
**Location**: core/github_ops.py
**Purpose**: Defines interface for GitHub API interactions via gh CLI
**Type**: ABC with 2 abstract methods
**Key methods**:
- `get_prs_for_repo()` - Fetch all PRs with optional CI check status
- `get_pr_status()` - Query PR status for specific branch

### RealGitHubOps (Production Implementation)
**Location**: core/github_ops.py
**Purpose**: Executes gh CLI commands and parses JSON output
**Type**: Concrete class implementing GitHubOps
**Key pattern**: Uses try/except to handle gh CLI unavailability gracefully, returns empty dict on failure

### GlobalConfigOps (Abstract Base Class)
**Location**: core/global_config_ops.py
**Purpose**: Defines interface for global configuration file management (~/.workstack/config.toml)
**Type**: ABC with 7 abstract methods
**Key methods**:
- Getters: `get_workstacks_root()`, `get_use_graphite()`, `get_shell_setup_complete()`, `get_show_pr_info()`, `get_show_pr_checks()`
- `set()` - Update config with sentinel pattern for optional fields
- `exists()`, `get_path()` - Utility methods

### RealGlobalConfigOps (Production Implementation)
**Location**: core/global_config_ops.py
**Purpose**: Manages ~/.workstack/config.toml with lazy-loaded caching
**Type**: Concrete class implementing GlobalConfigOps
**Key pattern**: Lazy-loaded cache invalidated on writes, creates parent directories as needed

### RepoContext (Data Structure)
**Location**: cli/core.py
**Purpose**: Encapsulates repository root and workstacks directory information
**Type**: Frozen dataclass with 3 fields
**Fields**: `root` (Path), `repo_name` (str), `workstacks_dir` (Path)
**Key insight**: Discovered once per command invocation; used for path resolution throughout CLI

### LoadedConfig (Data Structure)
**Location**: cli/config.py
**Purpose**: In-memory representation of `.workstack/config.toml`
**Type**: Frozen dataclass with 3 fields
**Fields**: `env` (dict), `post_create_commands` (list), `post_create_shell` (str)
**Key insight**: Immutable; loaded once and passed through context

### TreeNode (Data Structure)
**Location**: cli/tree.py
**Purpose**: Represents a single node in the worktree tree hierarchy
**Type**: Frozen dataclass with 4 fields
**Fields**: `branch_name`, `worktree_name`, `children` (list), `is_current` (bool)
**Key insight**: Immutable structure enables pure tree rendering functions

### WorktreeMapping (Data Structure)
**Location**: cli/tree.py
**Purpose**: Encapsulates all mappings between branches, worktrees, and filesystem paths
**Type**: Frozen dataclass with 3 fields
**Fields**: `branch_to_worktree`, `worktree_to_path`, `current_worktree`
**Key insight**: Centralizes worktree discovery logic; used by tree building and rendering

### BranchGraph (Data Structure)
**Location**: cli/tree.py
**Purpose**: Represents branch relationships from Graphite cache
**Type**: Frozen dataclass with 3 fields
**Fields**: `parent_of`, `children_of`, `trunk_branches`
**Key insight**: Filtered version used for tree building contains only branches with active worktrees

### StatusOrchestrator (Orchestration)
**Location**: status/orchestrator.py
**Purpose**: Central coordinator that manages the status collection pipeline
**Type**: Concrete class
**Key methods**:
- `collect_status(ctx, worktree_path, repo_root)` - Main entry point orchestrating collection and assembly
- `_get_worktree_info()` - Determines basic worktree metadata
- `_get_related_worktrees()` - Identifies other worktrees in the repository

**Design characteristics**:
- Accepts list of `StatusCollector` instances at initialization
- Configurable timeout per collector (default 2.0 seconds)
- Uses ThreadPoolExecutor for parallel collection
- Implements graceful degradation through exception handling

### StatusData (Data Structure)
**Location**: status/models/status_data.py
**Purpose**: Root container aggregating all status information for a worktree
**Type**: Frozen dataclass with 8 fields
**Fields**: `worktree_info` (required), `git_status`, `stack_position`, `pr_status`, `environment`, `dependencies`, `plan`, `related_worktrees` (optional)
**Key insight**: Optional fields enable partial status collection when data sources unavailable

## Critical Functions

### create_context
**Location**: core/context.py
**Purpose**: Factory function that creates WorkstackContext with real or dry-run implementations
**Signature**: `create_context(dry_run: bool = False) -> WorkstackContext`
**Key logic**: Creates real implementations, wraps with dry-run wrappers if dry_run=True, returns assembled context
**Key insight**: Single point of dependency assembly; enables test injection by replacing this function

### discover_repo_context
**Location**: cli/core.py
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
**Location**: cli/config.py
**Purpose**: Loads configuration from `.workstack/config.toml`
**Signature**: `load_config(config_dir: Path) -> LoadedConfig`
**Returns**: LoadedConfig with defaults if file doesn't exist
**Key logic**:
- Parses TOML format
- Extracts `[env]` section for environment variables
- Extracts `[post_create]` section for commands and shell
- Type-converts all values to strings
**Key insight**: Graceful degradation; returns empty config if file missing

### build_workstack_tree
**Location**: cli/tree.py
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
**Location**: cli/tree.py
**Purpose**: Renders tree structure as ASCII art with Unicode box-drawing characters
**Signature**: `render_tree(roots: list[TreeNode]) -> str`
**Output format**:
- `├─` for middle children (branch continues below)
- `└─` for last child (no more branches below)
- `│` for continuation lines (vertical connection)
- Current worktree highlighted in bright green
- Worktree names shown in dimmed annotation `[@name]`
**Key insight**: Pure function; no I/O or side effects

### get_branch_stack
**Location**: cli/graphite.py
**Purpose**: Gets the linear Graphite stack for a given branch
**Signature**: `get_branch_stack(ctx: WorkstackContext, repo_root: Path, branch: str) -> list[str] | None`
**Returns**: List of branch names from trunk to leaf, or None if cache missing or branch not tracked
**Algorithm**:
1. Load branch info from Graphite cache
2. Traverse DOWN to trunk (collecting ancestors)
3. Traverse UP following first child (collecting descendants)
4. Combine into linear chain
**Key insight**: Returns linear chain even if full graph has branching; follows first child only

### render_activation_script
**Location**: cli/activation.py
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
**Location**: cli/shell_utils.py
**Purpose**: Writes shell script to temp file with unique UUID
**Signature**: `write_script_to_temp(script_content: str, *, command_name: str, comment: str | None = None) -> Path`
**Returns**: Path to temp file
**Filename format**: `workstack-{command}-{uuid}.sh`
**Key logic**:
- Adds metadata header with timestamp, UUID, user, working directory
- Makes file executable
- Logs to debug log if enabled
**Key insight**: UUID-based naming prevents collisions; metadata aids debugging

### parse_graphite_pr_info
**Location**: core/graphite_ops.py
**Purpose**: Parse Graphite's .graphite_pr_info JSON into PullRequestInfo objects
**Key logic**: Iterates through prInfos array, extracts branch name and PR data, converts Graphite URL format to GitHub format

### parse_graphite_cache
**Location**: core/graphite_ops.py
**Purpose**: Parse Graphite's .graphite_cache_persist JSON into BranchMetadata objects
**Key logic**: Extracts