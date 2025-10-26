# Semantic Lookup Index

## Child Packages

- **collectors** (collectors/): Plugin-based architecture for gathering status information from various sources (git, GitHub, Graphite, plan files)
- **models** (models/): Frozen dataclasses representing different aspects of repository and development environment status
- **renderers** (renderers/): Pluggable rendering system for displaying status information to users in various formats

## Status Orchestration and Coordination

**Search phrases**: status orchestration, status collection, parallel collection, status assembly, status coordination, collect all status, gather status information, status aggregation
**Files**: orchestrator.py
**Description**: Central orchestrator that coordinates multiple status collectors, runs them in parallel with timeouts, and assembles final status data. Handles error boundaries and graceful degradation when collectors fail or timeout.

## Parallel Status Collection with Timeouts

**Search phrases**: parallel collection, concurrent collection, thread pool, timeout handling, collection timeouts, responsive status, non-blocking collection, collection failures
**Files**: orchestrator.py
**Description**: Implements parallel status collection using ThreadPoolExecutor with per-collector timeouts to ensure responsive output even when some collectors are slow or fail. Failed collectors return None rather than blocking the entire command.

## Worktree Information Gathering

**Search phrases**: worktree metadata, worktree information, worktree details, worktree name, worktree path, worktree branch, root worktree detection, current worktree
**Files**: orchestrator.py
**Description**: Determines and collects basic worktree information including name, path, branch, and whether it's the root worktree. Handles path resolution safely with existence checks.

## Related Worktrees Discovery

**Search phrases**: related worktrees, other worktrees, worktree list, multiple worktrees, worktree relationships, worktree enumeration, sibling worktrees
**Files**: orchestrator.py
**Description**: Discovers and lists other worktrees in the same repository, excluding the current worktree. Provides information about related worktrees including their branches and root status.

## Status Data Models

**Search phrases**: status data structures, status models, status information types, status schema, data models, status container
**Files**: models/
**Child packages**: models
**Description**: See models package documentation for comprehensive status data model definitions including GitStatus, PullRequestStatus, StackPosition, PlanStatus, and the root StatusData container.

## Status Collection Framework

**Search phrases**: status collector, information gathering, status data collection, collector pattern, extensible collectors, plugin architecture
**Files**: collectors/
**Child packages**: collectors
**Description**: See collectors package documentation for the abstract collector pattern and concrete implementations for git, GitHub PRs, Graphite stacks, and plan files.

## Status Rendering and Display

**Search phrases**: render status, display status, format status output, show status information, status visualization, console output, terminal display, status formatting
**Files**: renderers/
**Child packages**: renderers
**Description**: See renderers package documentation for pluggable rendering system with text-based console output implementation using Click for styling.

## Error Handling and Graceful Degradation

**Search phrases**: error handling, graceful failure, collection failures, timeout handling, error boundaries, optional data, fallback mechanisms, partial status
**Files**: orchestrator.py
**Description**: Implements error boundaries at the orchestration level where individual collector failures or timeouts don't prevent the entire status command from completing. Failed collectors return None, allowing partial status collection.

## Git Operations Integration

**Search phrases**: git operations, git integration, git context, git repository operations, branch information, worktree git operations
**Files**: orchestrator.py
**Description**: Uses WorkstackContext's git_ops to access git operations for determining current branch and listing worktrees. Integrates with the broader git operations system.

## Status Command Entry Point

**Search phrases**: status command, status entry point, status module, status package, status initialization
**Files**: __init__.py
**Description**: Package initialization that exports the StatusOrchestrator as the primary public API for the status command functionality.