# Semantic Lookup Index

## Child Packages
- **[commands]** (commands/): Click command implementations for all user-facing workflows including worktree creation, navigation, removal, and configuration management
- **[shell_integration]** (shell_integration/): Shell wrapper and handler for integrating workstack with bash/zsh/fish shells

## [Worktree Creation and Setup]
**Search phrases**: create worktree, new worktree, scaffold environment, initialize branch, setup branch, create branch, worktree initialization, branch creation, environment setup, post-create hooks, .env file generation, plan file handling, branch sanitization
**Files**: commands/create.py, commands/init.py, config.py, activation.py
**Child packages**: commands
**Description**: Creating new worktrees with branch management, environment variable templating, post-create command execution, and plan file integration. Includes branch sanitization, worktree naming conventions, and configuration-driven setup.

## [Worktree Navigation and Switching]
**Search phrases**: switch worktree, activate worktree, change directory, navigate branches, jump to branch, move up stack, move down stack, graphite navigation, branch hierarchy navigation, worktree activation, shell integration activation, directory change
**Files**: commands/switch.py, commands/up.py, commands/down.py, commands/jump.py, activation.py, shell_utils.py
**Child packages**: commands
**Description**: Switching between worktrees and branches with automatic environment activation. Includes Graphite stack navigation (up/down), branch jumping, and shell script generation for directory changes and environment setup.

## [Worktree Removal and Cleanup]
**Search phrases**: delete worktree, remove worktree, cleanup worktrees, merged branches, closed PRs, garbage collection, branch deletion, stack deletion, worktree pruning, stale worktrees
**Files**: commands/remove.py, commands/gc.py, commands/sync.py
**Child packages**: commands
**Description**: Removing worktrees and associated branches, identifying merged/closed PRs for cleanup, garbage collection of stale worktrees, and automatic pruning of git metadata.

## [Worktree Movement and Reorganization]
**Search phrases**: move branch, swap branches, reorganize worktrees, move between worktrees, branch relocation, worktree swapping, branch movement, rename worktree
**Files**: commands/move.py, commands/rename.py
**Child packages**: commands
**Description**: Moving branches between worktrees, swapping branch locations, renaming worktrees, and updating associated metadata (.env files, git references).

## [Worktree Listing and Inspection]
**Search phrases**: list worktrees, show worktrees, worktree status, branch stacks, graphite stacks, PR information, CI checks, plan files, worktree overview, tree visualization, hierarchy display
**Files**: commands/list.py, commands/tree.py, commands/status.py, tree.py
**Child packages**: commands
**Description**: Displaying worktrees with branch information, Graphite stack visualization, PR status indicators, CI check results, and plan file summaries. Includes tree-based hierarchy visualization and detailed status reporting.

## [Graphite Integration]
**Search phrases**: graphite branches, graphite metadata, branch relationships, parent-child branches, trunk branches, stack information, graphite cache, branch hierarchy, stacked workflow, dependent branches
**Files**: graphite.py, tree.py, commands/gt.py, commands/list.py, commands/tree.py, commands/up.py, commands/down.py, commands/jump.py, commands/switch.py
**Child packages**: commands
**Description**: Machine-readable access to Graphite metadata, branch hierarchy visualization, parent-child relationship navigation, and stack-based operations. Includes tree formatting, branch metadata queries, and cache file parsing.

## [Configuration Management]
**Search phrases**: config get, config set, config list, global configuration, repository configuration, environment variables, post-create commands, configuration keys, settings management, config file, TOML configuration
**Files**: config.py, commands/config.py, commands/init.py
**Child packages**: commands
**Description**: Reading and writing global and repository-level configuration, managing environment variable templates, post-create command definitions, and configuration key validation. Includes TOML file parsing and hierarchical key access.

## [Shell Integration and Activation]
**Search phrases**: shell completion, shell wrapper, bash completion, zsh completion, fish completion, auto-activation, environment activation, virtual environment, .env loading, shell integration setup, shell detection, activation script
**Files**: commands/completion.py, commands/shell_integration.py, commands/init.py, activation.py, shell_utils.py, shell_integration/handler.py
**Child packages**: commands, shell_integration
**Description**: Shell completion script generation for bash/zsh/fish, shell wrapper functions for automatic worktree activation, environment variable loading, and virtual environment setup. Includes shell detection, integration setup instructions, and script generation.

## [Synchronization with Graphite]
**Search phrases**: sync with graphite, gt sync, branch synchronization, merged branch cleanup, automatic cleanup, force sync, dry-run sync, branch deletion automation, sync workflow
**Files**: commands/sync.py
**Child packages**: commands
**Description**: Synchronizing with Graphite, identifying and removing merged/closed worktrees, automatic branch cleanup with confirmation, and fallback to root worktree after cleanup.

## [Repository Context Discovery]
**Search phrases**: discover repository, find git root, repository detection, workstacks directory, worktree path resolution, repository context, git root detection, repo initialization
**Files**: core.py, commands/init.py, commands/create.py, commands/list.py, commands/tree.py, commands/switch.py, commands/remove.py, commands/move.py, commands/rename.py, commands/sync.py, commands/gc.py, commands/status.py, commands/up.py, commands/down.py, commands/jump.py
**Child packages**: commands
**Description**: Discovering repository root, locating workstacks directories, resolving worktree paths, and validating repository context for all operations. Includes handling of git worktrees and common directory detection.

## [Dry-Run and Safety Features]
**Search phrases**: dry-run mode, preview operations, destructive operations, confirmation prompts, force flag, safety checks, uncommitted changes detection, operation planning
**Files**: commands/remove.py, commands/move.py, commands/rename.py, commands/sync.py, core.py
**Child packages**: commands
**Description**: Dry-run mode for previewing destructive operations, confirmation prompts for user safety, force flags to skip confirmpts, and detection of uncommitted changes before operations.

## [Error Handling and Validation]
**Search phrases**: input validation, error messages, branch validation, worktree validation, reserved names, detached HEAD, git errors, graphite errors, validation, error boundary
**Files**: commands/create.py, commands/switch.py, commands/remove.py, commands/move.py, commands/rename.py, commands/jump.py, commands/up.py, commands/down.py, core.py
**Child packages**: commands
**Description**: Comprehensive input validation, user-friendly error messages, detection of edge cases (detached HEAD, reserved names, missing branches), and graceful error handling with error boundary patterns.

## [Plan File Management]
**Search phrases**: plan files, .PLAN.md, plan extraction, plan title, plan file handling, plan-based worktree creation, plan summary
**Files**: commands/create.py, commands/list.py, commands/status.py
**Child packages**: commands
**Description**: Handling plan markdown files (.PLAN.md), extracting plan titles, deriving worktree names from plan filenames, and displaying plan summaries in worktree listings.

## [PR Status and GitHub Integration]
**Search phrases**: pull request status, PR information, merged PRs, closed PRs, PR checks, CI status, GitHub API, PR links, draft PRs, PR metadata
**Files**: commands/list.py, commands/gc.py, commands/sync.py
**Child packages**: commands
**Description**: Fetching PR status from GitHub, displaying PR information with emoji indicators, checking CI status, identifying merged/closed PRs for cleanup, and generating clickable PR links.

## [Branch Naming and Sanitization]
**Search phrases**: branch name sanitization, worktree name sanitization, safe branch names, branch component sanitization, name validation, special character handling, filename sanitization
**Files**: commands/create.py, commands/rename.py, core.py
**Child packages**: commands
**Description**: Sanitizing branch and worktree names for safe filesystem and git usage, handling special characters, collapsing separators, and providing sensible defaults for empty results.

## [Environment Variable Templating]
**Search phrases**: .env file generation, environment templates, variable substitution, dotenv files, environment configuration, template variables, environment setup
**Files**: commands/create.py, commands/rename.py, config.py, activation.py
**Child packages**: commands
**Description**: Generating .env files from configuration templates with variable substitution (worktree_path, repo_root, name), quoting values for dotenv compatibility, and loading environment variables.

## [Worktree Metadata and Git Operations]
**Search phrases**: git worktree operations, worktree metadata, branch checkout, branch creation, detached HEAD, worktree pruning, git metadata management, git common directory
**Files**: commands/create.py, commands/remove.py, commands/move.py, commands/switch.py, commands/up.py, commands/down.py, commands/jump.py, core.py
**Child packages**: commands
**Description**: Low-level git worktree operations including creation, removal, branch checkout, metadata pruning, and handling edge cases like detached HEAD states and git common directory resolution.

## [Script Generation and Temp Files]
**Search phrases**: activation scripts, shell scripts, temp file generation, script output, cd scripts, environment activation scripts, script metadata, script cleanup
**Files**: commands/create.py, commands/switch.py, commands/up.py, commands/down.py, commands/jump.py, commands/sync.py, commands/shell_integration.py, activation.py, shell_utils.py
**Child packages**: commands, shell_integration
**Description**: Generating shell activation scripts for directory changes and environment setup, writing scripts to temporary files, managing script lifecycle, and outputting script paths for shell wrapper execution.

## [Initialization and Setup]
**Search phrases**: workstack initialization, first-time setup, global config creation, repository setup, preset selection, shell setup, graphite detection, initial configuration
**Files**: commands/init.py, cli.py, config.py
**Child packages**: commands
**Description**: First-time workstack initialization, global configuration creation, repository-level config scaffolding, preset-based configuration templates, and shell integration setup.

## [Preset Configuration]
**Search phrases**: configuration presets, preset templates, auto-detection, preset selection, project-specific presets, generic presets, preset rendering
**Files**: commands/init.py, config.py
**Child packages**: commands
**Description**: Discovering and applying configuration presets, auto-detecting appropriate presets based on repository characteristics, and rendering preset templates with variable substitution.

## [Tree Visualization]
**Search phrases**: tree display, ASCII tree, tree rendering, box-drawing characters, tree structure, hierarchy visualization, branch tree, worktree tree, tree formatting
**Files**: tree.py, commands/tree.py, commands/gt.py
**Child packages**: commands
**Description**: Building and rendering tree structures showing worktrees and their Graphite dependency relationships. Uses Unicode box-drawing characters for visual hierarchy and supports colorized output for current worktree highlighting.

## [CLI Entry Point and Command Registration]
**Search phrases**: CLI entry point, command registration, command group, click commands, CLI initialization, command dispatcher, main entry point
**Files**: cli.py, commands/__init__.py
**Child packages**: commands
**Description**: Main CLI entry point, command registration, context initialization, and command group organization. Handles version display and help option configuration.

## [Debug Logging]
**Search phrases**: debug logging, debug mode, debug output, troubleshooting, debug file, debug information, WORKSTACK_DEBUG
**Files**: debug.py
**Description**: Debug logging functionality when WORKSTACK_DEBUG=1 is set. Debug logs are written to /tmp/workstack-debug.log for troubleshooting and development.

## [Shell Wrapper Coordination]
**Search phrases**: shell wrapper, shell integration handler, passthrough marker, shell request handling, shell coordination, wrapper execution
**Files**: commands/shell_integration.py, shell_integration/handler.py, shell_utils.py
**Child packages**: commands, shell_integration
**Description**: Unified entry point for shell integration wrappers, passthrough marker support for shell wrapper coordination, and script execution coordination between workstack and shell wrappers.

## [Worktree Path Resolution]
**Search phrases**: worktree path, path resolution, worktree directory, workstacks directory, path validation, path construction, directory structure
**Files**: core.py, commands/create.py, commands/list.py, commands/switch.py, commands/move.py, commands/rename.py
**Child packages**: commands
**Description**: Resolving worktree paths within workstacks directory, constructing absolute paths, validating path safety, and handling special cases like root worktree.

## [Current Working Directory Recovery]
**Search phrases**: cwd recovery, directory recovery, current directory, working directory preservation, directory change fallback, cwd restoration
**Files**: commands/prepare_cwd_recovery.py, shell_utils.py
**Child packages**: commands
**Description**: Pre-generating recovery scripts for passthrough flows to handle edge cases where current working directory becomes invalid after worktree operations.