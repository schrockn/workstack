# Documentation Review: Shell Integration Refactor

**Branch**: `workstack-sync-shell-integration-plan`
**Base Branch**: `main`
**Review Date**: 2025-10-08

---

## Executive Summary

**Status**: 2 documentation files need updates

This branch implements a significant architectural improvement to shell integration by introducing a unified `__shell` handler that consolidates shell-integrated commands (`switch`, `sync`, `create`) under a single entry point. This replaces the previous pattern where each command had its own hidden variant (e.g., `__switch`).

The agent-facing architecture documentation needs updates to reflect this new pattern, which will help developers and AI assistants understand and extend the shell integration system.

---

## Code Changes Overview

### What Changed

**New Architecture Pattern**:

- **Old**: Each shell-integrated command had its own hidden variant (`__switch` for `switch`)
- **New**: Single unified `__shell` command routes to any command with `--script` flag

### Key Changes

1. **New Module**: `src/workstack/shell_integration/handler.py`
   - Unified handler logic for shell integration
   - Routes requests to appropriate commands
   - Determines passthrough vs. script output
   - Defines `ShellIntegrationResult` dataclass
   - Exports `PASSTHROUGH_MARKER` constant

2. **New Command**: `src/workstack/commands/shell_integration.py`
   - Single hidden `__shell` command entry point
   - Replaces individual hidden commands
   - Calls `handle_shell_request()` from handler module

3. **Modified Commands**: Added `--script` flag support to:
   - `src/workstack/commands/switch.py` - Outputs shell activation script
   - `src/workstack/commands/sync.py` - Outputs directory change script when worktree deleted
   - `src/workstack/commands/create.py` - Outputs cd script to new worktree

4. **Removed**: `hidden_switch_cmd` from `commands/switch.py`

5. **Updated Shell Wrappers**: All shell wrapper scripts now call:
   ```bash
   workstack __shell <command> <args>
   ```
   Instead of command-specific hidden commands like `workstack __switch <args>`.

### Benefits of New Pattern

**DRY Principle**: Single handler instead of per-command hidden commands

**Extensible**: Adding new shell-integrated commands is trivial:

```python
# Just add --script flag to your command
@click.option("--script", is_flag=True, hidden=True)
def new_cmd(..., script: bool):
    if script:
        click.echo(generate_script())
```

**Consistent**: All shell-integrated commands follow the same pattern

**Testable**: Centralized routing logic easier to test and reason about

**Maintainable**: Single source of truth for shell integration behavior

---

## The `__shell` Command

### Purpose

The `__shell` command is a **hidden internal command** used exclusively by shell wrapper functions. It provides a unified entry point for all commands that need shell integration (directory changes, environment activation, etc.).

### Rationale

**Problem**: Shell functions cannot change the parent shell's directory directly. When you run `workstack switch my-feature`, the subprocess can't `cd` to the new directory in your interactive shell.

**Solution**: The shell wrapper function calls `workstack __shell switch my-feature`, which outputs shell code that the wrapper then `eval`s in the current shell context.

**Why a single `__shell` command?**

1. **Avoid duplication**: Previously, each command needed its own hidden variant (`__switch`, potentially `__sync`, `__create`, etc.)
2. **Consistent protocol**: All shell-integrated commands use the same passthrough marker and output format
3. **Easier to extend**: Adding shell integration to a new command requires only adding a `--script` flag
4. **Clearer separation**: Shell integration logic lives in one place (`handler.py`) instead of scattered across command files

### How It Works

```
User types: workstack switch my-feature
     ↓
Shell wrapper intercepts (bash_wrapper.sh / zsh_wrapper.sh)
     ↓
Calls: workstack __shell switch my-feature
     ↓
handler.py routes to: switch_cmd(["my-feature", "--script"])
     ↓
switch_cmd outputs shell script to stdout
     ↓
Shell wrapper evals the script (cd + env activation)
     ↓
User is now in the new worktree directory
```

### Special Cases

**Passthrough Marker**: When `__shell` outputs `__WORKSTACK_PASSTHROUGH__`, the shell wrapper knows to call the regular command instead of eval'ing output. This happens for:

- Help flags (`-h`, `--help`)
- Explicit `--script` flag (user called it directly)
- Errors (let normal error handling show the message)

**Example**:

```bash
$ workstack switch --help
# Shell wrapper calls: workstack __shell switch --help
# handler.py detects --help, returns passthrough marker
# Shell wrapper calls: workstack switch --help
# User sees normal help output
```

### Usage (Internal Only)

```bash
# Called by shell wrappers only:
workstack __shell switch my-feature
workstack __shell sync
workstack __shell create new-feature

# Users should never call this directly
# (it's hidden from --help output)
```

---

## Documentation Files Requiring Updates

### 1. `.agent/FEATURE_INDEX.md`

**Impact**: MEDIUM
**Location**: Lines 141-149 (Shell Integration section)
**Issue**: Missing new shell integration handler module and updated pattern

#### Current State

```markdown
## Shell Integration

| Feature               | Implementation                                      | Description                         |
| --------------------- | --------------------------------------------------- | ----------------------------------- |
| Bash activation       | `src/workstack/shell_integration/bash_wrapper.sh`   | Source in `.bashrc`                 |
| Zsh activation        | `src/workstack/shell_integration/zsh_wrapper.sh`    | Source in `.zshrc`                  |
| Fish activation       | `src/workstack/shell_integration/fish_wrapper.fish` | Source in `config.fish`             |
| Completion generation | `src/workstack/commands/completion.py`              | Generate shell-specific completions |
```

#### Required Changes

Add two new rows to the Shell Integration table:

```markdown
| Shell handler | `src/workstack/shell_integration/handler.py` | Unified handler for shell-integrated commands |
| Shell command entry | `src/workstack/commands/shell_integration.py` | Hidden `__shell` command for wrappers |
```

Add note after table:

```markdown
**Shell Integration Pattern**: The `switch`, `sync`, and `create` commands support a hidden `--script` flag that outputs shell code instead of regular output. Shell wrapper functions use the unified `__shell` command to invoke these commands in script mode.
```

---

### 2. `.agent/docs/MODULE_MAP.md`

**Impact**: MEDIUM
**Location**: Multiple sections
**Issue**: Documentation describes old `__switch` pattern; new unified pattern not documented

#### Section A: Visual Hierarchy (Line 58)

**Current State**:

```markdown
└─── Support
├─ presets/ ................... Configuration presets (dagster, generic, etc.)
└─ shell_integration/ ......... Shell completion and activation scripts
```

**Required Change**:

```markdown
└─── Support
├─ presets/ ................... Configuration presets (dagster, generic, etc.)
└─ shell_integration/ ......... Shell integration system
├─ bash_wrapper.sh ........ Bash shell function wrapper
├─ zsh_wrapper.sh ......... Zsh shell function wrapper
├─ fish_wrapper.fish ...... Fish shell function wrapper
└─ handler.py ............. Unified shell integration handler
```

#### Section B: Commands List (Line 30-41)

Add after `completion.py`:

```markdown
│ ├─ shell_integration.py ... Hidden \_\_shell command for wrappers
```

#### Section C: switch.py Documentation (Lines 134-162)

**Current State**:

```markdown
**Responsibilities**:

- Switch between worktrees
- Generate shell activation scripts
- Hidden `--internal` variant for shell integration
- Display available worktrees if name ambiguous

**Key Functions**:

- `switch_cmd()` - Main command handler
- `_hidden_switch_cmd()` - Internal variant for shell
- Activation script generation logic
```

**Required Change**:

```markdown
**Responsibilities**:

- Switch between worktrees
- Generate shell activation scripts (via `--script` flag)
- Display available worktrees if name ambiguous

**Key Functions**:

- `switch_cmd()` - Main command handler with optional `--script` flag
- `_render_activation_script()` - Generate shell activation script

**Shell Integration**: Works through unified `__shell` handler (see `shell_integration.py`)
```

#### Section D: sync.py Documentation (Lines 287-314)

**Current State**:

```markdown
**Responsibilities**:

- Sync with graphite repository
- Identify merged PRs
- Suggest cleanup of merged worktrees
- Interactive removal prompts
```

**Required Change**: Add shell integration responsibility:

```markdown
**Responsibilities**:

- Sync with graphite repository
- Identify merged PRs
- Suggest cleanup of merged worktrees
- Interactive removal prompts
- Generate directory change script when worktree deleted (via `--script` flag)

**Key Functions**:

- `sync_cmd()` - Main command handler with optional `--script` flag
- `_emit()` - Output messages to stdout or stderr based on script mode
- `_render_return_to_root_script()` - Generate cd script to return to root

**Shell Integration**: Supports `--script` flag for automatic directory change when current worktree is deleted during sync
```

#### Section E: create.py Documentation (Lines 100-131)

Add to responsibilities and key functions:

```markdown
**Responsibilities**:

- Create new worktree with branch
- Support plan file (`--plan` flag)
- Set up environment variables
- Run post-create commands
- Handle branch naming conflicts
- Generate directory change script (via `--script` flag)

**Key Functions**:

- `create_cmd()` - Main command handler with optional `--script` flag
- `_generate_worktree_name()` - Generate name from branch
- `_render_cd_script()` - Generate shell cd script to new worktree
- Various validation helpers

**Shell Integration**: Supports `--script` flag for automatic directory change to newly created worktree
```

#### Section F: Add New Module Documentation (After line 440)

Add complete documentation for the new shell integration command:

````markdown
---

#### `commands/shell_integration.py`

**Purpose**: Implements hidden `workstack __shell` command for shell integration.

**Responsibilities**:

- Unified entry point for shell wrapper scripts
- Routes commands to appropriate handlers with `--script` flag
- Emits passthrough marker for help/error cases
- Supports `switch`, `sync`, and `create` commands

**Key Functions**:

- `hidden_shell_cmd()` - Main hidden command handler
- Uses `handler.py` for routing logic

**Dependencies**:

- `shell_integration/handler.py` - For `handle_shell_request()`

**Usage** (internal, called by shell wrappers):

```bash
workstack __shell switch my-feature
workstack __shell sync
workstack __shell create new-feature
```
````

**Note**: Hidden command (not in `--help`), used only by shell wrapper functions.

**Rationale**: Provides unified shell integration protocol, avoiding per-command hidden variants. See [Shell Integration Pattern](#shell-integration-pattern) for details.

---

````

#### Section G: Add Core Layer Documentation (After line 593)

Add documentation for the handler module:

```markdown
---

#### `shell_integration/handler.py`

**Purpose**: Unified shell integration handler logic (Core Layer).

**Responsibilities**:

- Route shell wrapper requests to appropriate command handlers
- Add `--script` flag to commands for shell integration mode
- Determine when to passthrough vs. return script
- Handle help flags and error cases

**Key Types**:

```python
@dataclass(frozen=True)
class ShellIntegrationResult:
    passthrough: bool    # If true, shell wrapper calls regular command
    script: str | None   # Shell code to eval (cd commands, etc.)
    exit_code: int
````

**Key Functions**:

- `handle_shell_request(args)` - Main dispatcher for shell requests
  - Takes: Command args from shell wrapper
  - Returns: `ShellIntegrationResult` with passthrough decision and script
- `_invoke_hidden_command(command_name, args)` - Invoke command with `--script` flag
  - Detects help/error cases → passthrough
  - Otherwise runs command with `--script` → returns shell code

**Constants**:

- `PASSTHROUGH_MARKER: Final[str] = "__WORKSTACK_PASSTHROUGH__"` - Special marker that signals shell wrapper to call regular command instead of eval'ing output

**Dependencies**:

- `click.testing.CliRunner` - For invoking commands programmatically
- `commands/create.py` - For `create` command with `--script`
- `commands/switch.py` - For `switch_cmd` with `--script`
- `commands/sync.py` - For `sync_cmd` with `--script`
- `context.py` - For `create_context()`

**Used By**: `commands/shell_integration.py`

**Pattern**: Provides clean separation between shell integration logic and command logic. Commands only need to support `--script` flag; handler manages the routing and passthrough protocol.

**Example Flow**:

```
Shell wrapper → __shell switch my-feature
    ↓
handler.handle_shell_request(["switch", "my-feature"])
    ↓
_invoke_hidden_command("switch", ("my-feature",))
    ↓
CliRunner.invoke(switch_cmd, ["my-feature", "--script"])
    ↓
Returns ShellIntegrationResult(passthrough=False, script="cd ...; export ...", exit_code=0)
    ↓
Shell wrapper evals script
```

---

````

#### Section H: Shell Integration Pattern (New Section)

Add a new major section after "How to Navigate" explaining the pattern:

```markdown
---

## Shell Integration Pattern

### Overview

Commands that need to modify the parent shell's environment (cd, export) cannot do so from a subprocess. The shell integration pattern solves this by having commands output shell code that the wrapper function evals.

### Components

1. **Shell Wrappers** (`shell_integration/*.sh`, `*.fish`)
   - Intercept `workstack` commands in the user's shell
   - Call `workstack __shell <command> <args>`
   - Eval the output (unless passthrough marker detected)

2. **Hidden Command** (`commands/shell_integration.py`)
   - Single entry point: `workstack __shell`
   - Routes to handler for processing

3. **Handler** (`shell_integration/handler.py`)
   - Core routing logic
   - Invokes commands with `--script` flag
   - Returns `ShellIntegrationResult`

4. **Command Support** (commands with `--script` flag)
   - `switch` - Outputs cd + env activation
   - `sync` - Outputs cd to root if worktree deleted
   - `create` - Outputs cd to new worktree

### Protocol

**Normal Flow**:
````

User: workstack switch my-feature
↓
Wrapper: output=$(workstack __shell switch my-feature)
  ↓
Handler: Invokes switch_cmd --script
  ↓
switch_cmd: Outputs "cd /path/to/worktree; export ..."
  ↓
Wrapper: eval "$output"
↓
Result: User's shell is now in the worktree

```

**Passthrough Flow**:
```

User: workstack switch --help
↓
Wrapper: output=$(workstack \_\_shell switch --help)
↓
Handler: Detects --help, returns PASSTHROUGH_MARKER
↓
Wrapper: Detects marker, calls regular command
↓
Calls: workstack switch --help
↓
Result: Normal help output displayed

````

### Adding Shell Integration to a New Command

```python
@click.command("my-command")
@click.option("--script", is_flag=True, hidden=True)
@click.pass_obj
def my_cmd(ctx: WorkstackContext, script: bool) -> None:
    # Do normal work
    result = do_something()

    if script:
        # Output shell code for wrapper to eval
        click.echo(f"cd {some_path}")
    else:
        # Normal user-facing output
        click.echo(f"Done! You can now run: cd {some_path}")
````

That's it! The handler will automatically route `workstack __shell my-command args` to your command with `--script`.

### Why This Pattern?

**Before** (per-command hidden variants):

```
commands/switch.py:
  - switch_cmd()
  - hidden_switch_cmd()  # Duplicate logic

commands/sync.py:
  - sync_cmd()
  - hidden_sync_cmd()  # Duplicate logic

commands/create.py:
  - create()
  - hidden_create_cmd()  # Duplicate logic
```

**After** (unified handler):

```
commands/switch.py:
  - switch_cmd(script: bool)  # Single function

commands/sync.py:
  - sync_cmd(script: bool)  # Single function

commands/create.py:
  - create(script: bool)  # Single function

shell_integration/handler.py:
  - handle_shell_request()  # Single routing function
```

Benefits:

- Less code duplication
- Consistent behavior across commands
- Easier to add new shell-integrated commands
- Single source of truth for passthrough logic

---

```

---

## Documentation Files With No Required Updates

The following files were reviewed and require no changes:

### User-Facing Documentation

- **README.md** - Does not reference internal implementation details like `__switch` or shell integration architecture. User-facing command examples remain correct.

### High-Level Architecture

- **.agent/ARCHITECTURE.md** - Describes architectural layers and patterns at a high level without referencing specific command implementations. The ABC pattern, frozen dataclasses, and dependency injection principles remain unchanged.

- **.agent/GLOSSARY.md** - Term definitions (worktree, workstack, etc.) are not affected by implementation changes.

### Coding Standards

- **CLAUDE.md** - Project coding standards (type annotations, exception handling, import rules) remain applicable.

- **.agent/docs/PATTERNS.md** - Code pattern examples (dependency injection, context managers, etc.) are not affected by shell integration changes.

- **.agent/docs/EXCEPTION_HANDLING.md** - Exception handling guide remains applicable.

### Testing Documentation

- **tests/CLAUDE.md** - Testing patterns (fakes, dependency injection in tests) remain applicable. New tests follow existing patterns.

### Agent Instructions

- **AGENTS.md** - General agent-facing instructions not affected.

- **tests/AGENTS.md** - Test-specific agent instructions not affected.

---

## Recommendations

### Priority 1: Update `.agent/docs/MODULE_MAP.md`

**Rationale**: This is the most detailed architectural documentation. Developers and AI assistants looking to understand or extend shell integration will consult this file. The old `__switch` pattern is completely removed from the codebase, making the current documentation incorrect and misleading.

**Effort**: Medium (multiple sections to update, new sections to add)

**Impact**: High (affects understanding of entire shell integration system)

**Actions**:
1. Update visual hierarchy to show `handler.py`
2. Remove `_hidden_switch_cmd()` references from switch.py docs
3. Add `--script` flag to switch.py, sync.py, create.py docs
4. Add new module documentation for `shell_integration.py`
5. Add new core module documentation for `handler.py`
6. Add new "Shell Integration Pattern" section explaining the architecture

### Priority 2: Update `.agent/FEATURE_INDEX.md`

**Rationale**: This is the quick reference lookup table for finding features. Adding the new modules helps developers quickly locate the shell integration code.

**Effort**: Low (simple table additions)

**Impact**: Medium (improves discoverability)

**Actions**:
1. Add `handler.py` to Shell Integration table
2. Add `shell_integration.py` to Shell Integration table
3. Add note about `--script` flag pattern

### Testing

The branch already includes comprehensive tests for the new pattern:
- `tests/commands/test_plan.py` - Tests for `create --script`
- `tests/commands/test_switch.py` - Tests for `__shell switch` passthrough
- `tests/test_sync.py` - Tests for `sync --script` and shell integration
- Tests verify passthrough marker, script output, and error handling

No test documentation updates required.

---

## Impact Assessment

### Severity: MEDIUM

**Why MEDIUM and not HIGH?**
- User-facing functionality works correctly
- Changes are internal architectural improvements
- Existing features work the same from user perspective
- Only affects developers/AI assistants reading architecture docs

**Why MEDIUM and not LOW?**
- The old pattern (`__switch`) is completely removed
- Documentation describing removed code is misleading
- New pattern is architecturally significant
- Future extensions depend on understanding the new pattern

### Affected Audiences

1. **AI Assistants** - Will use outdated patterns when asked to extend shell integration
2. **New Contributors** - Will be confused when code doesn't match documentation
3. **Maintainers** - May duplicate effort by not understanding the unified pattern

### Risk of Not Updating

**Short Term**: Low - Code works, tests pass, users unaffected

**Long Term**: Medium
- Technical debt accumulates as docs drift from code
- Future developers waste time reconciling docs with code
- AI assistants generate incorrect implementations
- Knowledge transfer becomes harder

---

## Conclusion

The shell integration refactor is a well-designed architectural improvement that:
- Reduces code duplication
- Improves extensibility
- Maintains backward compatibility
- Follows project patterns (ABC interfaces, frozen dataclasses)

The documentation updates are straightforward and will ensure that the architecture documentation accurately reflects this improved design, making it easier for developers and AI assistants to understand and extend the system.

**Recommended Action**: Update both documentation files before merging to main, prioritizing MODULE_MAP.md for its comprehensive coverage of the new pattern.
```
