# dev_cli_core → devclikit Package Extraction - Implementation Plan

## Summary

Extract the `dev_cli_core` module from the `workstack` monolith into a standalone `devclikit` package within a uv workspace. This enables independent development, versioning, and potential PyPI publication while maintaining all existing functionality in workstack.

## Components

- **Workspace Root**: Root-level `pyproject.toml` defining workspace structure
- **devclikit Package**: New package at `packages/devclikit/` with moved core code
- **workstack Package**: Updated main package with new imports and workspace dependency
- **Migration Layer**: Import updates across all consuming code in workstack

## Phases

### Phase 1: Workspace Structure Setup

Create the uv workspace foundation without moving code yet.

- Add workspace configuration to root `pyproject.toml`
- Create `packages/devclikit/` directory structure
- Create initial `packages/devclikit/pyproject.toml` with metadata
- Verify workspace detection: `uv tree` should show both packages

**Verify**: `uv tree` shows workspace members, `uv sync` succeeds

### Phase 2: Code Migration

Move `dev_cli_core` code to new package location.

- Move `src/dev_cli_core/*` to `packages/devclikit/src/devclikit/`
- Update `packages/devclikit/src/devclikit/__init__.py` exports
- Remove `src/dev_cli_core/` directory
- Add workspace dependency in `workstack/pyproject.toml`

**Verify**: Directory structure matches workspace layout, old directory removed

### Phase 3: Import Updates

Update all imports from `dev_cli_core` to `devclikit`.

- Update `src/workstack/dev_cli/__main__.py` imports
- Update `src/workstack/dev_cli/commands/*/command.py` imports
- Update any tests importing `dev_cli_core`
- Update ruff/pyright configuration to remove `dev_cli_core` from known-first-party

**Verify**: `uv run pyright` passes, `ruff check` passes

### Phase 4: Validation & Documentation

Ensure everything works and document the new structure.

- Run full test suite: `uv run pytest`
- Test CLI functionality: `uv run workstack-dev --help`
- Test shell completion installation
- Update root README.md to mention workspace structure

**Verify**: All tests pass, CLI works identically to before

## Key Interfaces

### Workspace Configuration (Root pyproject.toml)

```toml
[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
devclikit = { workspace = true }
```

### devclikit Package Metadata

```toml
[project]
name = "devclikit"
version = "0.1.10"
description = "Framework for building development CLIs with PEP 723 script support"
requires-python = ">=3.13"
dependencies = [
    "click>=8.1.7",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Updated workstack Dependency

```toml
[project]
dependencies = [
    "devclikit",  # workspace dependency
    # ... other deps
]
```

### Public API (devclikit/**init**.py)

```python
"""DevCliKit: Framework for building development CLIs."""

from devclikit.cli_factory import create_cli
from devclikit.completion import add_completion_commands
from devclikit.exceptions import (
    DevCliError,
    CommandLoadError,
    ScriptExecutionError,
)
from devclikit.loader import load_commands
from devclikit.runner import run_pep723_script, validate_pep723_script
from devclikit.utils import ensure_directory, is_valid_command_name

__all__ = [
    "create_cli",
    "load_commands",
    "run_pep723_script",
    "validate_pep723_script",
    "add_completion_commands",
    "ensure_directory",
    "is_valid_command_name",
    "DevCliError",
    "CommandLoadError",
    "ScriptExecutionError",
]
```

## Technical Decisions

**1. Examples Location**: Move to `packages/devclikit/examples/` for self-contained package

- Reasoning: Makes devclikit independently demonstrable and testable
- **Decision**: Keep hello_world example in devclikit

**2. Version Syncing**: Manual for now, automate later if needed

- **Decision**: Track workstack's version (0.1.10), evolve together

**3. Test Suite**: Create minimal devclikit tests, keep workstack integration tests

- Unit tests for devclikit core functionality
- Integration tests remain in workstack

**4. PyPI Publishing**: Design for future publication, don't publish yet

- Use proper package metadata from day 1
- Add LICENSE, README to devclikit when ready to publish

**5. Build System**: Use hatchling (matches existing stack)

- Consistent with uv best practices
- Simple, no custom build steps needed

**6. Workspace Structure**: Keep workstack at root level

- **Decision**: Workstack stays at `src/workstack/`, only devclikit moves to `packages/`

**7. Ruff Configuration**: Update `known-first-party` to include `devclikit`

```toml
[tool.ruff.lint.isort]
known-first-party = ["workstack", "devclikit"]
```

## Open Questions

1. **Should devclikit version track workstack or be independent?**
   - **RESOLVED**: Track workstack's version (0.1.10)

2. **Move examples or keep in workstack as documentation?**
   - **RESOLVED**: Keep hello_world example in devclikit

3. **Should we create a `packages/workstack/` and move src/ there for consistency?**
   - **RESOLVED**: Keep workstack at root

4. **Should devclikit have its own GitHub repo eventually?**
   - Monorepo: Easier coordination, shared CI
   - Separate: Clear boundaries, independent release cycles
   - **DEFERRED**: Stay in monorepo for now

5. **How to handle shared dev dependencies (ruff, pyright)?**
   - Root-level: Shared across workspace
   - Per-package: Independent tooling versions
   - **DECISION**: Keep at root level in workstack's dependency-groups

## Risks & Mitigations

**Circular Dependencies**: Workspace resolves local packages first

- Mitigation: Explicit workspace sources in root pyproject.toml

**Import Breakage**: Missing import updates cause runtime failures

- Mitigation: Grep for all `dev_cli_core` imports before Phase 3
- Mitigation: Run pyright after every import change

**Test Failures**: Tests may hardcode old paths or imports

- Mitigation: Run test suite after Phase 3, fix incrementally

**Version Drift**: Packages get out of sync

- Mitigation: Document version update process in workspace README

## Migration Checklist

**Pre-flight**:

- [ ] Commit current working state
- [ ] Create git branch: `workspace-extract-devclikit`
- [ ] Verify all tests pass before starting

**Phase 1 - Structure**:

- [ ] Root pyproject.toml workspace config
- [ ] Create packages/devclikit/ directories
- [ ] Create packages/devclikit/pyproject.toml
- [ ] Verify: `uv tree` shows workspace

**Phase 2 - Migration**:

- [ ] Move src/dev_cli_core → packages/devclikit/src/devclikit
- [ ] Update devclikit **init**.py exports
- [ ] Remove old src/dev_cli_core/
- [ ] Add workspace dependency to workstack

**Phase 3 - Imports**:

- [ ] Find all dev_cli_core imports: `rg "from dev_cli_core" "import dev_cli_core"`
- [ ] Update workstack/dev_cli imports
- [ ] Update test imports
- [ ] Update ruff known-first-party
- [ ] Verify: `uv run pyright`

**Phase 4 - Validation**:

- [ ] Run: `uv run pytest`
- [ ] Test: `uv run workstack-dev --help`
- [ ] Test: Shell completion commands
- [ ] Update README.md
