# Code Review: the-whole-shebang

**Date**: Mon Oct 13 07:28:35 2025
**Base Branch**: main
**Current Branch**: the-whole-shebang

## Summary

- Major feature drop introducing safe rebase stacks, CLI commands, and supporting abstractions.
- Configuration surface widened with several new `rebase.*` options and the gitops layer gained rebase-aware APIs.
- Extensive automated coverage accompanies the change, but two blocking workflow regressions remain.

## Statistics

- Files changed: 22
- Lines added: 4833
- Lines removed: 11

## Issues by Severity

### 🔴 Critical Issues

- Creating a stack for the currently checked-out branch errors because `git worktree add` forbids double checkouts (`src/workstack/core/rebase_stack_ops.py:102`).
- Applying a finished stack fails while on that branch because `git branch -f` refuses to update the current HEAD (`src/workstack/cli/commands/rebase.py:353`).

### 🟠 High Priority

- None.

### 🟡 Medium Priority

- The new `rebase.stackLocation` config is ignored; stack paths remain hard-coded so user settings have no effect (`src/workstack/core/rebase_stack_ops.py:124`).

### 🟢 Low Priority

- None.

### ℹ️ Informational

- The `RebaseError` hierarchy is defined but not yet wired into CLI flows; consider integrating in a follow-up (`src/workstack/core/rebase_errors.py:6`).

## Positive Observations

- tests/cli/commands/test_rebase.py:1 — Strong CLI coverage covering preview/resolve/test/apply flows with fakes.
- src/workstack/core/rebaseops.py:1 — Clean separation of rebase-specific git operations behind an ABC with a real implementation and fakes.

## Detailed Findings

1. **Location**: src/workstack/core/rebase_stack_ops.py:102
   - **Issue**: `create_stack` calls `git worktree add <stack_path> <branch>`, but git rejects adding a worktree for a branch that is already checked out (which is the common case when the user is on that branch in the root repo).
   - **Why it matters**: `workstack rebase preview` breaks immediately with `fatal: '<branch>' is already checked out at ...`, so the core “safe stack” workflow never starts.
   - **Recommendation**: Create the stack from the branch tip commit instead of the branch ref (e.g., resolve the sha with `git rev-parse` and add the worktree in detached mode) or create a temporary stack branch name; add a regression test where the branch is checked out in the primary worktree.
   - **Example**:
     ```text
     git worktree add /tmp/.rebase-stack-feature feature
     fatal: 'feature' is already checked out at '/path/to/repo'
     ```

2. **Location**: src/workstack/cli/commands/rebase.py:353
   - **Issue**: `apply_cmd` runs `git branch -f <branch> <stack_commit>` while that branch remains checked out in the root worktree.
   - **Why it matters**: git disallows force-updating the current HEAD, so `workstack rebase apply` errors out after the stack is cleaned up, leaving the user without an updated branch and no stack to retry.
   - **Recommendation**: Update the branch before cleaning up (e.g., `git reset --hard <stack_commit>` in the root worktree or update the ref from the stack worktree and then sync), ensuring uncommitted changes are handled safely.
   - **Example**:
     ```text
     git branch -f feature 1234abcd
     error: Cannot force update the current branch.
     ```

3. **Location**: src/workstack/core/rebase_stack_ops.py:124
   - **Issue**: Stack paths ignore the newly exposed `rebase.stackLocation` configuration; `_get_stack_path` is hard-coded to `.rebase-stack-<branch>`.
   - **Why it matters**: Users can set `config set rebase.stackLocation …` but the value is never respected, undermining the new configuration keys and documentation.
   - **Recommendation**: Thread the configured prefix/location into `RebaseStackOps` (e.g., pass it via `WorkstackContext` or read from `global_config_ops`) and add coverage for non-default paths.
   - **Example**: `workstack config set rebase.stackLocation rebase-worktrees` still produces `.rebase-stack-feature` directories.

## Recommendations Summary

1. Allow stack creation when the branch is already checked out by detaching or using a temporary stack branch.
2. Fix `rebase apply` to update the active branch safely (e.g., via `git reset --hard` on the root worktree) before removing the stack.
3. Honor the new `rebase.stackLocation` config inside `RebaseStackOps`.
