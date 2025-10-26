# Semantic Lookup Index

## Data Models for Status Information
**Search phrases**: status data models, status information structures, data classes, status container, status schema
**Files**: status_data.py, __init__.py
**Description**: Core data model definitions that represent various aspects of repository and development environment status. These are frozen dataclasses designed to be immutable and serializable.

## Worktree Information
**Search phrases**: worktree details, git worktree, worktree metadata, worktree path, worktree branch, worktree name
**Files**: status_data.py
**Description**: Represents basic information about a git worktree including its name, path, branch, and whether it's the root worktree.

## Git Repository Status
**Search phrases**: git status, repository status, branch status, git changes, staged files, modified files, untracked files, commit history, ahead behind
**Files**: status_data.py
**Description**: Comprehensive git repository status including branch information, cleanliness, commit counts relative to upstream, file changes (staged/modified/untracked), and recent commit history.

## Commit Information
**Search phrases**: commit details, commit metadata, commit author, commit message, commit hash, commit date, git commit
**Files**: status_data.py
**Description**: Represents individual commit information including SHA, message, author, and date. Used as part of recent commit history in git status.

## Stack Position and Hierarchy
**Search phrases**: graphite stack, stack position, branch hierarchy, parent branch, child branches, trunk branch, stack structure
**Files**: status_data.py
**Description**: Represents the position of a branch within a Graphite stack, including the full stack list, current branch, parent/child relationships, and trunk status.

## Pull Request Status
**Search phrases**: pull request, PR status, PR checks, PR reviews, draft PR, PR merge readiness, PR number, PR title, PR state
**Files**: status_data.py
**Description**: Represents pull request information including number, title, state, draft status, URL, check results, reviews, and merge readiness.

## Environment Status
**Search phrases**: environment variables, environment configuration, environment status
**Files**: status_data.py
**Description**: Represents environment variables status as a dictionary of key-value pairs.

## Dependency Status
**Search phrases**: dependencies, dependency updates, outdated dependencies, language dependencies, dependency health, package updates
**Files**: status_data.py
**Description**: Represents dependency status for various language ecosystems including language type, update status, count of outdated packages, and detailed information.

## Plan File Status
**Search phrases**: plan file, .PLAN.md, plan status, plan summary, plan content, plan existence
**Files**: status_data.py
**Description**: Represents the status of a .PLAN.md file including existence, path, summary, line count, and first lines of content.

## Complete Status Container
**Search phrases**: all status information, complete status, status aggregation, status snapshot, full status report
**Files**: status_data.py
**Description**: Top-level container that aggregates all status information including worktree info, git status, stack position, PR status, environment, dependencies, plan status, and related worktrees.

## Model Exports and Public API
**Search phrases**: public API, exported models, model imports, available models
**Files**: __init__.py
**Description**: Defines the public API for the models package, exporting all data model classes for use by other modules.