# Semantic Lookup Index

## Concepts and Capabilities

### Status Collection Framework
**Search phrases**: status collector, information gathering, status data collection, collector pattern, extensible collectors
**Files**: base.py
**Description**: Abstract base class defining the collector pattern for gathering status information. Each collector is responsible for a specific type of status data and handles errors gracefully.

### Git Repository Status
**Search phrases**: git status, repository information, branch tracking, commit history, file changes, staged files, modified files, untracked files, ahead behind commits
**Files**: git.py
**Description**: Collects comprehensive git repository status including current branch, file status (staged/modified/untracked), ahead/behind counts relative to remote, and recent commit history.

### Plan File Tracking
**Search phrases**: plan file, .PLAN.md, plan document, plan summary, plan content, plan tracking
**Files**: plan.py
**Description**: Monitors and collects information about .PLAN.md files including existence, content summary, line count, and preview of first lines.

### Graphite Stack Integration
**Search phrases**: graphite stack, branch stack, stack position, parent branch, child branches, trunk detection, graphite integration
**Files**: graphite.py
**Description**: Integrates with Graphite to track branch stack relationships, determining current position in stack, parent/child branches, and trunk status.

### GitHub Pull Request Status
**Search phrases**: pull request, PR status, GitHub PR, PR checks, draft PR, merge readiness, CI status, PR state
**Files**: github.py
**Description**: Collects GitHub pull request information for the current branch including PR state, draft status, CI check results, and merge readiness determination. Supports fallback from Graphite to GitHub API.

### Collector Availability Checking
**Search phrases**: collector availability, feature detection, configuration checking, conditional collection, enabled collectors
**Files**: base.py, git.py, plan.py, graphite.py, github.py
**Description**: Each collector implements availability checking to determine if it can run based on configuration, file existence, and context state before attempting collection.

### Status Data Models
**Search phrases**: status models, data structures, status information types, PR status, git status, plan status, stack position
**Files**: git.py, plan.py, graphite.py, github.py
**Description**: Collectors return structured status data objects (GitStatus, PlanStatus, StackPosition, PullRequestStatus) that represent collected information in a standardized format.

### Error Handling and Graceful Degradation
**Search phrases**: error handling, graceful failure, optional data, fallback mechanisms, collection failures
**Files**: base.py, git.py, plan.py, graphite.py, github.py
**Description**: Collectors handle errors gracefully by returning None when information cannot be collected, supporting fallback mechanisms (e.g., GitHub PR collector falls back from Graphite to GitHub API).