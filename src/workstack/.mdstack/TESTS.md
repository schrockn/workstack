# Tests

## Child Packages

- **cli**: Test files located in `tests/cli/` covering command implementations and utilities
- **core**: No test files in scope; core abstractions tested via integration tests in `tests/`
- **status**: Test files located in `tests/status/` covering status collection and rendering

## Tests in This Scope

No test files found in `/workstack/` root directory.

## Related Tests

### tests/cli/test_tree.py (repo-relative)
**Exercises**: `workstack/cli/tree.py`
**Purpose**: Validates tree building and rendering logic for displaying worktree hierarchies with Graphite parent-child relationships
**Scope**: Unit tests for pure tree-building functions and rendering
**Coverage**:
- Happy path: Building trees from valid Graphite cache data, rendering with proper Unicode box-drawing characters
- Error cases: Missing Graphite cache, invalid cache format, branches without worktrees
- Edge cases: Single branch trees, deeply nested stacks, current worktree detection, root worktree naming
- Formatting: Color application for current worktree, worktree annotation display, prefix/connector logic for nested nodes

### tests/cli/test_config.py (repo-relative)
**Exercises**: `workstack/cli/config.py`
**Purpose**: Validates configuration file loading and parsing from `.workstack/config.toml`
**Scope**: Unit tests for configuration loading and TOML parsing
**Coverage**:
- Happy path: Loading valid config files with env variables, post-create commands, and shell specifications
- Error cases: Missing config files (returns defaults), malformed TOML
- Edge cases: Empty config sections, null shell values, missing optional fields
- Defaults: Proper fallback values when config file doesn't exist

### tests/cli/test_graphite.py (repo-relative)
**Exercises**: `workstack/cli/graphite.py`
**Purpose**: Validates Graphite cache reading and branch relationship extraction
**Scope**: Unit tests for branch info loading and stack traversal logic
**Coverage**:
- Happy path: Loading valid Graphite cache, traversing linear stacks, finding parent/child relationships
- Error cases: Missing cache file, corrupted JSON, branches not in cache, git command failures
- Edge cases: Trunk branches (no parent), leaf branches (no children), multiple children (linear chain selection), detached HEAD worktrees
- Stack traversal: Ancestor collection, descendant collection, combining into linear chains

### tests/cli/test_core.py (repo-relative)
**Exercises**: `workstack/cli/core.py`
**Purpose**: Validates repository context discovery and worktree path resolution
**Scope**: Unit tests for repository detection and path utilities
**Coverage**:
- Happy path: Finding git repository root, resolving workstacks directory, calculating worktree paths
- Error cases: Not in a git repository, missing global config, invalid worktree names
- Edge cases: Git worktrees (finding common git directory), nested repositories, symlinks
- Validation: Rejecting reserved names (".", "..", "root"), absolute paths, path separators

### tests/cli/test_activation.py (repo-relative)
**Exercises**: `workstack/cli/activation.py`
**Purpose**: Validates shell activation script generation for worktree environments
**Scope**: Unit tests for shell script generation with environment setup
**Coverage**:
- Happy path: Generating valid bash/zsh scripts with proper quoting and environment setup
- Script components: Directory change, venv creation with `uv sync`, venv activation, .env loading
- Edge cases: Paths with special characters (spaces, quotes), missing venv/env files, custom messages
- Shell compatibility: Proper syntax for bash and zsh

### tests/cli/test_shell_utils.py (repo-relative)
**Exercises**: `workstack/cli/shell_utils.py`
**Purpose**: Validates shell script generation and temporary file management
**Scope**: Unit tests for script rendering and temp file operations
**Coverage**:
- Happy path: Generating cd scripts with proper quoting, writing to temp files with metadata headers, cleaning old scripts
- Error cases: Permission errors during cleanup, missing temp directories
- Edge cases: Paths with special characters, UUID collision handling, file age detection
- Metadata: Script headers with timestamps, UUIDs, user info, working directory

### tests/cli/test_debug.py (repo-relative)
**Exercises**: `workstack/cli/debug.py`
**Purpose**: Validates debug logging functionality
**Scope**: Unit tests for debug mode detection and logging
**Coverage**:
- Happy path: Writing timestamped messages to debug log when `WORKSTACK_DEBUG=1`
- Error cases: Debug mode disabled (no output), file write failures
- Edge cases: Multiple concurrent writes, log file permissions

### tests/cli/commands/ (repo-relative)
**Exercises**: `workstack/cli/commands/` modules
**Purpose**: Validates Click command implementations for all user-facing workflows
**Scope**: Integration tests for command execution with mocked git/GitHub operations
**Coverage**:
- Command argument parsing and validation
- Workflow orchestration (multi-step operations)
- Error handling and user feedback
- Script mode support for shell integration
- Dry-run functionality
- Confirmation prompts and force flags

**Notable patterns**:
- Mock-based testing of external dependencies (git, GitHub, Graphite)
- Fixture-based setup for repository contexts and worktree configurations
- Parametrized tests for multiple operation modes
- Output validation for user-facing messages and script generation
- Edge case coverage for detached HEAD, merged branches, ambiguous branch names

### tests/core/test_gitops.py (repo-relative)
**Exercises**: `workstack/core/gitops.py`
**Purpose**: Validates git operations abstraction and implementations
**Scope**: Unit tests for GitOps interface and RealGitOps/DryRunGitOps implementations
**Coverage**:
- Happy path: Executing git commands and parsing output correctly
- Worktree operations: Creating, moving, removing, listing worktrees
- Branch operations: Checking out, deleting, querying branch information
- Query operations: Getting current branch, detecting default branch, retrieving commit info
- Dry-run mode: Verifying destructive operations print intentions instead of executing
- Error cases: Git command failures, invalid branch names, missing worktrees
- Edge cases: Detached HEAD states, worktrees with special characters in names, git common directory resolution

### tests/core/test_github_ops.py (repo-relative)
**Exercises**: `workstack/core/github_ops.py`
**Purpose**: Validates GitHub API operations abstraction
**Scope**: Unit tests for GitHubOps interface and RealGitHubOps/DryRunGitHubOps implementations
**Coverage**:
- Happy path: Fetching PR lists, querying PR status, parsing GitHub API responses
- PR information: State determination, draft status, CI check aggregation
- Check status logic: Handling various check states (passed, failed, pending, skipped)
- Error cases: Missing gh CLI, authentication failures, invalid JSON responses
- Graceful degradation: Returning empty results when GitHub unavailable
- Dry-run mode: Verifying read-only operations delegate to wrapped implementation

### tests/core/test_graphite_ops.py (repo-relative)
**Exercises**: `workstack/core/graphite_ops.py`
**Purpose**: Validates Graphite operations abstraction and cache parsing
**Scope**: Unit tests for GraphiteOps interface and cache file parsing
**Coverage**:
- Happy path: Reading Graphite cache files, parsing JSON, extracting branch relationships
- Cache parsing: Handling .graphite_cache_persist and .graphite_pr_info formats
- Branch stack building: Traversing parent-child relationships to build linear chains
- URL conversion: Converting between Graphite and GitHub URL formats
- Error cases: Missing cache files, corrupted JSON, invalid branch data
- Graceful degradation: Returning empty results when Graphite unavailable
- Dry-run mode: Verifying sync operations print intentions

### tests/core/test_global_config_ops.py (repo-relative)
**Exercises**: `workstack/core/global_config_ops.py`
**Purpose**: Validates global configuration file management
**Scope**: Unit tests for GlobalConfigOps interface and configuration persistence
**Coverage**:
- Happy path: Reading and writing ~/.workstack/config.toml, lazy-loaded caching
- Configuration fields: Workstacks root, Graphite preference, shell setup status, PR display options
- Caching behavior: Cache invalidation on writes, lazy loading on first access
- File operations: Creating parent directories, TOML parsing and serialization
- Sentinel pattern: Using _UNCHANGED sentinel for optional config updates
- Error cases: File permission errors, invalid TOML, missing config file
- Dry-run mode: Verifying write operations print intentions

### tests/core/test_shell_ops.py (repo-relative)
**Exercises**: `workstack/core/shell_ops.py`
**Purpose**: Validates shell detection and tool availability checking
**Scope**: Unit tests for ShellOps interface and shell detection logic
**Coverage**:
- Happy path: Detecting current shell from SHELL environment variable, finding tools in PATH
- Shell detection: Mapping shell paths to shell names (bash, zsh, fish)
- RC file resolution: Determining correct shell configuration file paths
- Tool availability: Checking if command-line tools (git, gh, gt) are installed
- Error cases: Missing SHELL environment variable, tools not in PATH
- Edge cases: Non-standard shell paths, symlinked shells

### tests/core/test_context.py (repo-relative)
**Exercises**: `workstack/core/context.py`
**Purpose**: Validates dependency injection context creation
**Scope**: Unit tests for WorkstackContext factory and assembly
**Coverage**:
- Happy path: Creating context with real implementations, creating context with dry-run wrappers
- Dependency assembly: Verifying all operations are properly initialized
- Dry-run mode: Verifying dry-run flag correctly wraps destructive operations
- Context immutability: Verifying frozen dataclass prevents modification

### tests/core/test_branch_metadata.py (repo-relative)
**Exercises**: `workstack/core/branch_metadata.py`
**Purpose**: Validates branch metadata data structure
**Scope**: Unit tests for BranchMetadata dataclass
**Coverage**:
- Happy path: Creating branch metadata with all fields
- Immutability: Verifying frozen dataclass prevents modification
- Field validation: Ensuring all fields are properly typed

### tests/core/test_file_utils.py (repo-relative)
**Exercises**: `workstack/core/file_utils.py`
**Purpose**: Validates file operation utilities
**Scope**: Unit tests for markdown parsing and plan file handling
**Coverage**:
- Happy path: Extracting first heading from markdown files with YAML frontmatter
- Edge cases: Files without headings, files with only frontmatter, empty files
- Error cases: Missing files, invalid YAML frontmatter

### tests/status/test_orchestrator.py (repo-relative)
**Exercises**: `workstack/status/orchestrator.py`
**Purpose**: Validates core orchestration logic for parallel status collection
**Scope**: Integration testing of StatusOrchestrator class
**Coverage**:
- Happy path: Parallel collector execution, aggregation of results into StatusData
- Timeout handling: Verifying individual collector timeouts don't block others
- Graceful degradation: Verifying failed collectors don't fail entire command
- Worktree detection: Determining root vs linked worktrees, current worktree identification
- Related worktrees: Discovering and filtering other worktrees in repository
- Error boundaries: Verifying individual collector failures are caught and logged

### tests/status/collectors/test_git_collector.py (repo-relative)
**Exercises**: `workstack/status/collectors/git.py`
**Purpose**: Validates git repository status collection
**Scope**: Unit testing of GitStatusCollector
**Coverage**:
- Happy path: Collecting current branch, file status, commit history
- Availability checking: Verifying collector runs in git repositories
- File categorization: Staged, modified, untracked files detection
- Commit tracking: Ahead/behind commit counts relative to remote
- Edge cases: Detached HEAD, no commits, no remote tracking

### tests/status/collectors/test_plan_collector.py (repo-relative)
**Exercises**: `workstack/status/collectors/plan.py`
**Purpose**: Validates .PLAN.md file detection and content collection
**Scope**: Unit testing of PlanFileCollector
**Coverage**:
- Happy path: Detecting plan files, reading content, calculating line counts
- Availability checking: Verifying collector runs when plan file exists
- Content handling: Extracting preview lines, summarizing content
- Error cases: Missing files, permission errors, empty files

### tests/status/collectors/test_graphite_collector.py (repo-relative)
**Exercises**: `workstack/status/collectors/graphite.py`
**Purpose**: Validates Graphite stack position tracking
**Scope**: Unit testing of GraphiteStackCollector
**Coverage**:
- Happy path: Detecting stack position, identifying parent/child relationships
- Availability checking: Verifying collector runs when Graphite enabled
- Stack hierarchy: Trunk detection, position within stack
- Edge cases: Branches not in stack, single-branch stacks

### tests/status/collectors/test_github_collector.py (repo-relative)
**Exercises**: `workstack/status/collectors/github.py`
**Purpose**: Validates GitHub pull request status collection
**Scope**: Unit testing of GitHubPRCollector
**Coverage**:
- Happy path: Fetching PR data, determining state and merge readiness
- Availability checking: Verifying collector runs when PR info enabled
- PR state: Open, closed, merged, draft status detection
- Check results: Aggregating CI check status
- Error cases: Branches without PRs, API failures, missing data

### tests/status/models/test_status_data.py (repo-relative)
**Exercises**: `workstack/status/models/status_data.py`
**Purpose**: Validates status data model construction
**Scope**: Unit testing of all StatusData model classes
**Coverage**:
- Happy path: Creating models with required and optional fields
- Immutability: Verifying frozen dataclass prevents modification
- Type validation: Ensuring fields are properly typed
- Composition: Verifying nested models compose correctly into StatusData

### tests/status/renderers/test_simple_renderer.py (repo-relative)
**Exercises**: `workstack/status/renderers/simple.py`
**Purpose**: Validates terminal output rendering of status information
**Scope**: Unit testing of SimpleRenderer
**Coverage**:
- Happy path: Rendering complete status with all sections
- Conditional rendering: Verifying optional sections render only when data available
- Formatting: Color application, text styling, visual hierarchy
- File list handling: Truncation with "more items" indicators
- Edge cases: Missing data, partial status, empty collections

## Testing Patterns and Approaches

### Dependency Injection for Testability
The codebase uses dependency injection extensively to enable testing. The `WorkstackContext` provides access to all external operations (git, GitHub, Graphite, config), allowing tests to inject mock implementations. This pattern appears consistently across core operations and CLI commands.

### Mock-Based Testing
Tests use mocking to isolate components from external dependencies (git commands, GitHub API, Graphite cache files). This enables fast, deterministic tests that don't require actual repositories or API access.

### Fixture-Based Setup
Test fixtures establish common test scenarios (repository contexts, worktree configurations, Graphite cache data) that are reused across multiple tests. This reduces duplication and ensures consistent test environments.

### Graceful Degradation Testing
Tests verify that the system continues functioning when optional components are unavailable (missing Graphite cache, GitHub API unavailable, etc.). This validates the error boundary patterns used throughout the codebase.

### Dry-Run Mode Validation
Tests verify that dry-run implementations correctly intercept destructive operations and print intentions instead of executing them. This ensures the preview functionality works correctly for all operations.

### Error Boundary Validation
Tests verify that errors in individual components (collectors, operations) are caught and handled gracefully, preventing cascading failures. This is particularly important for parallel operations like status collection.

### Pure Function Testing
Tests for pure functions (tree rendering, path resolution, configuration parsing) verify correct transformation of inputs to outputs without side effects. These tests are typically fast and deterministic.

### Integration Testing
Command tests perform integration testing by orchestrating multiple components together with mocked external dependencies. This validates that workflows function correctly end-to-end.