# Semantic Lookup Index

## [Worktree Creation and Setup]
**Search phrases**: create worktree, new worktree, scaffold environment, initialize branch, setup branch, create branch, worktree initialization, branch creation, environment setup, post-create hooks, .env file generation, plan file handling
**Files**: create.py, init.py
**Description**: Creating new worktrees with branch management, environment variable templating, post-create command execution, and plan file integration. Includes branch sanitization, worktree naming conventions, and configuration-driven setup.

## [Worktree Navigation and Switching]
**Search phrases**: switch worktree, activate worktree, change directory, navigate branches, jump to branch, move up stack, move down stack, graphite navigation, branch hierarchy navigation, worktree activation, shell integration activation
**Files**: switch.py, up.py, down.py, jump.py
**Description**: Switching between worktrees and branches with automatic environment activation. Includes Graphite stack navigation (up/down), branch jumping, and shell script generation for directory changes and environment setup.

## [Worktree Removal and Cleanup]
**Search phrases**: delete worktree, remove worktree, cleanup worktrees, merged branches, closed PRs, garbage collection, branch deletion, stack deletion, worktree pruning
**Files**: remove.py, gc.py, sync.py
**Description**: Removing worktrees and associated branches, identifying merged/closed PRs for cleanup, garbage collection of stale worktrees, and automatic pruning of git metadata.

## [Worktree Movement and Reorganization]
**Search phrases**: move branch, swap branches, reorganize worktrees, move between worktrees, branch relocation, worktree swapping, branch movement
**Files**: move.py, rename.py
**Description**: Moving branches between worktrees, swapping branch locations, renaming worktrees, and updating associated metadata (.env files, git references).

## [Worktree Listing and Inspection]
**Search phrases**: list worktrees, show worktrees, worktree status, branch stacks, graphite stacks, PR information, CI checks, plan files, worktree overview
**Files**: list.py, tree.py, status.py
**Description**: Displaying worktrees with branch information, Graphite stack visualization, PR status indicators, CI check results, and plan file summaries. Includes tree-based hierarchy visualization and detailed status reporting.

## [Graphite Integration]
**Search phrases**: graphite branches, graphite metadata, branch relationships, parent-child branches, trunk branches, stack information, graphite cache, branch hierarchy
**Files**: gt.py, list.py, tree.py, up.py, down.py, jump.py, switch.py
**Description**: Machine-readable access to Graphite metadata, branch hierarchy visualization, parent-child relationship navigation, and stack-based operations. Includes tree formatting and branch metadata queries.

## [Configuration Management]
**Search phrases**: config get, config set, config list, global configuration, repository configuration, environment variables, post-create commands, configuration keys, settings management
**Files**: config.py, init.py
**Description**: Reading and writing global and repository-level configuration, managing environment variable templates, post-create command definitions, and configuration key validation.

## [Shell Integration and Activation]
**Search phrases**: shell completion, shell wrapper, bash completion, zsh completion, fish completion, auto-activation, environment activation, virtual environment, .env loading, shell integration setup
**Files**: completion.py, shell_integration.py, init.py, switch.py, create.py, up.py, down.py, jump.py
**Description**: Shell completion script generation for bash/zsh/fish, shell wrapper functions for automatic worktree activation, environment variable loading, and virtual environment setup. Includes shell detection and integration setup instructions.

## [Synchronization with Graphite]
**Search phrases**: sync with graphite, gt sync, branch synchronization, merged branch cleanup, automatic cleanup, force sync, dry-run sync, branch deletion automation
**Files**: sync.py
**Description**: Synchronizing with Graphite, identifying and removing merged/closed worktrees, automatic branch cleanup with confirmation, and fallback to root worktree after cleanup.

## [Repository Context Discovery]
**Search phrases**: discover repository, find git root, repository detection, workstacks directory, worktree path resolution, repository context
**Files**: init.py, create.py, list.py, tree.py, switch.py, remove.py, move.py, rename.py, sync.py, gc.py, status.py, up.py, down.py, jump.py
**Description**: Discovering repository root, locating workstacks directories, resolving worktree paths, and validating repository context for all operations.

## [Dry-Run and Safety Features]
**Search phrases**: dry-run mode, preview operations, destructive operations, confirmation prompts, force flag, safety checks, uncommitted changes detection
**Files**: remove.py, move.py, rename.py, sync.py
**Description**: Dry-run mode for previewing destructive operations, confirmation prompts for user safety, force flags to skip confirmpts, and detection of uncommitted changes before operations.

## [Error Handling and Validation]
**Search phrases**: input validation, error messages, branch validation, worktree validation, reserved names, detached HEAD, git errors, graphite errors
**Files**: create.py, switch.py, remove.py, move.py, rename.py, jump.py, up.py, down.py
**Description**: Comprehensive input validation, user-friendly error messages, detection of edge cases (detached HEAD, reserved names, missing branches), and graceful error handling.

## [Plan File Management]
**Search phrases**: plan files, .PLAN.md, plan extraction, plan title, plan file handling, plan-based worktree creation
**Files**: create.py, list.py, status.py
**Description**: Handling plan markdown files (.PLAN.md), extracting plan titles, deriving worktree names from plan filenames, and displaying plan summaries in worktree listings.

## [PR Status and GitHub Integration]
**Search phrases**: pull request status, PR information, merged PRs, closed PRs, PR checks, CI status, GitHub API, PR links, draft PRs
**Files**: list.py, gc.py, sync.py
**Description**: Fetching PR status from GitHub, displaying PR information with emoji indicators, checking CI status, identifying merged/closed PRs for cleanup, and generating clickable PR links.

## [Branch Naming and Sanitization]
**Search phrases**: branch name sanitization, worktree name sanitization, safe branch names, branch component sanitization, name validation, special character handling
**Files**: create.py, rename.py
**Description**: Sanitizing branch and worktree names for safe filesystem and git usage, handling special characters, collapsing separators, and providing sensible defaults for empty results.

## [Environment Variable Templating]
**Search phrases**: .env file generation, environment templates, variable substitution, dotenv files, environment configuration, template variables
**Files**: create.py, rename.py
**Description**: Generating .env files from configuration templates with variable substitution (worktree_path, repo_root, name), quoting values for dotenv compatibility.

## [Worktree Metadata and Git Operations]
**Search phrases**: git worktree operations, worktree metadata, branch checkout, branch creation, detached HEAD, worktree pruning, git metadata management
**Files**: create.py, remove.py, move.py, switch.py, up.py, down.py, jump.py
**Description**: Low-level git worktree operations including creation, removal, branch checkout, metadata pruning, and handling edge cases like detached HEAD states.

## [Script Generation and Temp Files]
**Search phrases**: activation scripts, shell scripts, temp file generation, script output, cd scripts, environment activation scripts
**Files**: create.py, switch.py, up.py, down.py, jump.py, sync.py, shell_integration.py
**Description**: Generating shell activation scripts for directory changes and environment setup, writing scripts to temporary files, and outputting script paths for shell wrapper execution.

## [Initialization and Setup]
**Search phrases**: workstack initialization, first-time setup, global config creation, repository setup, preset selection, shell setup, graphite detection
**Files**: init.py
**Description**: First-time workstack initialization, global configuration creation, repository-level config scaffolding, preset-based configuration templates, and shell integration setup.

## [Preset Configuration]
**Search phrases**: configuration presets, preset templates, auto-detection, preset selection, project-specific presets, generic presets
**Files**: init.py
**Description**: Discovering and applying configuration presets, auto-detecting appropriate presets based on repository characteristics, and rendering preset templates.