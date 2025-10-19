---
description: Merge a single PR from a Graphite stack without affecting upstack branches
---

# Land Branch

Merge a single PR from a Graphite stack without affecting upstack branches.

## What This Command Does

This command safely lands a single branch from a Graphite stack by:

1. **Validates branch position**: Ensures the branch is exactly one level up from main
2. **Checks PR status**: Verifies an open pull request exists
3. **Validates linear stack**: Ensures the branch has 0 or 1 children (linear stack only)
4. **Merges the PR**: Squash-merges the PR to main using `gh pr merge -s`
5. **Navigates to child**: If a child branch exists, automatically navigates to it

## Usage

```bash
/land-branch
```

This command takes no arguments and operates on the current branch.

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

### Step 1: Get Current Branch and Metadata

First, get the current branch name:

```bash
git branch --show-current
```

**Store the branch name for use in status messages.**

Next, get branch metadata:

```bash
workstack graphite branches --format json
```

**Parse the JSON output to extract:**

- Current branch's parent name (from `"parent"` field)
- Current branch's children array (from `"children"` field)

**Example JSON structure:**

```json
{
  "branches": [
    {
      "name": "feature-branch",
      "parent": "main",
      "children": ["next-feature"],
      "is_trunk": false,
      "commit_sha": "abc123"
    }
  ]
}
```

### Step 2: Validate Parent is Main

**Check that the parent branch is exactly "main".**

If `parent !== "main"`, report error and exit:

```
Error: Branch must be exactly one level up from main

Current branch: {branch_name}
Parent branch: {parent} (expected: main)

Please navigate to a branch that branches directly from main.
```

### Step 3: Check PR Exists and is Open

Run:

```bash
gh pr view --json state,number
```

**Parse JSON to check:**

- Command succeeds (PR exists)
- `state` field is `"OPEN"`

**If no PR exists (command fails):**

```
Error: No pull request found for this branch

Please create a PR first using: gt submit
```

**If PR is not open:**

```
Error: Pull request is not open (state: {state})

This command only works with open pull requests.
```

### Step 4: Validate Linear Stack

**Check the children array from Step 1.**

**Valid cases:**

- `children = []` (last branch in stack)
- `children = ["single-branch"]` (exactly one child)

**If `len(children) > 1`, report error and exit:**

```
Error: Branch has multiple children (not a linear stack)

Children: {child1}, {child2}, {child3}

This command only works with linear stacks. Please use a branch with 0 or 1 children.
```

### Step 5: Merge the PR

Run:

```bash
gh pr merge -s
```

This squash-merges the PR to main and closes it.

**If the command fails, report error and exit:**

```
Error: Failed to merge PR

{output from gh pr merge}

Please resolve the issue and try again.
```

### Step 6: Navigate to Child Branch (if exists)

**If `children = []` (no children):**

```
✓ Successfully merged PR #{pr_number} for branch {branch_name}
✓ Stack complete! No more branches to land.
```

**If `children = ["single-branch"]` (one child):**

Run:

```bash
workstack jump {child_branch_name}
```

Then output:

```
✓ Successfully merged PR #{pr_number} for branch {branch_name}
✓ Navigated to child branch: {child_branch_name}

You can now run /land-branch again to merge the next PR in the stack.
```

## TodoWrite Structure

When executing this command, create these todos:

1. "Get current branch name and metadata" / "Getting current branch name and metadata"
2. "Validate parent is main" / "Validating parent is main"
3. "Check PR exists and is open" / "Checking PR exists and is open"
4. "Validate linear stack (0-1 children)" / "Validating linear stack"
5. "Merge PR with gh pr merge -s" / "Merging PR with gh pr merge -s"
6. "Navigate to child branch if exists" / "Navigating to child branch"
7. "Report final status" / "Reporting final status"

Start with todo 1 as `in_progress`, rest as `pending`. Mark each as `completed` immediately after finishing.

## Important Notes

- **This command only works with linear stacks** (0 or 1 children per branch)
- **Branch must be exactly one level up from main** (parent must be "main")
- **PR must be open** before running this command
- **No explicit rebase** - `gh pr merge` will validate mergeability
- **Use `workstack jump`** for navigation (not `gt checkout`) to maintain consistency

## Error Handling

All errors should:

1. Use clear, actionable error messages
2. Exit immediately (do not continue execution)
3. Provide context about what went wrong and how to fix it

Error message template:

```
Error: [What went wrong]

[Current state details]

[Suggested action to fix]
```
