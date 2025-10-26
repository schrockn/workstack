# Observed Architecture

## Overview

The `models` scope defines the data structures for the status command system. It provides a comprehensive set of frozen dataclasses that represent different aspects of a development environment's state, including git information, pull requests, dependencies, and project planning. These models serve as the contract between status data collectors and the status command's presentation layer.

## Module Organization

### status_data.py
**Responsibility**: Defines all core data models for status information collection and representation
**Key exports**: Nine frozen dataclasses representing different status domains

### __init__.py
**Responsibility**: Exposes the public API of the models package
**Key exports**: All nine dataclasses via `__all__`

## Core Abstractions

### WorktreeInfo
**Location**: status_data.py
**Purpose**: Represents a git worktree with its basic metadata
**Type**: Frozen dataclass
**Fields**: name, path, branch, is_root
**Usage**: Used to identify and track individual worktrees in a multi-worktree setup

### CommitInfo
**Location**: status_data.py
**Purpose**: Encapsulates metadata about a single git commit
**Type**: Frozen dataclass
**Fields**: sha, message, author, date
**Usage**: Aggregated in GitStatus to provide recent commit history

### GitStatus
**Location**: status_data.py
**Purpose**: Comprehensive snapshot of a git repository's state
**Type**: Frozen dataclass
**Fields**: branch, clean, ahead, behind, staged_files, modified_files, untracked_files, recent_commits
**Usage**: Core model for git-related status information; includes both state flags and file tracking

### StackPosition
**Location**: status_data.py
**Purpose**: Represents a branch's position within a Graphite stack hierarchy
**Type**: Frozen dataclass
**Fields**: stack, current_branch, parent_branch, children_branches, is_trunk
**Usage**: Models the relationship between branches in a stacked workflow

### PullRequestStatus
**Location**: status_data.py
**Purpose**: Represents the state of a pull request with merge readiness information
**Type**: Frozen dataclass
**Fields**: number, title, state, is_draft, url, checks_passing, reviews, ready_to_merge
**Usage**: Provides PR metadata with optional fields for data sources that don't provide all information

### EnvironmentStatus
**Location**: status_data.py
**Purpose**: Captures environment variables relevant to the project
**Type**: Frozen dataclass
**Fields**: variables (dict)
**Usage**: Simple key-value store for environment state

### DependencyStatus
**Location**: status_data.py
**Purpose**: Tracks dependency health for a specific language ecosystem
**Type**: Frozen dataclass
**Fields**: language, up_to_date, outdated_count, details
**Usage**: Extensible model supporting multiple language ecosystems

### PlanStatus
**Location**: status_data.py
**Purpose**: Represents the state of a .PLAN.md file in the project
**Type**: Frozen dataclass
**Fields**: exists, path, summary, line_count, first_lines
**Usage**: Provides project planning document metadata and preview

### StatusData
**Location**: status_data.py
**Purpose**: Root container aggregating all status information into a single coherent structure
**Type**: Frozen dataclass
**Fields**: worktree_info, git_status, stack_position, pr_status, environment, dependencies, plan, related_worktrees
**Usage**: The primary data structure passed between status collectors and presentation layers; optional fields allow partial status collection

## Architectural Patterns

### Frozen Dataclasses
All models use `@dataclass(frozen=True)` to ensure immutability. This pattern:
- Prevents accidental mutation of status data
- Makes models safe to cache or share across components
- Enables use as dictionary keys if needed
- Signals that these are value objects, not mutable entities

### Optional Fields
Many dataclasses use `| None` type hints to indicate optional information:
- `GitStatus.branch`, `StackPosition.parent_branch`, `PullRequestStatus.title`
- `PullRequestStatus.checks_passing`, `PullRequestStatus.reviews`
- `DependencyStatus.details`, `PlanStatus.path`, `PlanStatus.summary`

This pattern accommodates data sources that may not provide complete information.

### Hierarchical Composition
StatusData acts as a root container that composes multiple domain-specific models:
- Git domain: GitStatus, StackPosition
- PR domain: PullRequestStatus
- Environment domain: EnvironmentStatus
- Dependency domain: DependencyStatus
- Planning domain: PlanStatus
- Worktree domain: WorktreeInfo, related_worktrees

### List-Based Collections
Models use `list[T]` for collections:
- `GitStatus.staged_files`, `modified_files`, `untracked_files`, `recent_commits`
- `StackPosition.stack`, `children_branches`
- `PullRequestStatus.reviews`
- `PlanStatus.first_lines`
- `StatusData.related_worktrees`

This allows flexible collection sizes and maintains order.

## Data Flow

1. **Collection Phase**: Status collectors (external to this scope) gather information from various sources (git, GitHub API, filesystem, etc.)
2. **Model Construction**: Collectors instantiate these dataclasses with collected data
3. **Aggregation**: Individual status models are composed into a StatusData container
4. **Presentation Phase**: The status command's presentation layer receives StatusData and formats it for display
5. **Immutability Guarantee**: Frozen dataclasses ensure the status snapshot remains consistent throughout processing

## Dependencies

### External Dependencies
- `dataclasses`: Python standard library for dataclass decorator
- `pathlib.Path`: Standard library for filesystem paths

### Internal Dependencies
- No internal dependencies; this is a leaf module in the dependency graph
- Imported by: status command presentation and collection layers (external to this scope)

## Extension Points

### Adding New Status Domains
To add a new status category:
1. Create a new frozen dataclass in status_data.py following the existing pattern
2. Add an optional field to StatusData to include the new model
3. Export the new class in __init__.py

### Supporting Additional Data Sources
The optional field pattern (`| None`) allows new data sources to provide partial information:
- A data source can populate only the fields it can provide
- Consumers check for `None` before using optional fields
- No breaking changes required when adding new data sources

### Language Ecosystem Support
DependencyStatus is designed to support multiple languages:
- The `language` field identifies the ecosystem
- New ecosystems can be added by creating DependencyStatus instances with different language values
- The `details` field provides ecosystem-specific information

## Key Concepts Explained

### Worktree
A git worktree is an alternative working directory linked to the same repository. The models support tracking multiple worktrees through WorktreeInfo and the `related_worktrees` list in StatusData.

### Stack Position (Graphite)
Graphite is a tool for managing stacked pull requests. StackPosition models the hierarchical relationship between branches, tracking parent-child relationships and trunk status.

### Pull Request Readiness
The `ready_to_merge` field in PullRequestStatus is a computed boolean indicating whether a PR is in a state suitable for merging (typically: not draft, checks passing, approved).

### Status Optionality
Many fields are optional because status information may come from different sources with varying capabilities. A local-only status collector might not have PR information; a CI system might not have environment variables.

## Common Agent Tasks

### Retrieving Specific Status Information
Access nested models through StatusData:
```python
status_data.git_status.branch  # Current branch
status_data.pr_status.ready_to_merge  # PR merge readiness
status_data.plan.first_lines  # Project plan preview
```

### Handling Optional Information
Check for None before accessing optional fields:
```python
if status_data.git_status and status_data.git_status.branch:
    # Use branch information
if status_data.pr_status and status_data.pr_status.reviews:
    # Process reviews
```

### Adding a New Status Field
1. Determine if it belongs in an existing model or needs a new one
2. Add the field to the appropriate dataclass with proper type hints
3. Update StatusData if creating a new top-level domain
4. Update __init__.py exports if adding a new class
5. Update status collectors to populate the new field

### Creating a StatusData Instance
Collectors build StatusData by instantiating each component:
```python
status = StatusData(
    worktree_info=WorktreeInfo(...),
    git_status=GitStatus(...),
    stack_position=StackPosition(...),
    pr_status=PullRequestStatus(...),
    environment=EnvironmentStatus(...),
    dependencies=DependencyStatus(...),
    plan=PlanStatus(...),
    related_worktrees=[...]
)
```