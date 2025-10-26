# Tests

## Child Packages

- **commands**: No test files found in this scope

## Tests in This Scope

No test files found in `/workstack/cli/`.

## Related Tests

### tests/cli/test_tree.py (repo-relative)
**Exercises**: `workstack/cli/tree.py`
**Purpose**: Validates tree building and rendering logic for displaying worktree hierarchies with Graphite parent-child relationships
**Scope**: 
- Unit tests for pure tree-building functions (`build_workstack_tree`, `_get_worktree_mapping`, `_load_graphite_branch_graph`, `_filter_graph_to_active_branches`, `_build_tree_from_graph`)
- Unit tests for tree rendering (`render_tree`, `_format_branch_name`, `_format_worktree_annotation`)
**Coverage**:
- Happy path: Building trees from valid Graphite cache data, rendering with proper Unicode box-drawing characters
- Error cases: Missing Graphite cache, invalid cache format, branches without worktrees
- Edge cases: Single branch trees, deeply nested stacks, current worktree detection, root worktree naming
- Formatting: Color application for current worktree, worktree annotation display, prefix/connector logic for nested nodes

### tests/cli/test_config.py (repo-relative)
**Exercises**: `workstack/cli/config.py`
**Purpose**: Validates configuration file loading and parsing from `.workstack/config.toml`
**Scope**: 
- Unit tests for `LoadedConfig` dataclass and `load_config()` function
- TOML parsing and environment variable extraction
**Coverage**:
- Happy path: Loading valid config files with env variables, post-create commands, and shell specifications
- Error cases: Missing config files (returns defaults), malformed TOML
- Edge cases: Empty config sections, null shell values, missing optional fields
- Defaults: Proper fallback values when config file doesn't exist

### tests/cli/test_graphite.py (repo-relative)
**Exercises**: `workstack/cli/graphite.py`
**Purpose**: Validates Graphite cache reading and branch relationship extraction
**Scope**:
- Unit tests for branch info loading (`_load_branch_info`, `_load_graphite_cache`)
- Stack traversal logic (`get_branch_stack`, `get_parent_branch`, `get_child_branches`)
- Worktree-branch matching (`find_worktrees_containing_branch`, `find_worktree_for_branch`)
**Coverage**:
- Happy path: Loading valid Graphite cache, traversing linear stacks, finding parent/child relationships
- Error cases: Missing cache file, corrupted JSON, branches not in cache, git command failures
- Edge cases: Trunk branches (no parent), leaf branches (no children), multiple children (linear chain selection), detached HEAD worktrees
- Stack traversal: Ancestor collection, descendant collection, combining into linear chains

### tests/cli/test_core.py (repo-relative)
**Exercises**: `workstack/cli/core.py`
**Purpose**: Validates repository context discovery and worktree path resolution
**Scope**:
- Unit tests for `discover_repo_context()` function
- Worktree path calculation (`worktree_path_for`)
- Worktree name validation (`validate_worktree_name_for_removal`)
- Workstacks directory creation (`ensure_workstacks_dir`)
**Coverage**:
- Happy path: Finding git repository root, resolving workstacks directory, calculating worktree paths
- Error cases: Not in a git repository, missing global config, invalid worktree names
- Edge cases: Git worktrees (finding common git directory), nested repositories, symlinks
- Validation: Rejecting reserved names (".", "..", "root"), absolute paths, path separators

### tests/cli/test_activation.py (repo-relative)
**Exercises**: `workstack/cli/activation.py`
**Purpose**: Validates shell activation script generation for worktree environments
**Scope**:
- Unit tests for `render_activation_script()` function
- Shell script generation with venv and .env handling
**Coverage**:
- Happy path: Generating valid bash/zsh scripts with proper quoting and environment setup
- Script components: Directory change, venv creation with `uv sync`, venv activation, .env loading
- Edge cases: Paths with special characters (spaces, quotes), missing venv/env files, custom messages
- Shell compatibility: Proper syntax for bash and zsh

### tests/cli/test_shell_utils.py (repo-relative)
**Exercises**: `workstack/cli/shell_utils.py`
**Purpose**: Validates shell script generation and temporary file management
**Scope**:
- Unit tests for script rendering (`render_cd_script`)
- Temporary file writing (`write_script_to_temp`)
- Stale script cleanup (`cleanup_stale_scripts`)
**Coverage**:
- Happy path: Generating cd scripts with proper quoting, writing to temp files with metadata headers, cleaning old scripts
- Error cases: Permission errors during cleanup, missing temp directories
- Edge cases: Paths with special characters, UUID collision handling, file age detection
- Metadata: Script headers with timestamps, UUIDs, user info, working directory

### tests/cli/test_debug.py (repo-relative)
**Exercises**: `workstack/cli/debug.py`
**Purpose**: Validates debug logging functionality
**Scope**:
- Unit tests for debug mode detection (`is_debug()`)
- Debug log writing (`debug_log()`)
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
- Parametrized tests for multiple operation modes (e.g., create with different flags)
- Output validation for user-facing messages and script generation
- Edge case coverage for detached HEAD, merged branches, ambiguous branch names