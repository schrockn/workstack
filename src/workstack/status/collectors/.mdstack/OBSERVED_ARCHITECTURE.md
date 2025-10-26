# Observed Architecture

## Overview

The `collectors` scope implements a plugin-based architecture for gathering status information about worktrees. Each collector is a specialized component responsible for extracting a specific type of status data (git information, GitHub PRs, Graphite stack position, plan files). The architecture uses an abstract base class pattern to define a consistent interface that all collectors must implement, enabling extensibility and composition.

## Module Organization

### base.py
**Responsibility**: Defines the abstract interface that all status collectors must implement
**Key exports**: `StatusCollector` (abstract base class)
**Pattern**: Abstract Base Class (ABC) defining a contract for all collector implementations

### git.py
**Responsibility**: Collects git repository status information including branch, file changes, commit history, and ahead/behind counts
**Key exports**: `GitStatusCollector`
**Dependencies**: Uses `ctx.git_ops` for git operations

### github.py
**Responsibility**: Collects GitHub pull request information for the current branch, with fallback logic between Graphite and GitHub APIs
**Key exports**: `GitHubPRCollector`
**Dependencies**: Uses `ctx.graphite_ops` and `ctx.github_ops` for PR data

### graphite.py
**Responsibility**: Collects Graphite stack position information, determining parent/child relationships and trunk status
**Key exports**: `GraphiteStackCollector`
**Dependencies**: Uses `ctx.graphite_ops` for stack operations

### plan.py
**Responsibility**: Collects information about `.PLAN.md` files including existence, content summary, and line count
**Key exports**: `PlanFileCollector`
**Pattern**: File-based collector with text parsing

### __init__.py
**Responsibility**: Package initialization and public API definition
**Key exports**: `StatusCollector`, `GitStatusCollector`

## Core Abstractions

### StatusCollector
**Location**: base.py
**Purpose**: Abstract base class defining the interface for all status collectors
**Type**: Abstract Base Class (ABC)
**Key Methods**:
- `name` (property): Returns a string identifier for the collector
- `is_available(ctx, worktree_path)`: Determines if the collector can operate in the given context
- `collect(ctx, worktree_path, repo_root)`: Performs the actual data collection and returns structured status data

**Design Pattern**: Template Method pattern - subclasses implement the abstract methods to define specific collection behavior

### GitStatusCollector
**Location**: git.py
**Purpose**: Concrete collector for git repository status
**Returns**: `GitStatus` object containing branch, file changes, commit history, and sync status

### GitHubPRCollector
**Location**: github.py
**Purpose**: Concrete collector for GitHub pull request information
**Returns**: `PullRequestStatus` object with PR metadata and merge readiness
**Special Pattern**: Implements fallback logic - tries Graphite first (fast), falls back to GitHub API

### GraphiteStackCollector
**Location**: graphite.py
**Purpose**: Concrete collector for Graphite stack position information
**Returns**: `StackPosition` object with stack hierarchy and current position
**Availability**: Only available when Graphite is enabled in global config

### PlanFileCollector
**Location**: plan.py
**Purpose**: Concrete collector for `.PLAN.md` file information
**Returns**: `PlanStatus` object with file metadata and content preview
**Special Pattern**: Gracefully handles missing files by returning a `PlanStatus` with `exists=False`

## Architectural Patterns

### Plugin Architecture
Each collector is a self-contained plugin that:
1. Declares its availability via `is_available()` - enabling conditional activation
2. Implements collection logic independently in `collect()`
3. Returns structured data via domain models (GitStatus, PullRequestStatus, etc.)

This allows new collectors to be added without modifying existing code.

### Availability Checking Pattern
Collectors implement `is_available()` to check preconditions before collection:
- **GitStatusCollector**: Checks if worktree exists
- **GitHubPRCollector**: Checks if PR info is enabled in config and worktree exists
- **GraphiteStackCollector**: Checks if Graphite is enabled in config and worktree exists
- **PlanFileCollector**: Checks if `.PLAN.md` file exists

This pattern allows orchestrators to skip unavailable collectors without errors.

### Graceful Degradation
- **GitHubPRCollector**: Falls back from Graphite to GitHub API if Graphite data unavailable
- **PlanFileCollector**: Returns a valid `PlanStatus` with `exists=False` rather than raising errors
- All collectors return `None` on collection failure rather than raising exceptions

### Context Injection Pattern
All collectors receive a `WorkstackContext` object providing access to:
- `git_ops`: Git operations
- `github_ops`: GitHub API operations
- `graphite_ops`: Graphite operations
- `global_config_ops`: Configuration access

This centralizes dependencies and enables testing/mocking.

## Data Flow

1. **Orchestration Layer** (external to this scope) calls collectors
2. **Availability Check**: Orchestrator calls `is_available()` on each collector
3. **Conditional Collection**: Only available collectors proceed to `collect()`
4. **Data Gathering**: Collector uses context operations to fetch data from git, APIs, or filesystem
5. **Data Transformation**: Raw data is transformed into domain models (GitStatus, PullRequestStatus, etc.)
6. **Return**: Structured data returned to orchestrator or `None` on failure
7. **Composition**: Orchestrator combines results from multiple collectors into unified status view

## Dependencies

### Internal Dependencies
- `workstack.core.context.WorkstackContext`: Provides access to operations
- `workstack.status.models.status_data`: Domain models for status information
  - `GitStatus`, `CommitInfo`, `PullRequestStatus`, `StackPosition`, `PlanStatus`

### External Dependencies
- `pathlib.Path`: For filesystem operations
- `abc.ABC, abstractmethod`: For abstract base class pattern

### Context Operations Used
- `ctx.git_ops`: Git repository operations
- `ctx.github_ops`: GitHub API operations
- `ctx.graphite_ops`: Graphite stack operations
- `ctx.global_config_ops`: Configuration queries

## Extension Points

### Adding a New Collector

To add a new status collector:

1. **Create new file** in this scope (e.g., `myfeature.py`)
2. **Implement StatusCollector**:
   ```python
   class MyFeatureCollector(StatusCollector):
       @property
       def name(self) -> str:
           return "myfeature"
       
       def is_available(self, ctx, worktree_path) -> bool:
           # Check preconditions
           return True
       
       def collect(self, ctx, worktree_path, repo_root):
           # Gather data using ctx operations
           # Return domain model or None
   ```
3. **Export in __init__.py**: Add to `__all__` list
4. **Create domain model** in `workstack.status.models.status_data` if needed
5. **Register with orchestrator** (external to this scope)

### Modifying Collector Behavior

- **Change availability logic**: Modify `is_available()` method
- **Change data collection**: Modify `collect()` method
- **Add new fields**: Extend corresponding domain model in `status_data.py`
- **Change fallback strategy**: Modify fallback logic in `collect()` (e.g., GitHubPRCollector)

## Key Concepts Explained

### Worktree
A git worktree is a working directory associated with a repository. Collectors operate on a specific worktree path to gather localized status information.

### Availability vs. Collection
- **Availability**: Whether a collector can potentially run (preconditions met)
- **Collection**: Whether data was successfully gathered (may return None even if available)

This separation allows orchestrators to skip unavailable collectors efficiently.

### Graceful Failure
Collectors are designed to fail gracefully:
- Return `None` rather than raise exceptions
- Return valid objects with `exists=False` or empty fields rather than error states
- This allows partial status collection even when some collectors fail

### Stack Position (Graphite)
In Graphite, branches form a stack hierarchy where:
- **Trunk**: The base branch (index 0)
- **Parent**: The branch this branch is based on
- **Children**: Branches based on this branch
- **Stack**: Ordered list of branches from trunk to leaf

## Common Agent Tasks

### Understanding Collector Behavior
1. Check `is_available()` to understand when a collector runs
2. Review `collect()` to see what data it gathers and how
3. Check the return type (domain model) to understand output structure

### Adding a New Status Type
1. Create domain model in `workstack.status.models.status_data`
2. Create collector class inheriting from `StatusCollector`
3. Implement the three required methods
4. Export in `__init__.py`

### Debugging Collection Failures
1. Check if collector `is_available()` - if False, preconditions not met
2. Check `collect()` logic for error handling
3. Verify context operations (git_ops, github_ops, etc.) are working
4. Check if collector returns `None` vs. partial data

### Modifying Collection Logic
1. Locate the specific collector file
2. Modify `collect()` method to change data gathering
3. Update return type if adding new fields
4. Update domain model if needed
5. Test with `is_available()` to ensure preconditions still valid

### Implementing Fallback Strategies
See `GitHubPRCollector` for pattern:
1. Try primary source first
2. Check if data available
3. Fall back to secondary source if needed
4. Return best available data or None