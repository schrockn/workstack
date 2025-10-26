# Observed Architecture

## Overview

The `core` package provides the foundational abstraction layer for workstack operations. It implements a dependency injection pattern with abstract interfaces and multiple implementations (real, dry-run, and test-friendly variants) for all external system interactions. This architecture enables testability, dry-run mode support, and clean separation between business logic and system dependencies.

The package is organized around four primary operational domains: git operations, GitHub API interactions, Graphite CLI integration, and global configuration management. Each domain follows the same architectural pattern: an abstract base class defining the interface, a production implementation using subprocess/file I/O, and a dry-run wrapper for preview mode.

## Module Organization

### gitops.py
**Responsibility**: Abstract interface and implementations for git operations (worktree management, branch operations, commit inspection)
**Key exports**: 
- `GitOps` (ABC) - Abstract interface for all git operations
- `RealGitOps` - Production implementation using subprocess
- `DryRunGitOps` - Dry-run wrapper that prints intended actions
- `WorktreeInfo` - Dataclass for worktree metadata

### github_ops.py
**Responsibility**: Abstract interface and implementations for GitHub API interactions via gh CLI
**Key exports**:
- `GitHubOps` (ABC) - Abstract interface for GitHub operations
- `RealGitHubOps` - Production implementation using gh CLI
- `DryRunGitHubOps` - Dry-run wrapper
- `PullRequestInfo` - Dataclass for PR metadata
- Helper functions: `parse_github_pr_list`, `parse_github_pr_status`, `_parse_github_pr_url`

### graphite_ops.py
**Responsibility**: Abstract interface and implementations for Graphite CLI operations and cache parsing
**Key exports**:
- `GraphiteOps` (ABC) - Abstract interface for Graphite operations
- `RealGraphiteOps` - Production implementation using gt CLI
- `DryRunGraphiteOps` - Dry-run wrapper
- Helper functions: `parse_graphite_pr_info`, `parse_graphite_cache`, `read_graphite_json_file`

### global_config_ops.py
**Responsibility**: Abstract interface and implementations for global configuration file management (~/.workstack/config.toml)
**Key exports**:
- `GlobalConfigOps` (ABC) - Abstract interface for config operations
- `RealGlobalConfigOps` - Production implementation with lazy-loaded caching
- `DryRunGlobalConfigOps` - Dry-run wrapper
- `_UNCHANGED` - Sentinel value for optional config updates

### context.py
**Responsibility**: Dependency injection container that assembles all operational dependencies
**Key exports**:
- `WorkstackContext` - Frozen dataclass holding all dependencies
- `create_context()` - Factory function that creates context with real or dry-run implementations

### branch_metadata.py
**Responsibility**: Data structure for Graphite branch metadata
**Key exports**:
- `BranchMetadata` - Frozen dataclass representing a gt-tracked branch

### shell_ops.py
**Responsibility**: Abstract interface for shell detection and tool availability checks
**Key exports**:
- `ShellOps` (ABC) - Abstract interface for shell operations
- `RealShellOps` - Production implementation using environment and PATH
- `detect_shell_from_env()` - Helper function for shell detection

### file_utils.py
**Responsibility**: File operation utilities for markdown parsing
**Key exports**:
- `extract_plan_title()` - Extract first heading from markdown plan files

### __init__.py
**Responsibility**: Package initialization (empty)

## Core Abstractions

### GitOps (Abstract Base Class)
**Location**: gitops.py
**Purpose**: Defines the complete interface for git operations. All git interactions in the codebase go through this abstraction, enabling testability and dry-run mode.
**Type**: ABC with 15 abstract methods
**Key methods**:
- Worktree operations: `list_worktrees`, `add_worktree`, `move_worktree`, `remove_worktree`, `prune_worktrees`
- Branch operations: `checkout_branch`, `checkout_detached`, `delete_branch_with_graphite`, `is_branch_checked_out`
- Query operations: `get_current_branch`, `detect_default_branch`, `get_git_common_dir`, `get_branch_head`, `get_commit_message`
- Status operations: `has_staged_changes`, `get_file_status`, `get_ahead_behind`, `get_recent_commits`

### RealGitOps (Production Implementation)
**Location**: gitops.py
**Purpose**: Executes actual git commands via subprocess. All operations use `subprocess.run()` with appropriate flags and error handling.
**Type**: Concrete class implementing GitOps
**Key pattern**: Subprocess calls with `check=True` for error handling, `capture_output=True` for output capture

### DryRunGitOps (Dry-Run Wrapper)
**Location**: gitops.py
**Purpose**: Wraps a GitOps implementation and intercepts destructive operations to print dry-run messages instead of executing them. Read-only operations delegate to wrapped implementation.
**Type**: Decorator pattern - wraps any GitOps implementation
**Destructive operations**: `add_worktree`, `move_worktree`, `remove_worktree`, `delete_branch_with_graphite`, `prune_worktrees`

### GraphiteOps (Abstract Base Class)
**Location**: graphite_ops.py
**Purpose**: Defines interface for Graphite CLI operations and cache reading. Abstracts both CLI execution and JSON cache parsing.
**Type**: ABC with 5 abstract methods
**Key methods**:
- `get_graphite_url()` - Construct Graphite URL from GitHub PR info
- `sync()` - Run gt sync with optional force flag
- `get_prs_from_graphite()` - Read .graphite_pr_info cache
- `get_all_branches()` - Read .graphite_cache_persist and enrich with git data
- `get_branch_stack()` - Build linear stack of branches from trunk to leaf

### RealGraphiteOps (Production Implementation)
**Location**: graphite_ops.py
**Purpose**: Executes gt CLI commands and reads Graphite cache files. Parses JSON caches and enriches with git metadata.
**Type**: Concrete class implementing GraphiteOps
**Key pattern**: Reads JSON files from .git directory, parses with helper functions, enriches with git branch heads

### DryRunGraphiteOps (Dry-Run Wrapper)
**Location**: graphite_ops.py
**Purpose**: Wraps GraphiteOps and intercepts destructive operations. Currently only `sync()` is destructive.
**Type**: Decorator pattern
**Destructive operations**: `sync()`

### GitHubOps (Abstract Base Class)
**Location**: github_ops.py
**Purpose**: Defines interface for GitHub API interactions via gh CLI. Currently read-only operations.
**Type**: ABC with 2 abstract methods
**Key methods**:
- `get_prs_for_repo()` - Fetch all PRs with optional CI check status
- `get_pr_status()` - Query PR status for specific branch

### RealGitHubOps (Production Implementation)
**Location**: github_ops.py
**Purpose**: Executes gh CLI commands and parses JSON output. Handles authentication and availability gracefully.
**Type**: Concrete class implementing GitHubOps
**Key pattern**: Uses try/except to handle gh CLI unavailability, returns empty dict on failure

### DryRunGitHubOps (Dry-Run Wrapper)
**Location**: github_ops.py
**Purpose**: Wraps GitHubOps. Currently delegates all operations since GitHubOps is read-only.
**Type**: Decorator pattern
**Note**: Included for consistency and future write operations

### GlobalConfigOps (Abstract Base Class)
**Location**: global_config_ops.py
**Purpose**: Defines interface for global configuration file management. Uses sentinel pattern for optional updates.
**Type**: ABC with 7 abstract methods
**Key methods**:
- Getters: `get_workstacks_root()`, `get_use_graphite()`, `get_shell_setup_complete()`, `get_show_pr_info()`, `get_show_pr_checks()`
- `set()` - Update config with sentinel pattern for optional fields
- `exists()`, `get_path()` - Utility methods

### RealGlobalConfigOps (Production Implementation)
**Location**: global_config_ops.py
**Purpose**: Manages ~/.workstack/config.toml with lazy-loaded caching. Handles file creation and TOML parsing.
**Type**: Concrete class implementing GlobalConfigOps
**Key pattern**: Lazy-loaded cache invalidated on writes, creates parent directories as needed

### DryRunGlobalConfigOps (Dry-Run Wrapper)
**Location**: global_config_ops.py
**Purpose**: Wraps GlobalConfigOps and prints dry-run messages for write operations.
**Type**: Decorator pattern
**Destructive operations**: `set()`

### ShellOps (Abstract Base Class)
**Location**: shell_ops.py
**Purpose**: Defines interface for shell detection and tool availability checks. Enables dependency injection for testing.
**Type**: ABC with 2 abstract methods
**Key methods**:
- `detect_shell()` - Detect current shell and RC file path
- `get_installed_tool_path()` - Check if tool is in PATH

### RealShellOps (Production Implementation)
**Location**: shell_ops.py
**Purpose**: Detects shell from SHELL environment variable and checks tool availability via shutil.which().
**Type**: Concrete class implementing ShellOps

### PullRequestInfo (Data Class)
**Location**: github_ops.py
**Purpose**: Immutable container for GitHub PR metadata
**Type**: Frozen dataclass with 7 fields
**Fields**: `number`, `state`, `url`, `is_draft`, `checks_passing`, `owner`, `repo`

### BranchMetadata (Data Class)
**Location**: branch_metadata.py
**Purpose**: Immutable container for Graphite branch metadata
**Type**: Frozen dataclass with 5 fields
**Fields**: `name`, `parent`, `children`, `is_trunk`, `commit_sha`

### WorktreeInfo (Data Class)
**Location**: gitops.py
**Purpose**: Immutable container for git worktree metadata
**Type**: Frozen dataclass with 2 fields
**Fields**: `path`, `branch`

### WorkstackContext (Dependency Container)
**Location**: context.py
**Purpose**: Immutable container holding all operational dependencies for the application
**Type**: Frozen dataclass with 6 fields
**Fields**: `git_ops`, `global_config_ops`, `github_ops`, `graphite_ops`, `shell_ops`, `dry_run`

## Architectural Patterns

### Three-Implementation Pattern
Every operational domain follows the same pattern:
1. **Abstract Base Class (ABC)** - Defines the interface with `@abstractmethod` decorators
2. **Real Implementation** - Executes actual operations via subprocess or file I/O
3. **Dry-Run Wrapper** - Decorator that intercepts destructive operations and prints intentions

This pattern enables:
- Testability through mock implementations
- Dry-run mode without code duplication
- Clear separation of concerns
- Easy addition of new implementations (e.g., logging wrapper)

### Dependency Injection via Context
The `WorkstackContext` dataclass serves as the dependency container. Created once at CLI entry point via `create_context()`, it's threaded through the application. The `dry_run` flag controls whether real or dry-run implementations are used.

### Sentinel Pattern for Optional Updates
`GlobalConfigOps.set()` uses the `_UNCHANGED` sentinel value to distinguish between "not provided" and "set to False/None". This enables partial config updates without requiring all fields.

### Graceful Degradation for External Tools
`RealGitHubOps` and `RealGraphiteOps` use try/except blocks to handle missing CLI tools gracefully, returning empty results rather than crashing. This acknowledges that gh and gt may not be installed or authenticated.

### Lazy-Loaded Caching
`RealGlobalConfigOps` implements lazy-loaded caching with cache invalidation on writes. The cache is only loaded when first accessed and invalidated after `set()` operations.

### JSON Cache Parsing
Graphite operations read JSON cache files (.graphite_pr_info, .graphite_cache_persist) and parse them with dedicated helper functions. These helpers are separate from the class to enable unit testing and reuse.

## Critical Functions

### parse_graphite_pr_info
**Location**: graphite_ops.py
**Purpose**: Parse Graphite's .graphite_pr_info JSON into PullRequestInfo objects. Converts Graphite URLs to GitHub URLs.
**Key logic**: Iterates through prInfos array, extracts branch name and PR data, converts Graphite URL format to GitHub format

### parse_graphite_cache
**Location**: graphite_ops.py
**Purpose**: Parse Graphite's .graphite_cache_persist JSON into BranchMetadata objects. Enriches with git commit SHAs.
**Key logic**: Extracts branch relationships (parent, children), validates data types, combines with git branch heads

### read_graphite_json_file
**Location**: graphite_ops.py
**Purpose**: Read and parse Graphite JSON files with error handling and warnings
**Key logic**: Reads file, parses JSON, emits UserWarning on parse failure before re-raising exception

### parse_github_pr_list
**Location**: github_ops.py
**Purpose**: Parse gh pr list JSON output into PullRequestInfo objects
**Key logic**: Iterates through PR array, determines check status from statusCheckRollup, parses owner/repo from URL

### _determine_checks_status
**Location**: github_ops.py
**Purpose**: Determine overall CI check status from GitHub check rollup data
**Key logic**: Returns None if no checks, True if all passed/skipped/neutral, False if any pending or failed

### detect_shell_from_env
**Location**: shell_ops.py
**Purpose**: Detect shell type and RC file path from SHELL environment variable
**Key logic**: Extracts shell name from path, maps to RC file location for bash/zsh/fish

### extract_plan_title
**Location**: file_utils.py
**Purpose**: Extract first markdown heading from plan file, handling YAML frontmatter
**Key logic**: Uses frontmatter library to parse YAML, then finds first line starting with #

### create_context
**Location**: context.py
**Purpose**: Factory function that creates WorkstackContext with real or dry-run implementations
**Key logic**: Creates real implementations, wraps with dry-run wrappers if dry_run=True, returns assembled context

## Data Flow

### PR Information Flow
1. **GitHub source**: `RealGitHubOps.get_prs_for_repo()` executes `gh pr list` command
2. **Parsing**: `parse_github_pr_list()` converts JSON to `PullRequestInfo` objects
3. **Graphite source**: `RealGraphiteOps.get_prs_from_graphite()` reads .graphite_pr_info cache
4. **Parsing**: `parse_graphite_pr_info()` converts JSON to `PullRequestInfo` objects
5. **URL conversion**: Graphite URLs converted to GitHub URLs via `_graphite_url_to_github_url()`

### Branch Metadata Flow
1. **Source**: `RealGraphiteOps.get_all_branches()` reads .graphite_cache_persist
2. **Parsing**: `parse_graphite_cache()` converts JSON to `BranchMetadata` objects
3. **Enrichment**: Git branch heads fetched via `GitOps.get_branch_head()` for each branch
4. **Stack building**: `RealGraphiteOps.get_branch_stack()` traverses parent/children relationships to build linear stack

### Configuration Flow
1. **Read**: `RealGlobalConfigOps` lazy-loads ~/.workstack/config.toml on first access
2. **Cache**: Subsequent reads use cached values
3. **Write**: `set()` method updates file and invalidates cache
4. **Dry-run**: `DryRunGlobalConfigOps` prints intended updates instead of writing

### Worktree Operations Flow
1. **Query**: `RealGitOps.list_worktrees()` executes `git worktree list --porcelain`
2. **Parsing**: Output parsed into `