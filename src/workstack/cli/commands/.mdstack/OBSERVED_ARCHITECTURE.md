# Observed Architecture

## Overview

The `commands` package contains Click command implementations for the workstack CLI. Each module represents a user-facing command or command group, implementing specific workflows for managing git worktrees, branches, and repository configuration. The architecture emphasizes separation of concerns, with each command handling a distinct user workflow while delegating to shared core operations through the `WorkstackContext`.

## Module Organization

### sync.py
**Responsibility**: Implements the `sync` command that synchronizes with Graphite and cleans up merged worktrees.
**Key exports**: `sync_cmd` (Click command), `_emit` (message output helper), `_return_to_original_worktree` (navigation helper)
**Key patterns**: 
- Script mode support for shell integration (all output to stderr, directory changes via script)
- Multi-step workflow with clear separation: verify → save location → sync → identify merged → cleanup → return
- Reuses `_remove_worktree` from `remove.py` for consistent deletion logic

### tree.py
**Responsibility**: Implements the `tree` command that displays worktree hierarchy with Graphite parent-child relationships.
**Key exports**: `tree_cmd` (Click command)
**Key patterns**: 
- Delegates tree building to `build_workstack_tree` from `workstack.cli.tree`
- Requires Graphite to be enabled
- Minimal command logic; mostly orchestration

### config.py
**Responsibility**: Implements the `config` command group with `list`, `get`, and `set` subcommands for managing global and repository-level configuration.
**Key exports**: `config_group`, `config_list`, `config_get`, `config_set` (Click commands), helper functions for parsing config keys
**Key patterns**:
- Hierarchical key parsing (e.g., `env.KEY`, `post_create.shell`, `post_create.commands`)
- Separate handling for global config (via `global_config_ops`) and repo config (via `LoadedConfig`)
- Defensive error handling with clear user messages for missing config

### list.py
**Responsibility**: Implements the `list` command (alias `ls`) that displays worktrees with optional Graphite stacks and PR information.
**Key exports**: `list_cmd`, `ls_cmd` (Click commands), `_list_worktrees` (internal implementation)
**Key patterns**:
- Complex filtering logic for Graphite stacks (`_filter_stack_for_worktree`) that differs between root and non-root worktrees
- PR information fetching with fallback strategy: Graphite → GitHub (with checks) → GitHub (without checks)
- Colorized output with emoji indicators for PR status
- Plan file summary display (`.PLAN.md` extraction)

### create.py
**Responsibility**: Implements the `create` command for creating new worktrees with branch creation, environment setup, and post-create hooks.
**Key exports**: `create` (Click command), sanitization functions, `add_worktree`, `make_env_content`, `run_commands_in_worktree`
**Key patterns**:
- Multiple creation modes: default, `--from-current-branch`, `--from-branch`, `--plan`
- Graphite integration for branch creation with staged changes validation
- Environment file generation with template substitution
- Post-create command execution with optional shell wrapper
- Script mode support for shell integration

### gc.py
**Responsibility**: Implements the `gc` command that identifies merged/closed worktrees safe for deletion (garbage collection).
**Key exports**: `gc_cmd` (Click command)
**Key patterns**:
- Debug output mode for transparency
- Reuses PR status checking from `github_ops`
- Display formatting consistent with `sync.py`
- Read-only operation (no deletion, just identification)

### completion.py
**Responsibility**: Implements the `completion` command group with subcommands for bash, zsh, and fish shell completion generation.
**Key exports**: `completion_group`, `completion_bash`, `completion_zsh`, `completion_fish` (Click commands)
**Key patterns**:
- Delegates to shell completion generation via environment variable (`_WORKSTACK_COMPLETE`)
- Subprocess-based approach to invoke workstack with completion environment
- Provides setup instructions for each shell type

### rename.py
**Responsibility**: Implements the `rename` command for renaming worktree directories and updating git metadata.
**Key exports**: `rename_cmd` (Click command)
**Key patterns**:
- Dry-run support via context creation
- Regenerates `.env` file with updated paths after rename
- Delegates to `git_ops.move_worktree` for git-level operations

### gt.py
**Responsibility**: Implements the `graphite` command group providing machine-readable access to Graphite metadata.
**Key exports**: `graphite_group`, `graphite_branches_cmd` (Click command), tree formatting helpers
**Key patterns**:
- Multiple output formats: text (simple list), JSON (structured), tree (hierarchical)
- Recursive tree formatting with proper indentation and connectors
- Commit message retrieval for tree display
- Requires Graphite to be enabled

### down.py
**Responsibility**: Implements the `down` command for navigating to parent branch in Graphite stack.
**Key exports**: `down_cmd` (Click command)
**Key patterns**:
- Delegates navigation logic to `_resolve_down_navigation` from `switch.py`
- Script mode support for shell integration
- Handles special case of trunk branch (switches to root repo)

### remove.py
**Responsibility**: Implements the `remove` command (alias `rm`) for deleting worktrees with optional stack deletion.
**Key exports**: `remove_cmd`, `rm_cmd` (Click commands), `_remove_worktree` (internal implementation)
**Key patterns**:
- Multi-step operation planning with single confirmation prompt
- Fallback strategy for git worktree removal (try git, then manual cleanup, then prune)
- Optional Graphite stack deletion with trunk branch filtering
- Dry-run support
- Reused by `sync.py` for automatic cleanup

### jump.py
**Responsibility**: Implements the `jump` command for finding and switching to a worktree by branch name.
**Key exports**: `jump_cmd` (Click command), `_perform_jump`, `_format_worktree_info`
**Key patterns**:
- Searches all worktrees for branch in Graphite stack (not just direct checkout)
- Handles ambiguity: multiple worktrees containing branch, or branch directly checked out in one
- Automatic branch checkout if needed before activation
- Script mode support for shell integration

### up.py
**Responsibility**: Implements the `up` command for navigating to child branch in Graphite stack.
**Key exports**: `up_cmd` (Click command)
**Key patterns**:
- Delegates navigation logic to `_resolve_up_navigation` from `switch.py`
- Script mode support for shell integration
- Mirrors `down.py` structure

### switch.py
**Responsibility**: Implements the `switch` command for changing to a worktree with environment activation.
**Key exports**: `switch_cmd` (Click command), navigation helpers (`_resolve_up_navigation`, `_resolve_down_navigation`), activation helpers
**Key patterns**:
- Three modes: explicit name, `--up` (child), `--down` (parent)
- Shared navigation logic used by `up.py` and `down.py`
- Shell completion for worktree names (includes "root")
- Script mode support for shell integration
- Defensive error handling in completion function (returns empty list on error)

### move.py
**Responsibility**: Implements the `move` command for moving branches between worktrees with explicit source specification.
**Key exports**: `move_cmd` (Click command), operation executors (`execute_move`, `execute_swap`), helpers
**Key patterns**:
- Three source resolution modes: `--current`, `--branch`, `--worktree`
- Three operation types: move (target doesn't exist), swap (both exist with branches), create (target empty)
- Detached HEAD strategy to avoid simultaneous branch checkout conflicts
- Uncommitted changes detection with force override
- Fallback branch specification for source after move

### prepare_cwd_recovery.py
**Responsibility**: Implements the hidden `__prepare_cwd_recovery` command that pre-generates recovery scripts for passthrough flows.
**Key exports**: `prepare_cwd_recovery_cmd` (Click command), `generate_recovery_script`
**Key patterns**:
- Graceful degradation: returns None if cwd vanished or repo not found
- Used by shell integration to handle directory removal edge cases
- Intentionally guards against runtime races with defensive checks

### init.py
**Responsibility**: Implements the `init` command for initializing workstack in a repository with global/repo config setup.
**Key exports**: `init_cmd` (Click command), config template rendering, shell setup helpers
**Key patterns**:
- Three modes: global config setup, repo config setup, shell integration setup
- Preset system for config templates with auto-detection (e.g., "dagster" vs "generic")
- Graphite detection and reporting
- `.gitignore` management for `.PLAN.md` and `.env`
- Shell integration setup with manual instructions

### shell_integration.py
**Responsibility**: Implements the hidden `__shell` command that serves as unified entry point for shell integration wrappers.
**Key exports**: `hidden_shell_cmd` (Click command)
**Key patterns**:
- Delegates to `handle_shell_request` from `workstack.cli.shell_integration.handler`
- Passthrough marker support for shell wrapper coordination
- Minimal command logic; mostly delegation

### status.py
**Responsibility**: Implements the `status` command that shows comprehensive status of current worktree.
**Key exports**: `status_cmd` (Click command)
**Key patterns**:
- Orchestrator pattern: collects status from multiple sources (Git, Graphite, GitHub, plan files)
- Worktree detection with defensive path existence checks
- Delegates rendering to `SimpleRenderer`

## Core Abstractions

### Click Command Pattern
**Location**: All modules
**Purpose**: Each command is a Click command function decorated with `@click.command()` or `@click.group()`, following Click's callback-based architecture
**Type**: Click command functions with `@click.pass_obj` to receive `WorkstackContext`

### WorkstackContext
**Location**: Passed to all commands via Click's context object
**Purpose**: Central dependency injection container providing access to git operations, GitHub operations, Graphite operations, and configuration
**Type**: Dataclass-like object from `workstack.core.context`

### RepoContext
**Location**: Returned by `discover_repo_context()`
**Purpose**: Encapsulates repository root and workstacks directory information
**Type**: Named tuple or dataclass with `root` and `workstacks_dir` attributes

## Critical Functions

### _emit (sync.py)
**Location**: sync.py
**Purpose**: Unified message output that respects script mode (all output to stderr in script mode)
**Signature**: `_emit(message: str, *, script_mode: bool, error: bool = False) -> None`
**Key insight**: Enables shell wrapper to capture only activation scripts from stdout

### _filter_stack_for_worktree (list.py)
**Location**: list.py
**Purpose**: Filters Graphite stack to show only relevant branches for a worktree (ancestors + current + active descendants)
**Signature**: `_filter_stack_for_worktree(stack: list[str], current_worktree_path: Path, all_worktree_branches: dict[Path, str | None], is_root_worktree: bool) -> list[str]`
**Key insight**: Different filtering logic for root vs non-root worktrees to keep display clean

### _remove_worktree (remove.py)
**Location**: remove.py
**Purpose**: Internal implementation of worktree removal with optional stack deletion
**Signature**: `_remove_worktree(ctx: WorkstackContext, name: str, force: bool, delete_stack: bool, dry_run: bool) -> None`
**Key insight**: Reused by `sync.py` for automatic cleanup; handles multi-step operations with single confirmation

### add_worktree (create.py)
**Location**: create.py
**Purpose**: Creates a git worktree with branch creation strategy (Graphite vs git)
**Signature**: `add_worktree(ctx: WorkstackContext, repo_root: Path, path: Path, *, branch: str | None, ref: str | None, use_existing_branch: bool, use_graphite: bool) -> None`
**Key insight**: Abstracts branch creation strategy; handles Graphite staged changes validation

### sanitize_worktree_name (create.py)
**Location**: create.py
**Purpose**: Sanitizes arbitrary names into valid directory names
**Signature**: `sanitize_worktree_name(name: str) -> str`
**Key insight**: Lowercases, replaces underscores with hyphens, removes unsafe characters

### strip_plan_from_filename (create.py)
**Location**: create.py
**Purpose**: Intelligently removes "plan" or "implementation plan" from filenames
**Signature**: `strip_plan_from_filename(filename: str) -> str`
**Key insight**: Handles case-insensitive matching with various separators; preserves original if removal would leave empty

### _resolve_up_navigation (switch.py)
**Location**: switch.py
**Purpose**: Determines target branch when navigating up (to child) in Graphite stack
**Signature**: `_resolve_up_navigation(ctx: WorkstackContext, repo: RepoContext, current_branch: str, worktrees: list[WorktreeInfo]) -> str`
**Key insight**: Shared by `up.py` and `switch.py --up`; validates target has worktree

### _resolve_down_navigation (switch.py)
**Location**: switch.py
**Purpose**: Determines target branch when navigating down (to parent) in Graphite stack
**Signature**: `_resolve_down_navigation(ctx: WorkstackContext, repo: RepoContext, current_branch: str, worktrees: list[WorktreeInfo]) -> str`
**Key insight**: Shared by `down.py` and `switch.py --down`; handles trunk branch special case

### _activate_worktree (switch.py)
**Location**: switch.py
**Purpose**: Generates activation script or user instructions for switching to a worktree
**Signature**: `_activate_worktree(repo: RepoContext, target_path: Path, script: bool, command_name: str) -> None`
**Key insight**: Shared by multiple commands; raises SystemExit after activation

### complete_worktree_names (switch.py)
**Location**: switch.py
**Purpose**: Shell completion function for worktree names
**Signature**: `complete_worktree_names(ctx: click.Context, param: click.Parameter | None, incomplete: str) -> list[str]`
**Key insight**: Error boundary pattern; returns empty list on exception for graceful degradation

### resolve_source_worktree (move.py)
**Location**: move.py
**Purpose**: Determines source worktree from `--current`, `--branch`, or `--worktree` flags
**Signature**: `resolve_source_worktree(ctx: WorkstackContext, repo_root: Path, *, current: bool, branch: str | None, worktree: str | None, workstacks_dir: Path) -> Path`
**Key insight**: Validates mutual exclusivity; defaults to current worktree

### detect_operation_type (move.py)
**Location**: move.py
**Purpose**: Determines whether move operation should move, swap, or create
**Signature**: `detect_operation_type(source_wt: Path, target_wt: Path, ctx: WorkstackContext, repo_root: Path) -> str`
**Key insight**: Returns "move", "swap", or "create" based on target existence and branch state

## Architectural Patterns

### Script Mode Pattern
**Used in**: sync.py, create.py, switch.py, up.py, down.py, jump.py
**Purpose**: Enables shell integration by outputting activation scripts instead of performing directory changes
**Implementation**: 
- `--script` flag generates shell script and outputs path to stdout
- All user messages go to stderr in script mode
- Shell wrapper executes script to perform actual directory change
- Allows workstack to work with or without shell integration

### Error Boundary Pattern
**Used in**: complete_worktree_names (switch.py), prepare_cwd_recovery.py
**Purpose**: Graceful degradation when operations fail