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

## Implementation Steps

When this command is invoked:

### Step 1: Execute land-branch command

Run the workstack-dev command with JSON output:

```bash
workstack-dev land-branch --format json
```

This command encapsulates all the validation and execution logic in Python, returning a structured JSON result.

### Step 2: Parse and display result

Parse the JSON output to determine success or failure:

**On success (`success: true`):**

Display the success message to the user. The JSON will include:

```json
{
  "success": true,
  "pr_number": 123,
  "branch_name": "feature-branch",
  "child_branch": "next-feature",
  "message": "Successfully merged PR #123 for branch feature-branch"
}
```

If `child_branch` is not null, inform the user they can run `/land-branch` again.

**On failure (`success: false`):**

Display the error message from the JSON response and exit with error status. The JSON will include:

```json
{
  "success": false,
  "error_type": "parent_not_main",
  "message": "Detailed error message...",
  "details": {
    "current_branch": "feature-branch",
    "parent_branch": "other-feature"
  }
}
```

## TodoWrite Structure

When executing this command, create these todos:

1. "Execute workstack-dev land-branch" / "Executing workstack-dev land-branch"
2. "Parse result and display to user" / "Parsing result and displaying to user"

Start with todo 1 as `in_progress`, rest as `pending`. Mark each as `completed` immediately after finishing.

## Important Notes

- **This command only works with linear stacks** (0 or 1 children per branch)
- **Branch must be exactly one level up from main** (parent must be "main")
- **PR must be open** before running this command
- **No explicit rebase** - `gh pr merge` will validate mergeability
- **Use `workstack up`** for navigation to automatically move to the child branch in the stack

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
