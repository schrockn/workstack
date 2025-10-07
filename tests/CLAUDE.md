# Test Structure Documentation

This document explains how to write tests for the workstack project using dependency injection patterns.

## Core Testing Principles

### 1. Dependency Injection Through Click Context

All CLI commands receive a `WorkstackContext` frozen dataclass containing injected dependencies:

```python
@dataclass(frozen=True)
class WorkstackContext:
    git_ops: GitOps
    global_config_ops: GlobalConfigOps
    github_ops: GitHubOps
    graphite_ops: GraphiteOps
    dry_run: bool
```

**Why**: This allows tests to inject fake implementations without mocking or monkeypatching.

### 2. Unit Tests: Use Fakes with Constructor-Injected State

Fakes are in-memory implementations that accept all state through constructor parameters:

```python
def test_rm_force_removes_directory() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        workstacks_root = cwd / "workstacks"

        # Build fake with pre-configured state
        git_ops = FakeGitOps(
            git_common_dirs={cwd: cwd / ".git"}
        )

        global_config_ops = FakeGlobalConfigOps(
            workstacks_root=workstacks_root,
            use_graphite=False,
        )

        # Create context and inject via Click
        # Note: In real tests, you'll need to provide all required fields
        # or use helper functions to create minimal contexts
        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        result = runner.invoke(cli, ["rm", "foo", "-f"], obj=test_ctx)
```

**Key Points**:

- Construct fakes with **all required state upfront** using keyword arguments
- No setter methods (except for special cases like git operations that mutate state)
- Pass context via `obj=test_ctx` to Click's `invoke()`

### 3. Integration Tests: Use Real Implementations

Integration tests verify real git interactions using `RealGitOps`:

```python
def test_list_worktrees_multiple(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")  # Helper that runs actual git commands

    # Create real worktrees with actual git
    subprocess.run(["git", "worktree", "add", "-b", "feature-1", str(wt1)], ...)

    # Use real implementation
    git_ops = RealGitOps()
    worktrees = git_ops.list_worktrees(repo)

    assert len(worktrees) == 3
```

**Key Points**:

- Use `subprocess.run()` to set up real git state
- Use `tmp_path` fixture for isolated filesystem
- Test actual git command behavior, not fakes

### 4. Fake State Configuration Patterns

#### Pattern A: Minimal State for Simple Tests

```python
git_ops = FakeGitOps(
    git_common_dirs={cwd: cwd / ".git"}
)
```

#### Pattern B: Pre-configured Worktrees

```python
git_ops = FakeGitOps(
    worktrees={
        cwd: [
            WorktreeInfo(path=cwd, branch="main"),
            WorktreeInfo(path=work_dir / "foo", branch="foo"),
        ],
    },
    git_common_dirs={cwd: cwd / ".git"},
)
```

#### Pattern C: Branch State Configuration

```python
git_ops = FakeGitOps(
    worktrees={...},
    current_branches={
        cwd: "main",
        worktree_path: "schrockn/ts-phase-3",
    },
    default_branches={
        repo_root: "main"
    },
    git_common_dirs={...}
)
```

### 5. Global Config Testing Patterns

#### Pattern A: Config Exists with Values

```python
global_config_ops = FakeGlobalConfigOps(
    workstacks_root=Path("/tmp/workstacks"),
    use_graphite=True,
    shell_setup_complete=False,
)
```

#### Pattern B: Config Doesn't Exist

```python
global_config_ops = FakeGlobalConfigOps(exists=False)

# This will raise FileNotFoundError
with pytest.raises(FileNotFoundError):
    global_config_ops.get_workstacks_root()
```

#### Pattern C: Testing Config Creation

```python
global_config_ops = FakeGlobalConfigOps(exists=False)

# Simulate creating config
global_config_ops.set(
    workstacks_root=Path("/tmp/workstacks"),
    use_graphite=False,
)

# Now config "exists" and has values
assert global_config_ops.get_workstacks_root() == Path("/tmp/workstacks")
```

### 6. Testing Click Commands with Context

Standard pattern for command testing:

```python
def test_command_behavior() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        # 1. Set up filesystem state
        # 2. Configure fakes with state
        git_ops = FakeGitOps(...)
        global_config_ops = FakeGlobalConfigOps(...)

        # 3. Create context
        test_ctx = WorkstackContext(
            git_ops=git_ops,
            global_config_ops=global_config_ops,
            github_ops=FakeGitHubOps(),
            graphite_ops=FakeGraphiteOps(),
            dry_run=False,
        )

        # 4. Invoke command with context
        result = runner.invoke(cli, ["command", "args"], obj=test_ctx)

        # 5. Assert on result
        assert result.exit_code == 0
        assert "expected output" in result.output
```

### 7. When Fakes Need Mutation

Some operations (like git worktree management) require mutating state:

```python
class FakeGitOps(GitOps):
    def add_worktree(self, repo_root: Path, path: Path, ...) -> None:
        """Add a new worktree (mutates internal state)."""
        if repo_root not in self._worktrees:
            self._worktrees[repo_root] = []
        self._worktrees[repo_root].append(WorktreeInfo(path=path, branch=branch))
```

**Why**: Git operations have side effects that tests need to verify. The fake simulates these mutations in-memory.

### 8. Avoid These Anti-Patterns

#### ❌ Don't Monkeypatch Functions

```python
# BAD
def test_something(monkeypatch):
    monkeypatch.setattr("module.function", lambda: "fake_value")
```

**Fix**: Inject the dependency through an ABC interface

#### ❌ Don't Mock Magic Attributes

```python
# BAD
with mock.patch("module.__file__", "/fake/path"):
    result = function_that_uses_file()
```

**Fix**: Add explicit path parameter to function

#### ❌ Don't Mutate Private Attributes

```python
# BAD
real_ops = RealGlobalConfigOps()
real_ops._path = test_path  # Violates encapsulation
```

**Fix**: Add constructor parameter for injection

#### ✅ Exception: Edge Case Testing

```python
# ACCEPTABLE - testing edge case where stdlib behavior needs control
def test_edge_case(monkeypatch):
    # Document why this is necessary
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
```

### 9. Testing with Subprocess Integration

When commands use subprocess internally, tests can verify by checking filesystem state:

```python
def test_create_with_plan_file(tmp_path: Path) -> None:
    # Set up isolated environment
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)

    # Run actual CLI via subprocess
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "--plan", "plan.md"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    # Verify filesystem changes
    assert worktree_path.exists()
    assert (worktree_path / ".PLAN.md").exists()
```

### 10. Summary: Decision Tree

```
Need to test CLI command?
├─ Unit test (fast, isolated logic)
│  └─ Use FakeGitOps + FakeGlobalConfigOps
│     └─ Configure state via constructor
│        └─ Inject via WorkstackContext
│           └─ Pass as obj= to runner.invoke()
│
└─ Integration test (verify real git behavior)
   └─ Use RealGitOps
      └─ Set up with actual git commands
         └─ Use tmp_path for isolation
            └─ Verify actual filesystem/git changes
```

**Golden Rule**: If you find yourself **repeatedly and excessively** using monkeypatch or mock, you're probably missing an abstraction that should be injected via the context.
