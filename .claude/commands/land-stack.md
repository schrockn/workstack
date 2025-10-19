---
description: Land a Graphite stack by squash-merging PRs from bottom to top
---

# Land Stack

Land a Graphite stack by sequentially squash-merging all PRs from the bottom of the stack to the top, using GitHub and Graphite CLI tools.

## What This Command Does

1. **Navigates to stack bottom**: Moves to the first branch in the stack (up from main)
2. **Iteratively merges PRs**: Squash-merges each PR, moves up, syncs, and restacks until reaching main
3. **Reports progress**: Tracks each merge operation and final status

## Usage

```bash
/land-stack
```

This command takes no arguments and operates on the current branch's stack.

## Graphite Command Execution

When executing gt commands in this workflow, use the `gt-runner` agent:

```
Task(
    subagent_type="gt-runner",
    description="[Short description]",
    prompt="Execute: gt [command]"
)
```

**When to use gt-runner:**

- Any gt command that produces output you need to parse
- Commands where you need structured results (PR URLs, branch lists, etc.)
- When output might pollute the context

**When to use Bash directly:**

- Simple gt commands with no output parsing needed
- Commands explicitly allowed in permissions

## Implementation Steps

When this command is invoked:

### 1. Navigate to Bottom of Stack

Navigate to the bottom of the stack (the first branch up from main).

Run this command repeatedly until you reach the bottom:

```bash
gt down
```

**How to know when you've reached the bottom:**

- Keep running `gt down` until the command outputs that you're at the bottom of the stack
- Graphite will indicate when you cannot go further down
- Alternatively, check with `gt log short` to see stack structure

### 2. Create Todo List for Tracking

Use TodoWrite to create a tracking structure:

```
1. Navigate to bottom of stack - in_progress initially, then completed
2. Merge PRs and move up stack - in_progress during the loop
3. Complete when on main - pending until done
```

Mark step 1 as completed once you're at the bottom of the stack.

### 3. Iterative Merge Loop

**This is the main loop that processes each PR in the stack.**

Mark "Merge PRs and move up stack" as in_progress.

For each branch in the stack (from bottom to top):

#### Step 3a: Merge the Current PR

Run:

```bash
gh pr merge -s
```

This squash-merges the current branch's PR to main and closes the PR.

**Expected outcome:**

- PR is merged to main
- PR is closed
- Local branch is updated

If this command fails:

- Report the specific error from `gh pr merge`
- Show which branch/PR failed
- STOP the landing process (do not continue to next PR)
- Ask user how to proceed

#### Step 3b: Move Up the Stack

Run:

```bash
gt up
```

This moves you to the next branch up in the stack.

**Expected outcome:**

- You're now on the next branch in the stack
- If you're now on main, the loop is complete

#### Step 3c: Sync with Remote

Run:

```bash
gt sync -f
```

This force-syncs the current branch with remote changes.

**Expected outcome:**

- Branch is synchronized with latest changes
- Any conflicts are handled (may require user intervention)

If `gt sync -f` fails:

- Report the sync error
- Show which branch failed to sync
- Ask user to resolve conflicts manually
- STOP the landing process

#### Step 3d: Check if Done

After syncing, check which branch you're on:

```bash
git branch --show-current
```

**If the output is "main":**

- You've completed landing the entire stack
- Mark "Merge PRs and move up stack" as completed
- Mark "Complete when on main" as completed
- STOP the loop
- Report success (see Expected Output Format below)

**If the output is NOT "main":**

- Continue to step 3e

#### Step 3e: Restack the Remaining Branches

Run:

```bash
gt restack
```

This rebases the remaining branches in the stack on top of the newly merged changes.

**Expected outcome:**

- Remaining branches are rebased
- Stack is clean and ready for next merge

If `gt restack` fails:

- Report the restack error
- Show which branch failed to restack
- Ask user to resolve conflicts manually
- STOP the landing process

#### Step 3f: Loop Back

Go back to step 3a (merge the current PR) and repeat.

**Safeguard:** Track the number of iterations. If you've done more than 20 iterations, STOP and report:

```
Error: Exceeded maximum iterations (20) while landing stack.

This likely indicates an issue with the stack structure or a bug in the landing process.

Please investigate the stack state manually.
```

## Important Notes

- **DO NOT run this command if there are uncommitted changes** - check `git status` first
- **Each PR must have an open PR on GitHub** - `gh pr merge` requires an existing PR
- **Force sync (`-f`) is required** because branches will be out of date after merges
- **Restack is necessary** after each merge to update remaining branches
- **The loop stops when you reach main** - this is the success condition
- **DO NOT batch todo completions** - mark each major step as completed immediately

## Error Handling

If any step fails:

1. **Report the specific command that failed**
2. **Show the full error message**
3. **Identify which branch you were on**
4. **STOP the landing process** (do not continue automatically)
5. **Ask the user how to proceed**

Example error report:

```
Error: Failed to merge PR for branch feature-branch-1

Command: gh pr merge -s

Error message:
Pull request is not mergeable: checks have not passed

Current branch: feature-branch-1

The landing process has been stopped. Please resolve the issue and try again.
```

## Expected Output Format

After successful completion:

```markdown
## Land Stack - Complete

**Status**: SUCCESS

**Stack landed successfully!**

All PRs have been squash-merged from bottom to top.

**Actions taken:**

1. Navigated to bottom of stack
2. Merged [N] PRs sequentially:
   - [branch-1] → merged to main
   - [branch-2] → merged to main
   - [branch-3] → merged to main
   - ...
3. Now on main branch

**Final state:**

- Current branch: main
- All PRs merged and closed
- Stack fully landed

You can now pull main to ensure you have all changes:
\`\`\`bash
git checkout main && git pull
\`\`\`
```

## Example Workflow

Here's what the full process looks like:

```bash
# Starting state: On a branch in a stack
Current branch: feature-3
Stack structure:
  main → feature-1 → feature-2 → feature-3 (you are here)

# 1. Navigate to bottom
$ gt down
$ gt down
Now on: feature-1

# 2. Start merge loop
$ gh pr merge -s  # Merge feature-1
$ gt up           # Move to feature-2
$ gt sync -f      # Sync with remote
$ gt restack      # Rebase feature-2 and feature-3

$ gh pr merge -s  # Merge feature-2
$ gt up           # Move to feature-3
$ gt sync -f      # Sync with remote
$ gt restack      # Rebase feature-3

$ gh pr merge -s  # Merge feature-3
$ gt up           # Move to main
$ gt sync -f      # Sync with remote
$ git branch --show-current
main

# Done! All PRs landed.
```
