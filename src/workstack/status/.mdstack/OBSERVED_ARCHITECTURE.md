# Observed Architecture

## Overview

The `status` scope implements a comprehensive status command system that collects, aggregates, and displays information about git worktrees and their development environment. It follows a layered architecture with three main responsibilities:

1. **Collection Layer** (`collectors/`): Gathers status information from various sources (git, GitHub, Graphite, filesystem)
2. **Data Model Layer** (`models/`): Defines immutable data structures representing status information
3. **Presentation Layer** (`renderers/`): Formats and displays status data to users
4. **Orchestration Layer** (`orchestrator.py`): Coordinates collectors and assembles final status data

The architecture emphasizes extensibility through plugin-based collectors, graceful degradation when data sources fail, and parallel execution for responsive output.

## Module Organization

### orchestrator.py
**Responsibility**: Coordinates all status collectors, runs them in parallel with timeouts, and assembles final status data into a unified `StatusData` object
**Key exports**: `StatusOrchestrator` class
**Key methods**: 
- `collect_status()` - Main entry point that orchestrates parallel collection
- `_get_worktree_info()` - Extracts basic worktree metadata
- `_get_related_worktrees()` - Lists other worktrees in the repository

### __init__.py
**Responsibility**: Package initialization and public API definition
**Key exports**: `StatusOrchestrator`

## Subpackages

### collectors/
Implements a plugin-based architecture for gathering status information. Each collector is a specialized component responsible for extracting a specific type of status data. See `.mdstack/OBSERVED_ARCHITECTURE.md` in the collectors scope for detailed architecture.

**Key concepts**:
- Abstract `StatusCollector` base class defines the interface
- Concrete implementations: `GitStatusCollector`, `GitHubPRCollector`, `GraphiteStackCollector`, `PlanFileCollector`
- Each collector implements `is_available()` for precondition checking and `collect()` for data gathering
- Graceful degradation: collectors return `None` on failure rather than raising exceptions

### models/
Defines frozen dataclasses representing all status information domains. See `.mdstack/OBSERVED_ARCHITECTURE.md` in the models scope for detailed architecture.

**Key concepts**:
- `StatusData` is the root container aggregating all status information
- Domain-specific models: `GitStatus`, `StackPosition`, `PullRequestStatus`, `EnvironmentStatus`, `DependencyStatus`, `PlanStatus`, `WorktreeInfo`
- All models use `@dataclass(frozen=True)` for immutability
- Optional fields accommodate partial data collection from different sources

### renderers/
Provides pluggable rendering system for displaying status information. See `.mdstack/OBSERVED_ARCHITECTURE.md` in the renderers scope for detailed architecture.

**Key concepts**:
- `SimpleRenderer` converts `StatusData` to formatted terminal output with colors
- Section-based rendering: header, plan, stack, PR status, git status, related worktrees
- Extensible design allows alternative renderers (JSON, HTML, etc.)

## Core Abstractions

### StatusOrchestrator
**Location**: orchestrator.py (scope-relative)
**Purpose**: Central coordinator that manages parallel collection of status information from multiple sources and assembles results into unified `StatusData`
**Type**: Concrete class
**Key characteristics**:
- Manages thread pool for parallel collector execution
- Implements timeout handling per collector and overall
- Gracefully handles collector failures without failing entire command
- Type-checks collector results before including in final `StatusData`

## Critical Functions

### StatusOrchestrator.collect_status()
**Location**: orchestrator.py (scope-relative)
**Purpose**: Main entry point that orchestrates the entire status collection process
**Signature**: `collect_status(ctx: WorkstackContext, worktree_path: Path, repo_root: Path) -> StatusData`
**Key behavior**:
- Determines worktree metadata (name, branch, root status)
- Submits all available collectors to thread pool
- Collects results with per-collector timeout
- Handles both individual collector timeouts and overall timeout
- Type-checks results before including in `StatusData`
- Retrieves list of related worktrees
- Returns complete `StatusData` object with all collected information

### StatusOrchestrator._get_worktree_info()
**Location**: orchestrator.py (scope-relative)
**Purpose**: Extracts basic metadata about a worktree
**Signature**: `_get_worktree_info(ctx: WorkstackContext, worktree_path: Path, repo_root: Path) -> WorktreeInfo`
**Key behavior**:
- Determines if worktree is the repository root
- Gets current branch via `ctx.git_ops`
- Returns `WorktreeInfo` with name, path, branch, and root status

### StatusOrchestrator._get_related_worktrees()
**Location**: orchestrator.py (scope-relative)
**Purpose**: Retrieves list of other worktrees in the repository
**Signature**: `_get_related_worktrees(ctx: WorkstackContext, repo_root: Path, current_path: Path) -> list[WorktreeInfo]`
**Key behavior**:
- Lists all worktrees via `ctx.git_ops.list_worktrees()`
- Filters out current worktree
- Determines root status for each worktree
- Handles missing worktree paths gracefully
- Returns list of `WorktreeInfo` for related worktrees

## Architectural Patterns

### Orchestration Pattern
The `StatusOrchestrator` implements a **coordinator pattern** that:
- Manages lifecycle of multiple collectors
- Handles cross-cutting concerns (timeouts, error handling)
- Assembles results into unified output
- Shields callers from complexity of parallel execution

### Plugin Architecture (Collectors)
Collectors implement a **plugin pattern** where:
- Abstract `StatusCollector` base class defines the contract
- Each collector is self-contained and independent
- Collectors declare availability via `is_available()`
- New collectors can be added without modifying orchestrator
- Orchestrator discovers and runs available collectors

### Parallel Execution with Graceful Degradation
The orchestrator implements **resilient parallel execution**:
- Uses `ThreadPoolExecutor` for concurrent collector execution
- Per-collector timeout prevents slow collectors from blocking others
- Overall timeout ensures responsive output
- Failed or slow collectors return `None` rather than failing entire command
- Partial status collection is acceptable and expected

### Error Boundary Pattern
The orchestrator implements **error boundaries** at multiple levels:
- Individual collector failures don't affect other collectors
- Timeout errors are caught and logged, not propagated
- Type checking ensures only valid data enters `StatusData`
- Graceful degradation: missing data is represented as `None` fields

### Context Injection Pattern
All components receive `WorkstackContext` providing:
- `git_ops`: Git repository operations
- `github_ops`: GitHub API operations
- `graphite_ops`: Graphite stack operations
- `global_config_ops`: Configuration access

This centralizes dependencies and enables testing/mocking.

## Data Flow

1. **Invocation**: External code calls `StatusOrchestrator.collect_status()` with context and paths
2. **Worktree Metadata**: Orchestrator determines basic worktree info (name, branch, root status)
3. **Availability Check**: Orchestrator calls `is_available()` on each collector
4. **Parallel Submission**: Available collectors are submitted to thread pool
5. **Concurrent Collection**: Each collector runs independently:
   - Accesses context operations (git, GitHub, Graphite, filesystem)
   - Gathers raw data from sources
   - Transforms into domain models
   - Returns structured data or `None` on failure
6. **Result Collection**: Orchestrator collects results with timeout handling:
   - Per-collector timeout prevents blocking
   - Overall timeout ensures responsiveness
   - Failed collectors contribute `None` to results
7. **Type Validation**: Orchestrator type-checks results before including in `StatusData`
8. **Related Worktrees**: Orchestrator retrieves list of other worktrees
9. **Assembly**: All results assembled into single `StatusData` object
10. **Return**: Complete status data returned to caller
11. **Presentation**: External code passes `StatusData` to renderer for display

## Dependencies

### Internal Dependencies
- `workstack.core.context.WorkstackContext`: Provides access to git, GitHub, Graphite, and config operations
- `workstack.status.collectors.base.StatusCollector`: Abstract base class for all collectors
- `workstack.status.models.status_data`: All status data models (GitStatus, PullRequestStatus, etc.)

### External Dependencies
- `pathlib.Path`: Filesystem path handling
- `concurrent.futures`: Thread pool and timeout management
- `logging`: Debug logging for collector timeouts and failures

### Context Operations Used
- `ctx.git_ops.get_current_branch()`: Get current branch of worktree
- `ctx.git_ops.list_worktrees()`: List all worktrees in repository

## Extension Points

### Adding a New Collector

To add a new status collector:

1. **Create collector class** in `collectors/` scope:
   ```python
   from workstack.status.collectors.base import StatusCollector
   
   class MyStatusCollector(StatusCollector):
       @property
       def name(self) -> str:
           return "my_status"
       
       def is_available(self, ctx, worktree_path) -> bool:
           # Check preconditions
           return True
       
       def collect(self, ctx, worktree_path, repo_root):
           # Gather data and return domain model or None
           pass
   ```

2. **Create domain model** in `models/status_data.py` if needed:
   ```python
   @dataclass(frozen=True)
   class MyStatus:
       field1: str
       field2: int | None = None
   ```

3. **Export collector** from `collectors/__init__.py`

4. **Register with orchestrator** (external to this scope):
   ```python
   orchestrator = StatusOrchestrator([
       GitStatusCollector(),
       MyStatusCollector(),  # New collector
       # ... other collectors
   ])
   ```

5. **Add field to StatusData** in `models/status_data.py`:
   ```python
   @dataclass(frozen=True)
   class StatusData:
       # ... existing fields
       my_status: MyStatus | None = None
   ```

6. **Update orchestrator** to include new collector result:
   ```python
   my_result = results.get("my_status")
   return StatusData(
       # ... existing fields
       my_status=my_result if isinstance(my_result, MyStatus) else None,
   )
   ```

7. **Add rendering** in `renderers/simple.py` to display new status

### Modifying Timeout Behavior

- **Per-collector timeout**: Adjust `timeout_seconds` parameter in `StatusOrchestrator.__init__()`
- **Overall timeout**: Modify calculation in `collect_status()`: `total_timeout = self.timeout_seconds * len(futures)`
- **Timeout handling**: Modify exception handling in `as_completed()` loop

### Changing Collector Execution Strategy

- **Sequential execution**: Replace `ThreadPoolExecutor` with sequential loop
- **Different thread pool size**: Modify `max_workers=5` parameter
- **Custom timeout logic**: Implement alternative timeout mechanism in `as_completed()` loop

### Adding New Worktree Information

To track additional worktree metadata:

1. Add field to `WorktreeInfo` in `models/status_data.py`
2. Populate in `_get_worktree_info()` method
3. Update `_get_related_worktrees()` if needed
4. Add rendering in `renderers/simple.py`

## Key Concepts Explained

### Worktree
A git worktree is an alternative working directory linked to the same repository. Git allows multiple worktrees to exist simultaneously, each with its own branch and working state. The status command tracks the current worktree and lists related ones.

### Collector Availability
Collectors implement `is_available()` to check preconditions before attempting collection. This allows the orchestrator to skip unavailable collectors efficiently without errors. For example, a GitHub PR collector might check if PR info is enabled in config before attempting collection.

### Graceful Degradation
The architecture is designed to provide partial status even when some data sources fail:
- Failed collectors return `None` rather than raising exceptions
- Orchestrator continues with other collectors
- Final `StatusData` may have `None` fields for unavailable information
- Users see what information is available rather than complete failure

### Parallel Execution with Timeouts
The orchestrator runs collectors concurrently to minimize total execution time:
- Each collector has its own timeout to prevent blocking
- Overall timeout ensures responsive output
- Failed or slow collectors don't affect others
- Results are collected as they complete via `as_completed()`

### Type Safety in Assembly
The orchestrator type-checks collector results before including them in `StatusData`:
```python
git_result = results.get("git")
git_status=git_result if isinstance(git_result, GitStatus) else None,
```
This ensures only valid data enters the final status object, even if collectors return unexpected types.

### Error Boundaries
The orchestrator implements error boundaries at multiple levels:
- Individual collector exceptions are caught and logged
- Timeout errors don't propagate to caller
- Type mismatches are handled gracefully
- Partial results are acceptable

This is an intentional use of exception handling at error boundaries per the codebase's exception handling guidelines.

## Common Agent Tasks

### Understanding Status Collection Flow
1. Review `StatusOrchestrator.collect_status()` to see overall orchestration
2. Check `collectors/` scope documentation for individual collector patterns
3. Review `models/status_data.py` to understand data structures
4. Trace through `_get_worktree_info()` and `_get_related_worktrees()` for metadata gathering

### Adding a New Status Type
1. Create domain model in `models/status_data.py` (frozen dataclass)
2. Create collector in `collectors/` scope implementing `StatusCollector`
3. Add field to `StatusData` in `models/status_data.py`
4. Update `collect_status()` to include new collector result
5. Add rendering in `renderers/simple.py`

### Debugging Collection Issues
1. Check if collector `is_available()` - if False, preconditions not met
2. Review collector's `collect()` method for error handling
3. Check orchestrator's timeout settings - may be too aggressive
4. Verify context operations (git_ops, github_ops, etc.) are working
5. Check logs for timeout or exception messages

### Modifying Timeout Behavior
1. Adjust `timeout_seconds` parameter in `StatusOrchestrator.__init__()`
2. Modify overall timeout calculation in `collect_status()`
3. Test with slow collectors to verify timeout handling
4. Verify partial results are acceptable when timeouts occur

### Handling New Worktree Metadata
1. Add field to `WorktreeInfo` in `models/status_data.py`
2. Populate in `_get_worktree_info()` using `ctx.git_ops` or other operations
3. Update `_get_related_worktrees()` if metadata applies to related worktrees
4. Add display logic in `renderers/simple.py`

### Improving Collector Performance
1. Review collector's `is_available()` - avoid expensive checks
2. Optimize data gathering in `collect()` method
3. Consider caching if collector is called frequently
4. Profile to identify bottlenecks
5. Adjust timeout if collector is legitimately slow

### Understanding Error Handling
1. Review exception handling in `collect_status()` - catches both TimeoutError and general Exception
2. Check how failed collectors are represented (as `None` in results)
3. Verify type checking prevents invalid data in `StatusData`
4. Review logging to understand what failures are recorded
5. Test with failing collectors to verify graceful degradation