---
description: Create git commit and submit current branch with Graphite
argument-hint: <description>
---

# Submit Branch

Automatically create a git commit with a helpful summary message and submit the current branch as a pull request.

## What This Command Does

1. **Commit outstanding changes**: Stage and commit any uncommitted changes with a temporary message
2. **Squash commits**: Run `gt squash` to combine all commits in the current branch
3. **Analyze and update message**: Use git-diff-summarizer agent to analyze all changes and create a comprehensive commit message
4. **Submit branch**: Run `gt submit --publish --no-edit` to create/update PR for the current branch
5. **Report results**: Show the submitted PRs and their URLs

## Usage

```bash
# With description argument
/submit-branch "Add user authentication feature"

# Without argument (will analyze changes automatically)
/submit-branch
```

## Graphite Command Execution

**ALWAYS use the `gt-runner` agent for ALL gt commands in this workflow:**

```
Task(
    subagent_type="gt-runner",
    description="[Short description]",
    prompt="Execute: gt [command]"
)
```

This ensures:

- Consistent execution and error handling
- Proper output parsing without polluting context
- Cost-optimized execution with Haiku model

## Implementation Steps

When this command is invoked:

### 1. Commit Outstanding Changes

Check for uncommitted changes and commit them:

```bash
git status
```

If there are uncommitted changes:

```bash
git add .
git commit -m "WIP: Prepare for submission"
```

### 2. Squash All Commits

Combine all commits in the current branch into a single commit using gt-runner:

```
Task(subagent_type="gt-runner", description="Squash commits", prompt="Execute: gt squash")
```

This creates a single commit containing all changes from the branch.

### 3. Analyze Changes and Update Commit Message

Use the git-diff-summarizer agent to analyze all changes and create a comprehensive commit message:

- Invoke the agent: `Task(subagent_type="git-diff-summarizer", prompt="Analyze all changes in this branch (compared to parent branch) and provide a comprehensive summary for the commit message")`
- The agent will analyze the full diff and provide a detailed summary
- Use the agent's summary to amend the squashed commit with `git commit --amend`
- Ensure the commit message follows the repository's commit style
- **DO NOT include any Claude Code footer or co-authorship attribution**

### 4. Submit Branch

Submit the current branch as a PR without interactive prompts using gt-runner:

```
Task(subagent_type="gt-runner", description="Submit branch", prompt="Execute: gt submit --publish --no-edit --restack")
```

Flags explained:

- `--publish`: Publish any draft PRs
- `--no-edit`: Use commit messages as PR titles/descriptions without prompting
- `--restack`: Restack branches before submitting. If there are conflicts, output the branch names that could not be restacked

### 5. Show Results

After submission, show:

- Whether PR was created or updated
- PR URL (from gt-runner output)
- Current branch name

## Important Notes

- **ALWAYS use git-diff-summarizer agent** for analyzing changes and creating commit messages
- **Commit early**: Stage and commit all changes before squashing
- **Squash before analyzing**: Run `gt squash` before using git-diff-summarizer so it analyzes the complete branch changes
- **Follow repo patterns**: Check recent commits with `git log` to match style
- **NO Claude footer**: Do not add any attribution or generated-by footer to the final commit message
- If there are no changes to commit at the start, report to the user and exit

## Error Handling

If any step fails:

- Report the specific command that failed
- Show the error message
- Ask the user how to proceed (don't retry automatically)

## Example Output

```
Checking for uncommitted changes...
✓ Found changes in 3 files
✓ Committed as "WIP: Prepare for submission"

Squashing commits...
✓ 3 commits squashed into 1

Analyzing changes with git-diff-summarizer...
✓ Branch contains changes to tree formatting in gt branches command
✓ Updating commit message with comprehensive summary

Submitting branch...
✓ PR created: #123
✓ https://github.com/owner/repo/pull/123
✓ Branch: gt-tree-format
```
