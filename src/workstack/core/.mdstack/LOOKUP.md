# Semantic Lookup Index

## [Git Operations]
**Search phrases**: git commands, branch management, worktree operations, checkout, commit information, file status, branch tracking
**Files**: gitops.py
**Description**: Abstract interface and production implementation for git operations including worktree management, branch operations, commit queries, and file status tracking.

## [GitHub Operations]
**Search phrases**: pull request information, PR status, GitHub API, CI checks, check status, PR list, branch PR mapping
**Files**: github_ops.py
**Description**: Abstract interface and production implementation for GitHub operations including PR fetching, status queries, and CI check status determination.

## [Graphite Operations]
**Search phrases**: Graphite CLI, gt commands, branch stack, branch metadata, PR info cache, branch relationships, trunk detection, sync
**Files**: graphite_ops.py
**Description**: Abstract interface and production implementation for Graphite operations including branch stack traversal, cache parsing, PR info retrieval, and synchronization.

## [Branch Metadata]
**Search phrases**: branch information, parent branch, child branches, trunk status, commit SHA, branch relationships
**Files**: branch_metadata.py
**Description**: Data structure for storing metadata about git-tracked branches including parent/child relationships, trunk status, and commit information.

## [Global Configuration]
**Search phrases**: config file, workstacks root, settings, preferences, shell setup, PR display options, Graphite preference
**Files**: global_config_ops.py
**Description**: Abstract interface and production implementation for managing global workstack configuration stored in ~/.workstack/config.toml.

## [Shell Operations]
**Search phrases**: shell detection, shell configuration, tool availability, PATH lookup, bash, zsh, fish
**Files**: shell_ops.py
**Description**: Abstract interface and production implementation for detecting the current shell and checking if command-line tools are installed.

## [File Utilities]
**Search phrases**: markdown parsing, plan file, extract heading, frontmatter
**Files**: file_utils.py
**Description**: Utility functions for file operations including extracting titles from markdown plan files with YAML frontmatter.

## [Dependency Injection Context]
**Search phrases**: application context, dependency injection, context creation, dry-run mode, service initialization
**Files**: context.py
**Description**: Immutable context dataclass that holds all dependencies for workstack operations, with factory function for creating production or dry-run contexts.

## [Dry-Run Mode]
**Search phrases**: dry run, preview changes, no-op operations, print intentions, destructive operations, safe mode
**Files**: gitops.py, github_ops.py, graphite_ops.py, global_config_ops.py
**Description**: Wrapper implementations that intercept destructive operations and print what would happen instead of executing them, enabling safe preview of changes.

## [JSON Parsing]
**Search phrases**: JSON parsing, Graphite cache, PR info parsing, JSON validation, error handling
**Files**: graphite_ops.py, github_ops.py
**Description**: Functions for parsing and validating JSON from Graphite cache files and GitHub API responses.

## [URL Conversion]
**Search phrases**: URL parsing, Graphite URL, GitHub URL, URL conversion, PR URL
**Files**: graphite_ops.py, github_ops.py
**Description**: Functions for parsing and converting between Graphite and GitHub URLs for pull requests.

## [Abstract Base Classes]
**Search phrases**: interface definition, abstract methods, contract, implementation pattern
**Files**: gitops.py, github_ops.py, graphite_ops.py, global_config_ops.py, shell_ops.py
**Description**: Abstract base classes (ABC) that define interfaces for all operations, enabling multiple implementations and dependency injection.

## [Production Implementations]
**Search phrases**: real implementation, subprocess execution, actual commands, production code
**Files**: gitops.py (RealGitOps), github_ops.py (RealGitHubOps), graphite_ops.py (RealGraphiteOps), global_config_ops.py (RealGlobalConfigOps), shell_ops.py (RealShellOps)
**Description**: Production implementations that execute actual commands via subprocess or system calls.

## [Worktree Management]
**Search phrases**: git worktree, add worktree, remove worktree, move worktree, list worktrees, worktree path
**Files**: gitops.py
**Description**: Operations for managing git worktrees including creation, removal, movement, and listing.

## [Branch Stack Traversal]
**Search phrases**: linear stack, branch chain, ancestors, descendants, trunk to leaf, parent-child traversal
**Files**: graphite_ops.py
**Description**: Algorithm for building the linear chain of branches from trunk to leaf, including all ancestors and descendants of a given branch.

## [CI Check Status]
**Search phrases**: check status, CI status, test results, check rollup, passing checks, failing checks
**Files**: github_ops.py
**Description**: Logic for determining overall CI check status from GitHub API responses, handling various check states and conclusions.

## [Configuration Caching]
**Search phrases**: lazy loading, cache invalidation, config cache, performance optimization
**Files**: global_config_ops.py
**Description**: Caching mechanism for global configuration to avoid repeated disk reads, with cache invalidation on writes.

## [Error Handling]
**Search phrases**: error boundaries, exception handling, graceful degradation, missing files, invalid JSON
**Files**: graphite_ops.py, github_ops.py, gitops.py
**Description**: Error handling patterns including try/except boundaries for CLI availability, file existence checks, and JSON validation.