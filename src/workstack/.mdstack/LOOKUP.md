# Semantic Lookup Index

## Child Packages
- **[cli]** (cli/): Command-line interface with commands for worktree management, configuration, and shell integration
- **[core]** (core/): Foundational abstractions for git operations, GitHub API, Graphite integration, and configuration management
- **[status]** (status/): Status collection and rendering system for displaying worktree information

## [Worktree Creation and Setup]
**Search phrases**: create worktree, new worktree, scaffold environment, initialize branch, setup branch, create branch, worktree initialization, branch creation, environment setup, post-create hooks, .env file generation, plan file handling, branch sanitization
**Files**: cli/commands/create.py, cli/config.py, cli/activation.py
**Child packages**: cli
**Description**: Creating new worktrees with branch management, environment variable templating, post-create command execution, and plan file integration. Includes branch sanitization, worktree naming conventions, and configuration-driven setup.

## [Worktree Navigation and Switching]
**Search phrases**: switch worktree, activate worktree, change directory, navigate branches, jump to branch, move up stack, move down stack, graphite navigation, branch hierarchy navigation, worktree activation, shell integration activation, directory change
**Files**: cli/commands/switch.py, cli/commands/up.py, cli/commands/down.py, cli/commands/jump.py, cli/activation.py, cli/shell_utils.py
**Child packages**: cli
**Description**: Switching between worktrees and branches with automatic environment activation. Includes Graphite stack navigation (up/down), branch jumping, and shell script generation for directory changes and environment setup.

## [Worktree Removal and Cleanup]
**Search phrases**: delete worktree, remove worktree, cleanup worktrees, merged branches, closed PRs, garbage collection, branch deletion, stack deletion, worktree pruning, stale worktrees
**Files**: cli/commands/remove.py, cli/commands/gc.py, cli/commands/sync.py
**Child packages**: cli
**Description**: Removing worktrees and associated branches, identifying merged/closed PRs for cleanup, garbage collection of stale worktrees, and automatic pruning of git metadata.

## [Worktree Movement and Reorganization]
**Search phrases**: move branch, swap branches, reorganize worktrees, move between worktrees, branch relocation, worktree swapping, branch movement, rename worktree
**Files**: cli/commands/move.py, cli/commands/rename.py
**Child packages**: cli
**Description**: Moving branches between worktrees, swapping branch locations, renaming worktrees, and updating associated metadata (.env files, git references).

## [Worktree Listing and Inspection]
**Search phrases**: list worktrees, show worktrees, worktree status, branch stacks, graphite stacks, PR information, CI checks, plan files, worktree overview, tree visualization, hierarchy display
**Files**: cli/commands/list.py, cli/commands/tree.py, cli/commands/status.py, cli/tree.py
**Child packages**: cli
**Description**: Displaying worktrees with branch information, Graphite stack visualization, PR status indicators, CI check results, and plan file summaries. Includes tree-based hierarchy visualization and detailed status reporting.

## [Graphite Integration]
**Search phrases**: graphite branches, graphite metadata, branch relationships, parent-child branches, trunk branches, stack information, graphite cache, branch hierarchy, stacked workflow, dependent branches
**Files**: cli/graphite.py, cli/tree.py, cli/commands/gt.py, cli/commands/list.py, cli/commands/tree.py, cli/commands/up.py, cli/commands/down.py, cli/commands/jump.py, cli/commands/switch.py, core/graphite_ops.py
**Child packages**: cli, core
**Description**: Machine-readable access to Graphite metadata, branch hierarchy visualization, parent-child relationship navigation, and stack-based operations. Includes tree formatting, branch metadata queries, and cache file parsing.

## [Configuration Management]
**Search phrases**: config get, config set, config list, global configuration, repository configuration, environment variables, post-create commands, configuration keys, settings management, config file, TOML configuration
**Files**: cli/config.py, cli/commands/config.py, cli/commands/init.py, core/global_config_ops.py
**Child packages**: cli, core
**Description**: Reading and writing global and repository-level configuration, managing environment variable templates, post-create command definitions, and configuration key validation. Includes TOML file parsing and hierarchical key access.

## [Shell Integration and Activation]
**Search phrases**: shell completion, shell wrapper, bash completion, zsh completion, fish completion, auto-activation, environment activation, virtual environment, .env loading, shell integration setup, shell detection, activation script
**Files**: cli/commands/completion.py, cli/commands/shell_integration.py, cli/commands/init.py, cli/activation.py, cli/shell_utils.py, cli/shell_integration/handler.py, core/shell_ops.py
**Child packages**: cli, core
**Description**: Shell completion script generation for bash/zsh/fish, shell wrapper functions for automatic worktree activation, environment variable loading, and virtual environment setup. Includes shell detection, integration setup instructions, and script generation.

## [Synchronization with Graphite]
**Search phrases**: sync with graphite, gt sync, branch synchronization, merged branch cleanup, automatic cleanup, force sync, dry-run sync, branch deletion automation, sync workflow
**Files**: cli/commands/sync.py, core/graphite_ops.py
**Child packages**: cli, core
**Description**: Synchronizing with Graphite, identifying and removing merged/closed worktrees, automatic branch cleanup with confirmation, and fallback to root worktree after cleanup.

## [Repository Context Discovery]
**Search phrases**: discover repository, find git root, repository detection, workstacks directory, worktree path resolution, repository context, git root detection, repo initialization
**Files**: cli/core.py, cli/commands/init.py, cli/commands/create.py, cli/commands/list.py, cli/commands/tree.py, cli/commands/switch.py, cli/commands/remove.py, cli/commands/move.py, cli/commands/rename.py, cli/commands/sync.py, cli/commands/gc.py, cli/commands/status.py, cli/commands/up.py, cli/commands/down.py, cli/commands/jump.py
**Child packages**: cli
**Description**: Discovering repository root, locating workstacks directories, resolving worktree paths, and validating repository context for all operations. Includes handling of git worktrees and common directory detection.

## [Dry-Run and Safety Features]
**Search phrases**: dry-run mode, preview operations, destructive operations, confirmation prompts, force flag, safety checks, uncommitted changes detection, operation planning
**Files**: cli/commands/remove.py, cli/commands/move.py, cli/commands/rename.py, cli/commands/sync.py, cli/core.py, core/gitops.py, core/github_ops.py, core/graphite_ops.py, core/global_config_ops.py
**Child packages**: cli, core
**Description**: Dry-run mode for previewing destructive operations, confirmation prompts for user safety, force flags to skip confirmpts, and detection of uncommitted changes before operations.

## [Error Handling and Validation]
**Search phrases**: input validation, error messages, branch validation, worktree validation, reserved names, detached HEAD, git errors, graphite errors, validation, error boundary
**Files**: cli/commands/create.py, cli/commands/switch.py, cli/commands/remove.py, cli/commands/move.py, cli/commands/rename.py, cli/commands/jump.py, cli/commands/up.py, cli/commands/down.py, cli/core.py
**Child packages**: cli
**Description**: Comprehensive input validation, user-friendly error messages, detection of edge cases (detached HEAD, reserved names, missing branches), and graceful error handling with error boundary patterns.

## [Plan File Management]
**Search phrases**: plan files, .PLAN.md, plan extraction, plan title, plan file handling, plan-based worktree creation, plan summary
**Files**: cli/commands/create.py, cli/commands/list.py, cli/commands/status.py, core/file_utils.py
**Child packages**: cli, core
**Description**: Handling plan markdown files (.PLAN.md), extracting plan titles, deriving worktree names from plan filenames, and displaying plan summaries in worktree listings.

## [PR Status and GitHub Integration]
**Search phrases**: pull request status, PR information, merged PRs, closed PRs, PR checks, CI status, GitHub API, PR links, draft PRs, PR metadata
**Files**: cli/commands/list.py, cli/commands/gc.py, cli/commands/sync.py, core/github_ops.py
**Child packages**: cli, core
**Description**: Fetching PR status from GitHub, displaying PR information with emoji indicators, checking CI status, identifying merged/closed PRs for cleanup, and generating clickable PR links.

## [Branch Naming and Sanitization]
**Search phrases**: branch name sanitization, worktree name sanitization, safe branch names, branch component sanitization, name validation, special character handling, filename sanitization
**Files**: cli/commands/create.py, cli/commands/rename.py, cli/core.py
**Child packages**: cli
**Description**: Sanitizing branch and worktree names for safe filesystem and git usage, handling special characters, collapsing separators, and providing sensible defaults for empty results.

## [Environment Variable Templating]
**Search phrases**: .env file generation, environment templates, variable substitution, dotenv files, environment configuration, template variables, environment setup
**Files**: cli/commands/create.py, cli/commands/rename.py, cli/config.py, cli/activation.py
**Child packages**: cli
**Description**: Generating .env files from configuration templates with variable substitution (worktree_path, repo_root, name), quoting values for dotenv compatibility, and loading environment variables.

## [Worktree Metadata and Git Operations]
**Search phrases**: git worktree operations, worktree metadata, branch checkout, branch creation, detached HEAD, worktree pruning, git metadata management, git common directory
**Files**: cli/commands/create.py, cli/commands/remove.py, cli/commands/move.py, cli/commands/switch.py, cli/commands/up.py, cli/commands/down.py, cli/commands/jump.py, cli/core.py, core/gitops.py
**Child packages**: cli, core
**Description**: Low-level git worktree operations including creation, removal, branch checkout, metadata pruning, and handling edge cases like detached HEAD states and git common directory resolution.

## [Script Generation and Temp Files]
**Search phrases**: activation scripts, shell scripts, temp file generation, script output, cd scripts, environment activation scripts, script metadata, script cleanup
**Files**: cli/commands/create.py, cli/commands/switch.py, cli/commands/up.py, cli/commands/down.py, cli/commands/jump.py, cli/commands/sync.py, cli/commands/shell_integration.py, cli/activation.py, cli/shell_utils.py
**Child packages**: cli
**Description**: Generating shell activation scripts for directory changes and environment setup, writing scripts to temporary files, managing script lifecycle, and outputting script paths for shell wrapper execution.

## [Initialization and Setup]
**Search phrases**: workstack initialization, first-time setup, global config creation, repository setup, preset selection, shell setup, graphite detection, initial configuration
**Files**: cli/commands/init.py, cli/cli.py, cli/config.py
**Child packages**: cli
**Description**: First-time workstack initialization, global configuration creation, repository-level config scaffolding, preset-based configuration templates, and shell integration setup.

## [Preset Configuration]
**Search phrases**: configuration presets, preset templates, auto-detection, preset selection, project-specific presets, generic presets, preset rendering
**Files**: cli/commands/init.py, cli/config.py
**Child packages**: cli
**Description**: Discovering and applying configuration presets, auto-detecting appropriate presets based on repository characteristics, and rendering preset templates with variable substitution.

## [Tree Visualization]
**Search phrases**: tree display, ASCII tree, tree rendering, box-drawing characters, tree structure, hierarchy visualization, branch tree, worktree tree, tree formatting
**Files**: cli/tree.py, cli/commands/tree.py, cli/commands/gt.py
**Child packages**: cli
**Description**: Building and rendering tree structures showing worktrees and their Graphite dependency relationships. Uses Unicode box-drawing characters for visual hierarchy and supports colorized output for current worktree highlighting.

## [CLI Entry Point and Command Registration]
**Search phrases**: CLI entry point, command registration, command group, click commands, CLI initialization, command dispatcher, main entry point
**Files**: cli/cli.py, cli/commands/__init__.py, __init__.py, __main__.py
**Child packages**: cli
**Description**: Main CLI entry point, command registration, context initialization, and command group organization. Handles version display and help option configuration.

## [Debug Logging]
**Search phrases**: debug logging, debug mode, debug output, troubleshooting, debug file, debug information, WORKSTACK_DEBUG
**Files**: cli/debug.py
**Child packages**: cli
**Description**: Debug logging functionality when WORKSTACK_DEBUG=1 is set. Debug logs are written to /tmp/workstack-debug.log for troubleshooting and development.

## [Shell Wrapper Coordination]
**Search phrases**: shell wrapper, shell integration handler, passthrough marker, shell request handling, shell coordination, wrapper execution
**Files**: cli/commands/shell_integration.py, cli/shell_integration/handler.py, cli/shell_utils.py
**Child packages**: cli
**Description**: Unified entry point for shell integration wrappers, passthrough marker support for shell wrapper coordination, and script execution coordination between workstack and shell wrappers.

## [Worktree Path Resolution]
**Search phrases**: worktree path, path resolution, worktree directory, workstacks directory, path validation, path construction, directory structure
**Files**: cli/core.py, cli/commands/create.py, cli/commands/list.py, cli/commands/switch.py, cli/commands/move.py, cli/commands/rename.py
**Child packages**: cli
**Description**: Resolving worktree paths within workstacks directory, constructing absolute paths, validating path safety, and handling special cases like root worktree.

## [Current Working Directory Recovery]
**Search phrases**: cwd recovery, directory recovery, current directory, working directory preservation, directory change fallback, cwd restoration
**Files**: cli/commands/prepare_cwd_recovery.py, cli/shell_utils.py
**Child packages**: cli
**Description**: Pre-generating recovery scripts for passthrough flows to handle edge cases where current working directory becomes invalid after worktree operations.

## [Git Operations Abstraction]
**Search phrases**: git commands, branch management, worktree operations, checkout, commit information, file status, branch tracking, git interface, abstract git operations
**Files**: core/gitops.py
**Child packages**: core
**Description**: Abstract interface and production implementation for git operations including worktree management, branch operations, commit queries, and file status tracking. Supports dry-run mode through wrapper implementations.

## [GitHub Operations Abstraction]
**Search phrases**: pull request information, PR status, GitHub API, CI checks, check status, PR list, branch PR mapping, github interface, abstract github operations
**Files**: core/github_ops.py
**Child packages**: core
**Description**: Abstract interface and production implementation for GitHub operations including PR fetching, status queries, and CI check status determination. Gracefully handles missing gh CLI.

## [Graphite Operations Abstraction]
**Search phrases**: Graphite CLI, gt commands, branch stack, branch metadata, PR info cache, branch relationships, trunk detection, sync, graphite interface, abstract graphite operations
**Files**: core/graphite_ops.py
**Child packages**: core
**Description**: Abstract interface and production implementation for Graphite operations including branch stack traversal, cache parsing, PR info retrieval, and synchronization. Supports dry-run mode.

## [Branch Metadata Data Structure]
**Search phrases**: branch information, parent branch, child branches, trunk status, commit SHA, branch relationships, branch metadata model
**Files**: core/branch_metadata.py
**Child packages**: core
**Description**: Data structure for storing metadata about git-tracked branches including parent/child relationships, trunk status, and commit information.

## [Global Configuration Operations]
**Search phrases**: config file, workstacks root, settings, preferences, shell setup, PR display options, Graphite preference,