---
description: Save implementation plan from context, create worktree, and execute
---

# /workstack:execute_plan

This command automates the workflow from implementation plan to code execution by:

1. **Detecting** an implementation plan in the recent conversation context
2. **Persisting** the plan to a markdown file at the current worktree root
3. **Creating** a workstack worktree with the plan
4. **Switching** to that worktree directory
5. **Executing** the plan automatically

## Usage

```bash
/workstack:execute_plan
```

## Prerequisites

- An implementation plan must exist in recent conversation context
- Current working directory must be in the workstack repository
- The plan should not already be saved to disk

## What Happens

When you run this command:

1. The assistant searches recent conversation for an implementation plan
2. Extracts and saves the plan as `<feature-name>-plan.md` at current worktree root
3. Creates a new workstack worktree with: `workstack create --plan <filename>-plan.md`
4. Changes to the new worktree directory
5. Automatically starts implementation execution

## Expected Outcome

- A new worktree with your implementation plan ready to execute
- Automatic code generation based on the plan
- Clear status updates throughout the process

---

## Agent Instructions

You are executing the `/workstack:execute_plan` command. Follow these steps carefully:

### Step 1: Detect Implementation Plan in Context

Search the recent conversation for an implementation plan. Look for:

- Markdown content with sections like "Implementation Plan:", "Overview", "Implementation Steps"
- Structured task lists or step-by-step instructions
- Headers containing words like "Plan", "Tasks", "Steps", "Implementation"

If no plan is found:

```
❌ Error: No implementation plan found in recent conversation

Please ensure an implementation plan has been presented recently in the conversation.
```

### Step 2: Extract and Process Plan Content

When a plan is found:

1. Extract the full markdown content of the plan
2. Preserve all formatting, headers, and structure
3. Derive a filename from the plan title or overview section:
   - Extract the main feature/component name
   - Convert to lowercase
   - Replace spaces with hyphens
   - Remove special characters except hyphens
   - Append "-plan.md"
   - Example: "User Authentication System" → `user-authentication-plan.md`

### Step 2.5: Detect Worktree Root

Execute: `git rev-parse --show-toplevel`

This returns the absolute path to the root of the current worktree. Store this as `<worktree-root>` for use in subsequent steps.

If the command fails:

```
❌ Error: Could not detect worktree root

Details: Not in a git repository or git command failed
Suggested action: Ensure you are in a valid git worktree
```

### Step 3: Save Plan to Disk

Use the Write tool to save the plan:

- Path: `<worktree-root>/<derived-filename>`
- Content: Full plan markdown content
- Verify file creation

If save fails, provide error:

```
❌ Error: Failed to save plan file

Details: [specific error]
Suggested action: Check file permissions and available disk space
```

### Step 4: Create Worktree with Plan

Execute: `workstack create --plan <worktree-root>/<filename>`

Use the absolute path from Step 2.5 to ensure workstack can find the plan file regardless of current working directory.

Parse the output to extract:

- Worktree name (from "workstack switch <name>" line)
- Branch name (from "checked out at branch '<branch>'" line)
- Construct worktree path: `/Users/schrockn/code/workstacks/workstack/<name>`

Handle specific errors:

- **Worktree exists**:

  ```
  ❌ Error: Worktree with this name already exists

  Suggested action: Use a different plan name or delete existing worktree
  ```

- **Invalid plan**:

  ```
  ❌ Error: Plan file format is invalid

  Details: [workstack error message]
  ```

### Step 5: Change to Worktree Directory

Execute: `cd <worktree-path>`

Then verify `.PLAN.md` exists in the new directory:

```bash
test -f .PLAN.md && echo "Plan file verified" || echo "Plan file missing"
```

If verification fails:

```
❌ Error: Plan file not found in worktree

Details: Expected .PLAN.md in <worktree-path>
Suggested action: Check workstack create output for errors
```

### Step 6: Execute the Implementation Plan

Begin execution of the implementation plan that was copied into the worktree:

- Read the `.PLAN.md` file from the current directory
- Start implementing the plan according to its instructions
- Provide progress updates as implementation proceeds

### Step 7: Report Success

After successful execution, provide summary:

```markdown
## ✅ Worktree Created and Plan Execution Started

**Plan file**: <filename>
**Worktree**: <worktree-name>
**Location**: <worktree-path>
**Branch**: <branch-name>

The implementation plan is now being executed in the new worktree.

### Next Steps

- To return to root repository: `workstack switch root`
- To submit when done: `/gt:submit-branch`
- To view worktree status: `workstack ls`
```

## Error Handling Summary

All errors should follow this format:

```
❌ Error: [Brief description]

Details: [Specific error message or context]

Suggested action: [What the user should do to resolve]
```

Common error scenarios to handle:

- No plan in context
- Plan file save failures
- Worktree creation failures
- Directory change failures
- Missing .PLAN.md after worktree creation
- SlashCommand invocation failures

## Important Notes

- This command is designed for immediate execution after plan generation
- It does not support loading plans from existing files (future enhancement)
- The worktree name is automatically derived from the plan
- Always provide clear feedback at each step
