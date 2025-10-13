# Implementation Plan: Phases 3 & 4 - Testing Infrastructure and Documentation

## Status: Phases 1 & 2 Complete ✅

### Completed Work

**Phase 1: Foundation** ✅

- Created ShellOps abstraction (`src/workstack/core/shell_ops.py`)
- Created FakeShellOps (`tests/fakes/shell_ops.py`)
- Added ShellOps to WorkstackContext
- Refactored init command to use ShellOps
- Eliminated ALL mock.patch usage (31 tests in test_init.py + updates across codebase)
- **Result**: 422 tests passing, 0 pyright errors, zero mock.patch usage

**Phase 2: Complete Three Implementations Pattern** ✅

- Added DryRunGitHubOps (`src/workstack/core/github_ops.py:257-286`)
- Added DryRunGlobalConfigOps (`src/workstack/core/global_config_ops.py:291-357`)
- Updated context factory to wrap all dependencies when `dry_run=True`
- **Result**: All 5 dependency categories now have Real, Dry-Run, and Fake implementations

---

## Phase 3: Testing Infrastructure

**Goal**: Add mutation tracking and comprehensive dry-run integration tests.

### Task 3.1: Add Mutation Tracking Properties to FakeGitOps

**Location**: `tests/fakes/gitops.py`

**Why**: Make test assertions explicit about what mutations occurred during test execution.

**Implementation**:

```python
class FakeGitOps(GitOps):
    def __init__(self, ...):
        # Existing constructor
        self._worktrees = worktrees or {}
        # ... other fields ...

        # Add tracking lists
        self._deleted_branches: list[str] = []
        self._added_worktrees: list[tuple[Path, str | None]] = []
        self._removed_worktrees: list[Path] = []
        self._checked_out_branches: list[tuple[Path, str]] = []

    def delete_branch(self, repo_root: Path, branch: str, *, force: bool) -> None:
        # Existing implementation
        ...
        # Track the deletion
        self._deleted_branches.append(branch)

    def add_worktree(self, repo_root: Path, path: Path, branch: str | None, ...) -> None:
        # Existing implementation
        ...
        # Track the addition
        self._added_worktrees.append((path, branch))

    def remove_worktree(self, repo_root: Path, worktree_path: Path, *, force: bool) -> None:
        # Existing implementation
        ...
        # Track the removal
        self._removed_worktrees.append(worktree_path)

    def checkout_branch(self, repo_root: Path, branch: str) -> None:
        # Existing implementation
        ...
        # Track the checkout
        self._checked_out_branches.append((repo_root, branch))

    # Add read-only properties for assertions
    @property
    def deleted_branches(self) -> list[str]:
        """Get list of branches deleted during test."""
        return self._deleted_branches.copy()

    @property
    def added_worktrees(self) -> list[tuple[Path, str | None]]:
        """Get list of worktrees added during test."""
        return self._added_worktrees.copy()

    @property
    def removed_worktrees(self) -> list[Path]:
        """Get list of worktrees removed during test."""
        return self._removed_worktrees.copy()

    @property
    def checked_out_branches(self) -> list[tuple[Path, str]]:
        """Get list of branches checked out during test."""
        return self._checked_out_branches.copy()
```

**Example Test Usage**:

```python
def test_rm_deletes_branch():
    git_ops = FakeGitOps(...)
    ctx = create_test_context(git_ops=git_ops)

    result = runner.invoke(cli, ["rm", "feature-branch"], obj=ctx)

    # Clear assertion about what mutation occurred
    assert "feature-branch" in git_ops.deleted_branches
    assert len(git_ops.deleted_branches) == 1
```

**Files to Update**:

- `tests/fakes/gitops.py` - Add tracking infrastructure
- Update 5-10 existing tests to demonstrate the pattern

**Success Criteria**:

- Mutation tracking properties available
- At least 5 tests updated to use new properties
- All 422+ tests still passing

---

### Task 3.2: Create Dry-Run Integration Test Suite

**Location**: `tests/integration/test_dryrun_integration.py` (new file)

**Why**: Verify that dry-run mode prevents destructive operations across all dependency categories.

**Implementation**:

```python
"""Integration tests for dry-run behavior across all operations.

These tests verify that dry-run mode prevents destructive operations
while still allowing read operations.
"""

from pathlib import Path
from click.testing import CliRunner

from workstack.cli.cli import cli
from workstack.core.context import create_context
from tests.integration.helpers import init_git_repo


def test_dryrun_git_operations_print_messages(tmp_path: Path) -> None:
    """Test that dry-run GitOps operations print messages without executing."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Use real context with dry_run=True
    ctx = create_context(dry_run=True)

    runner = CliRunner()
    # This should print dry-run message but not actually remove anything
    result = runner.invoke(
        cli,
        ["rm", "nonexistent-stack", "--force"],
        obj=ctx,
        catch_exceptions=False,
    )

    # Should show dry-run intent
    assert "[DRY RUN]" in result.output or "[DRY RUN]" in result.stderr


def test_dryrun_config_operations_print_messages(tmp_path: Path) -> None:
    """Test that dry-run GlobalConfigOps operations print messages."""
    # Test that config.set() prints but doesn't modify files
    # This would require a command that writes to global config
    pass


def test_dryrun_read_operations_still_work(tmp_path: Path) -> None:
    """Test that dry-run mode allows read operations."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    ctx = create_context(dry_run=True)

    runner = CliRunner()
    # List should work even in dry-run mode
    result = runner.invoke(cli, ["list"], obj=ctx)

    assert result.exit_code == 0
    # Should show normal output, no dry-run warnings for reads


def test_dryrun_graphite_operations_print_messages(tmp_path: Path) -> None:
    """Test that dry-run GraphiteOps operations print messages."""
    # Test gt commands print but don't execute
    # Would need a command that uses GraphiteOps write operations
    pass
```

**Additional Test Cases**:

- Test that dry-run mode is properly threaded through context
- Test that environment variable `WORKSTACK_DRY_RUN=1` activates dry-run
- Test complex operations that involve multiple write operations
- Verify exit codes are correct in dry-run mode

**Files to Create**:

- `tests/integration/test_dryrun_integration.py`

**Success Criteria**:

- At least 5 dry-run integration tests
- Tests cover GitOps, GlobalConfigOps, GraphiteOps
- All tests passing

---

### Task 3.3: Run Full Test Suite and Fix Any Issues

**Goal**: Ensure all changes integrate correctly.

**Steps**:

1. Run: `uv run pytest tests/ -v`
2. Run: `uv run pyright src/ tests/`
3. Fix any regressions found
4. Verify performance hasn't degraded

**Success Criteria**:

- All tests pass
- Pyright reports 0 errors
- No performance regressions (tests complete in similar time)

---

## Phase 4: Documentation

**Goal**: Create comprehensive testing documentation that enables agents and developers to write tests correctly.

### Task 4.1: Create .agent/docs/TESTING.md

**Location**: `.agent/docs/TESTING.md` (new file)

**Why**: Centralize testing patterns in .agent directory for AI agent consumption.

**Structure**:

````markdown
# Test Architecture: Coarse-Grained Dependency Injection

## Quick Reference

| Testing Scenario              | Use This                                             |
| ----------------------------- | ---------------------------------------------------- |
| Unit test CLI command         | FakeGitOps + FakeGlobalConfigOps + context injection |
| Integration test git behavior | RealGitOps + tmp_path fixture                        |
| Test dry-run behavior         | create_context(dry_run=True) + assertions on output  |
| Test shell detection          | FakeShellOps with detected_shell parameter           |
| Test tool availability        | FakeShellOps with installed_tools parameter          |

## Dependency Categories

### 1. GitOps - Version Control Operations

**Real Implementation**: `RealGitOps()`
**Dry-Run Wrapper**: `DryRunGitOps(wrapped)`
**Fake Implementation**: `FakeGitOps(...)`

**Constructor Parameters**:

```python
FakeGitOps(
    worktrees: dict[Path, list[WorktreeInfo]] = {},
    current_branches: dict[Path, str] = {},
    default_branches: dict[Path, str] = {},
    git_common_dirs: dict[Path, Path] = {},
    remote_tracking_branches: dict[tuple[Path, str], str] = {},
)
```
````

**Mutation Tracking** (read-only properties):

- `git_ops.deleted_branches: list[str]`
- `git_ops.added_worktrees: list[tuple[Path, str | None]]`
- `git_ops.removed_worktrees: list[Path]`
- `git_ops.checked_out_branches: list[tuple[Path, str]]`

**Common Patterns**:

```python
# Pattern 1: Empty git state
git_ops = FakeGitOps(git_common_dirs={cwd: cwd / ".git"})

# Pattern 2: Pre-configured worktrees
git_ops = FakeGitOps(
    worktrees={
        repo: [
            WorktreeInfo(path=repo, branch="main"),
            WorktreeInfo(path=wt1, branch="feature"),
        ]
    },
    git_common_dirs={repo: repo / ".git"},
)

# Pattern 3: Track mutations
git_ops = FakeGitOps(...)
# ... run command ...
assert "feature" in git_ops.deleted_branches
```

### 2. GlobalConfigOps - Configuration Management

**Real Implementation**: `RealGlobalConfigOps()`
**Dry-Run Wrapper**: `DryRunGlobalConfigOps(wrapped)`
**Fake Implementation**: `FakeGlobalConfigOps(...)`

**Constructor Parameters**:

```python
FakeGlobalConfigOps(
    exists: bool = True,
    workstacks_root: Path | None = None,
    use_graphite: bool = False,
    shell_setup_complete: bool = False,
    show_pr_info: bool = True,
    show_pr_checks: bool = False,
)
```

**Common Patterns**:

```python
# Pattern 1: Config exists with values
config_ops = FakeGlobalConfigOps(
    exists=True,
    workstacks_root=Path("/tmp/workstacks"),
    use_graphite=True,
)

# Pattern 2: Config doesn't exist (first-time init)
config_ops = FakeGlobalConfigOps(exists=False)

# Pattern 3: Test config mutations
config_ops = FakeGlobalConfigOps(exists=False)
config_ops.set(workstacks_root=Path("/tmp/ws"), use_graphite=True)
assert config_ops.get_workstacks_root() == Path("/tmp/ws")
```

### 3. GitHubOps - GitHub API Interactions

**Real Implementation**: `RealGitHubOps()`
**Dry-Run Wrapper**: `DryRunGitHubOps(wrapped)`
**Fake Implementation**: `FakeGitHubOps(...)`

**Constructor Parameters**:

```python
FakeGitHubOps(
    prs: dict[str, PullRequestInfo] = {},
)
```

**Common Patterns**:

```python
# Pattern 1: No PRs
github_ops = FakeGitHubOps()

# Pattern 2: Pre-configured PRs
from workstack.core.github_ops import PullRequestInfo

github_ops = FakeGitHubOps(
    prs={
        "feature-branch": PullRequestInfo(
            number=123,
            state="OPEN",
            url="https://github.com/owner/repo/pull/123",
            is_draft=False,
            checks_passing=True,
            owner="owner",
            repo="repo",
        ),
    }
)
```

### 4. GraphiteOps - Graphite Tool Operations

**Real Implementation**: `RealGraphiteOps()`
**Dry-Run Wrapper**: `DryRunGraphiteOps(wrapped)`
**Fake Implementation**: `FakeGraphiteOps(...)`

**Constructor Parameters**:

```python
FakeGraphiteOps(
    stacks: dict[Path, list[str]] = {},
    current_branch_in_stack: dict[Path, bool] = {},
)
```

**Common Patterns**:

```python
# Pattern 1: No Graphite stacks
graphite_ops = FakeGraphiteOps()

# Pattern 2: Pre-configured stacks
graphite_ops = FakeGraphiteOps(
    stacks={repo: ["main", "feature-1", "feature-2"]},
    current_branch_in_stack={repo: True},
)
```

### 5. ShellOps - Shell Detection and Tool Availability

**Real Implementation**: `RealShellOps()`
**No Dry-Run Wrapper** (read-only operations)
**Fake Implementation**: `FakeShellOps(...)`

**Constructor Parameters**:

```python
FakeShellOps(
    detected_shell: tuple[str, Path] | None = None,
    installed_tools: dict[str, str] = {},
)
```

**Common Patterns**:

```python
# Pattern 1: No shell detected
shell_ops = FakeShellOps()

# Pattern 2: Bash shell detected
shell_ops = FakeShellOps(
    detected_shell=("bash", Path.home() / ".bashrc")
)

# Pattern 3: Tool installed
shell_ops = FakeShellOps(
    installed_tools={"gt": "/usr/local/bin/gt"}
)

# Pattern 4: Multiple tools
shell_ops = FakeShellOps(
    detected_shell=("zsh", Path.home() / ".zshrc"),
    installed_tools={
        "gt": "/usr/local/bin/gt",
        "gh": "/usr/local/bin/gh",
    }
)
```

## Testing Patterns

### Unit Test Pattern

```python
def test_command_behavior() -> None:
    """Test CLI command with fakes."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()

        # Configure fakes with initial state
        git_ops = FakeGitOps(git_common_dirs={cwd: cwd / ".git"})
        config_ops = FakeGlobalConfigOps(
            workstacks_root=cwd / "workstacks",
            use_graphite=False,
        )

        # Create context with all dependencies
        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            shell_ops=FakeShellOps(),
            dry_run=False,
        )

        # Invoke command
        result = runner.invoke(cli, ["command", "args"], obj=test_ctx)

        # Assert on results
        assert result.exit_code == 0
        assert "expected output" in result.output

        # Assert on mutations (if tracking enabled)
        assert len(git_ops.deleted_branches) == 1
```

### Integration Test Pattern

```python
def test_real_git_behavior(tmp_path: Path) -> None:
    """Test with real git operations."""
    repo = tmp_path / "repo"
    repo.mkdir()

    # Set up real git repo
    init_git_repo(repo, "main")
    subprocess.run(
        ["git", "worktree", "add", "-b", "feature", str(wt1)],
        cwd=repo,
        check=True,
    )

    # Use real GitOps
    git_ops = RealGitOps()
    worktrees = git_ops.list_worktrees(repo)

    assert len(worktrees) == 2
    assert any(wt.branch == "feature" for wt in worktrees)
```

### Dry-Run Test Pattern

```python
def test_dryrun_prevents_mutations() -> None:
    """Test dry-run mode prevents changes."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Use production context factory with dry_run=True
        ctx = create_context(dry_run=True)

        result = runner.invoke(
            cli,
            ["rm", "stack", "--force"],
            obj=ctx,
        )

        # Verify dry-run message printed
        assert "[DRY RUN]" in result.output or "[DRY RUN]" in result.stderr

        # Verify no actual changes (check filesystem)
        assert directory_still_exists
```

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Using mock.patch

```python
# DON'T DO THIS
def test_bad(monkeypatch):
    monkeypatch.setattr("module.function", lambda: "fake")
    result = function_under_test()
```

**Why it's bad**: Tight coupling to implementation details, fragile tests.

**Do this instead**:

```python
# DO THIS
def test_good():
    fake_ops = FakeShellOps(installed_tools={"tool": "/path"})
    ctx = WorkstackContext(..., shell_ops=fake_ops, ...)
    result = function_under_test(ctx)
```

### ❌ Anti-Pattern 2: Mutating Private Attributes

```python
# DON'T DO THIS
def test_bad():
    ops = RealGlobalConfigOps()
    ops._path = test_path  # Violates encapsulation
```

**Do this instead**:

```python
# DO THIS
def test_good():
    ops = FakeGlobalConfigOps(...)  # Constructor injection
```

### ❌ Anti-Pattern 3: Not Using Context Injection

```python
# DON'T DO THIS
def test_bad():
    result = runner.invoke(cli, ["command"])  # Uses production context
```

**Do this instead**:

```python
# DO THIS
def test_good():
    test_ctx = create_test_context(...)  # Or WorkstackContext(...)
    result = runner.invoke(cli, ["command"], obj=test_ctx)
```

## State Mutation in Fakes

### When Fakes Need Mutation

Some operations require mutating state to simulate external systems:

- Git operations (add/remove worktrees, checkout branches)
- Configuration updates (set values)

### Mutation vs Immutability

- **Initial State**: Always via constructor (immutable after construction)
- **Runtime State**: Modified through operation methods (mutable)
- **Mutation Tracking**: Exposed via read-only properties for assertions

### Example: Testing Mutations

```python
def test_branch_deletion():
    # Initial state via constructor
    git_ops = FakeGitOps(
        worktrees={repo: [WorktreeInfo(path=wt, branch="feature")]},
        git_common_dirs={repo: repo / ".git"},
    )

    # Verify initial state
    assert len(git_ops.list_worktrees(repo)) == 1

    # Perform mutation
    git_ops.delete_branch(repo, "feature", force=True)

    # Verify mutation via tracking property
    assert "feature" in git_ops.deleted_branches
    assert len(git_ops.deleted_branches) == 1
```

## Decision Tree

```
Need to test CLI command?
├─ Unit test (fast, isolated logic)
│  └─ Use Fake* classes
│     └─ Configure state via constructor
│        └─ Inject via WorkstackContext
│           └─ Pass as obj= to runner.invoke()
│
└─ Integration test (verify real system behavior)
   └─ Use Real* classes
      └─ Set up with actual commands (git, etc.)
         └─ Use tmp_path for isolation
            └─ Verify actual filesystem/system changes
```

## Helper Functions

### create_test_context()

Located in `tests/fakes/context.py`:

```python
from tests.fakes.context import create_test_context

# Minimal context (all fakes with defaults)
ctx = create_test_context()

# Custom git_ops
ctx = create_test_context(
    git_ops=FakeGitOps(worktrees={...})
)

# Custom config_ops
ctx = create_test_context(
    global_config_ops=FakeGlobalConfigOps(
        workstacks_root=Path("/tmp/ws")
    )
)

# Dry-run mode
ctx = create_test_context(dry_run=True)
```

## Common Test Fixtures

Recommended fixtures to add to `conftest.py`:

```python
@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    """Create a fake git repository for testing."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo

@pytest.fixture
def test_context() -> WorkstackContext:
    """Create minimal test context with all fakes."""
    return create_test_context()
```

## Summary

**Key Principles**:

1. Use ABC-based interfaces (not Protocol)
2. Inject dependencies through constructor (no mutation after creation, except for state-tracking operations)
3. Three implementations: Real, Dry-Run (for writes), Fake (for tests)
4. No mock.patch or monkeypatch (except documented edge cases)
5. Unit tests use Fakes, Integration tests use Reals
6. Mutation tracking via read-only properties

**When in Doubt**:

- Use `create_test_context()` helper
- Configure fakes via constructor parameters
- Inject via `obj=test_ctx` to Click commands
- Assert on results and mutation tracking properties

````

**Files to Create**:
- `.agent/docs/TESTING.md` (comprehensive guide above)

**Success Criteria**:
- Complete documentation with all 5 dependency categories
- Examples for all common testing patterns
- Anti-patterns documented
- Decision tree for choosing test approach

---

### Task 4.2: Enhance FakeGitOps Documentation

**Location**: `tests/fakes/gitops.py`

**Add comprehensive docstring**:

```python
class FakeGitOps(GitOps):
    """In-memory fake implementation of git operations.

    State Management:
    -----------------
    This fake maintains mutable state to simulate git's stateful behavior.
    Operations like add_worktree, checkout_branch modify internal state.
    State changes are visible to subsequent method calls within the same test.

    When to Use Mutation:
    --------------------
    - Operations that simulate stateful external systems (git, databases)
    - When tests need to verify sequences of operations
    - When simulating side effects visible to production code

    Constructor Injection:
    ---------------------
    All INITIAL state is provided via constructor (immutable after construction).
    Runtime mutations occur through operation methods.
    Tests should construct fakes with complete initial state.

    Mutation Tracking:
    -----------------
    This fake tracks mutations for test assertions via read-only properties:
    - deleted_branches: Branches deleted via delete_branch()
    - added_worktrees: Worktrees added via add_worktree()
    - removed_worktrees: Worktrees removed via remove_worktree()
    - checked_out_branches: Branches checked out via checkout_branch()

    Examples:
    ---------
        # Initial state via constructor
        git_ops = FakeGitOps(
            worktrees={repo: [WorktreeInfo(path=wt1, branch="main")]},
            current_branches={wt1: "main"},
            git_common_dirs={repo: repo / ".git"},
        )

        # Mutation through operation
        git_ops.add_worktree(repo, wt2, branch="feature", ...)

        # Verify mutation
        assert len(git_ops.list_worktrees(repo)) == 2
        assert (wt2, "feature") in git_ops.added_worktrees

        # Verify sequence of operations
        git_ops.checkout_branch(repo, "feature")
        git_ops.delete_branch(repo, "old-feature", force=True)
        assert (repo, "feature") in git_ops.checked_out_branches
        assert "old-feature" in git_ops.deleted_branches
    """
````

**Files to Update**:

- `tests/fakes/gitops.py` - Add comprehensive docstring

**Success Criteria**:

- Docstring explains mutation semantics
- Examples cover common patterns
- Mutation tracking properties documented

---

### Task 4.3: Update tests/CLAUDE.md

**Location**: `tests/CLAUDE.md`

**Update to reference new documentation**:

```markdown
# Test Structure Documentation

For comprehensive testing patterns and architecture, see:
**[.agent/docs/TESTING.md](../.agent/docs/TESTING.md)**

## Quick Commands

Run all tests: `uv run pytest`
Run specific test: `uv run pytest tests/commands/test_rm.py::test_rm_force_removes_directory`
Run with coverage: `uv run pytest --cov=workstack`

## Test Organization

- `tests/commands/` - CLI command tests (unit tests with fakes)
- `tests/core/` - Core logic unit tests
- `tests/integration/` - Integration tests with real git
- `tests/fakes/` - Fake implementations for dependency injection

## Quick Reference

| Need to...                      | See                                                                                                   |
| ------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Understand testing architecture | [.agent/docs/TESTING.md](../.agent/docs/TESTING.md)                                                   |
| Write a new CLI command test    | [.agent/docs/TESTING.md#unit-test-pattern](../.agent/docs/TESTING.md#unit-test-pattern)               |
| Test real git behavior          | [.agent/docs/TESTING.md#integration-test-pattern](../.agent/docs/TESTING.md#integration-test-pattern) |
| Test dry-run mode               | [.agent/docs/TESTING.md#dry-run-test-pattern](../.agent/docs/TESTING.md#dry-run-test-pattern)         |
| Configure fakes                 | [.agent/docs/TESTING.md#dependency-categories](../.agent/docs/TESTING.md#dependency-categories)       |

## Testing Principles

1. **Use dependency injection** - All tests inject fakes via WorkstackContext
2. **No mock.patch** - Use FakeShellOps, FakeGitOps, etc. instead
3. **Constructor injection** - All fake state configured at construction
4. **Mutation tracking** - Use read-only properties for assertions (e.g., `git_ops.deleted_branches`)
5. **Three implementations** - Real (production), Dry-Run (safety), Fake (testing)

For complete details, see [.agent/docs/TESTING.md](../.agent/docs/TESTING.md).
```

**Files to Update**:

- `tests/CLAUDE.md` - Simplify and point to comprehensive docs

**Success Criteria**:

- Clear reference to `.agent/docs/TESTING.md`
- Quick command reference maintained
- Links to specific sections in TESTING.md

---

### Task 4.4: Update Main CLAUDE.md

**Location**: `CLAUDE.md`

**Add testing documentation reference**:

```markdown
## 📚 Quick Reference

| Need help with...     | See documentation                                                      |
| --------------------- | ---------------------------------------------------------------------- |
| **Code examples**     | [.agent/docs/PATTERNS.md](.agent/docs/PATTERNS.md)                     |
| **Exception details** | [.agent/docs/EXCEPTION_HANDLING.md](.agent/docs/EXCEPTION_HANDLING.md) |
| **Quick lookup**      | [.agent/docs/QUICK_REFERENCE.md](.agent/docs/QUICK_REFERENCE.md)       |
| **Writing tests**     | [.agent/docs/TESTING.md](.agent/docs/TESTING.md)                       |
```

**Files to Update**:

- `CLAUDE.md` - Update Quick Reference table

**Success Criteria**:

- Testing documentation linked in main CLAUDE.md
- Consistent with other documentation links

---

## Implementation Sequence for Phases 3 & 4

### Recommended Order

1. **Task 3.1**: Add mutation tracking (foundation for better tests)
2. **Task 4.2**: Document mutations in FakeGitOps (while fresh in mind)
3. **Task 4.1**: Create comprehensive TESTING.md (captures all patterns)
4. **Task 3.2**: Create dry-run integration tests (validates dry-run wrappers)
5. **Task 3.3**: Run full test suite (verify everything works)
6. **Task 4.3**: Update tests/CLAUDE.md (simplify to point to new docs)
7. **Task 4.4**: Update main CLAUDE.md (add testing reference)

### Why This Order

- Mutation tracking enables better test examples in documentation
- Documentation task (4.1) done early to guide integration test writing (3.2)
- Integration tests validate the dry-run wrappers added in Phase 2
- Final documentation updates (4.3, 4.4) after all implementation complete

---

## Success Criteria (Overall)

### Quantitative Metrics

- ✅ Zero uses of `mock.patch` or `monkeypatch` (achieved in Phase 1)
- ✅ All 5 dependency categories have Real, Dry-Run, and Fake (achieved in Phase 2)
- [ ] Mutation tracking properties available in FakeGitOps
- [ ] At least 5 dry-run integration tests
- [ ] 100% of CLI commands have dry-run test coverage
- [ ] All tests pass (`uv run pytest`)
- [ ] Pyright checks pass (`uv run pyright`)

### Qualitative Metrics

- ✅ Test code follows documented patterns consistently
- [ ] Agents can understand test structure from documentation alone
- [ ] New tests can be written without referring to existing tests
- [ ] Mutation patterns are explicit and well-explained

### Documentation Completeness

- [ ] `.agent/docs/TESTING.md` contains all patterns
- [ ] Each dependency category has constructor documentation with examples
- [ ] Anti-patterns are clearly documented with alternatives
- [ ] Examples cover all common scenarios (unit, integration, dry-run)
- [ ] Decision tree guides test approach selection

---

## Notes

### Parallel Work Opportunities

Within Phase 3:

- Task 3.1 and 3.2 can be done in parallel

Within Phase 4:

- Tasks 4.1, 4.2, 4.3, 4.4 can all be done in parallel

### Testing Strategy

After each task:

1. Run: `uv run pytest tests/`
2. Run: `uv run pyright src/ tests/`
3. Manual smoke test of affected commands
4. Check test execution time (no performance regressions)

### Estimated Effort

Phase 3: Medium complexity

- Mutation tracking: Straightforward addition to existing fake
- Integration tests: Requires understanding of dry-run wrappers

Phase 4: Low-Medium complexity

- Documentation writing: Time-consuming but straightforward
- Main challenge: Ensuring examples are accurate and complete
