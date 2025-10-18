---
description: Create git commit and submit stack with Graphite
argument-hint: <description>
---

# Submit Stack

Automatically create a git commit with a helpful summary message and submit the entire Graphite stack as pull requests.

## What This Command Does

1. **Analyze changes**: First checks for .PLAN.md file to understand context, otherwise reviews git status and diff
2. **Create commit**: Generates a concise single-sentence commit message summarizing the changes
3. **Restack**: Runs `gt restack` to ensure all branches in the stack are properly rebased
4. **Submit stack**: Runs `gt submit --stack --publish --no-edit` to create/update PRs for the entire stack
5. **Report results**: Shows the submitted PRs and their URLs

## Usage

```bash
# With description argument
/submit-stack "Add user authentication feature"

# Without argument (will analyze changes automatically)
/submit-stack
```

## Implementation Steps

When this command is invoked:

### 1. Analyze Current Changes

**FIRST**: Check if `.PLAN.md` exists in the repository root:

```bash
if [ -f .PLAN.md ]; then
  # Use .PLAN.md for context
else
  # Fall back to git analysis
fi
```

If `.PLAN.md` exists:

- Read the plan file to understand what was implemented
- Use the plan's summary and goals to create the commit message

If no `.PLAN.md`:

- Run `git status` and `git diff HEAD` to see changes
- Review the changes to create an accurate summary

### 2. Create Git Commit

Based on the analysis:

- If user provided an argument, use it as the basis for the commit message
- If `.PLAN.md` exists, summarize what was implemented from the plan
- Otherwise, analyze the git changes and create a descriptive single-sentence summary
- Ensure the commit message follows the repository's commit style (check `git log` for patterns)
- **DO NOT include any Claude Code footer or co-authorship attribution**

```bash
git add .
git commit -m "[Single sentence summary of what was done]"
```

### 3. Restack the Stack

Ensure all branches in the stack are properly rebased:

```bash
gt restack
```

### 4. Submit Stack

Submit all PRs in the stack without interactive prompts:

```bash
gt submit --stack --publish --no-edit --restack
```

Flags explained:

- `--stack`: Submit entire stack (upstack + downstack)
- `--publish`: Publish any draft PRs
- `--no-edit`: Use commit messages as PR titles/descriptions without prompting
- `--restack`: Restack branches before submitting (if needed)

### 5. Show Results

After submission, show:

- Number of PRs created/updated
- PR URLs (extract from `gt` output)
- Current stack status with `gt log short`

## Important Notes

- **Check for .PLAN.md FIRST** before analyzing git changes
- **NEVER run additional exploration commands** beyond checking .PLAN.md, git status/diff/log
- **Stage all changes** with `git add .` before committing
- **Single sentence summary**: Keep commit message concise and focused
- **Follow repo patterns**: Check recent commits with `git log` to match style
- **NO Claude footer**: Do not add any attribution or generated-by footer
- If there are no staged or unstaged changes, report to the user and exit

## Error Handling

If any step fails:

- Report the specific command that failed
- Show the error message
- Ask the user how to proceed (don't retry automatically)

## Example Output

```
Analyzing changes...
✓ Found .PLAN.md - using plan context
✓ Found changes in 3 files

Creating commit: "Add dot-agent submit-stack command for automated PR workflow"
✓ Commit created

Restacking branches...
✓ Stack restacked successfully

Submitting stack...
✓ 2 PRs created/updated:
  - PR #123: dot-agent-claude-folder-support (new)
  - PR #122: base-branch (updated)

Current stack:
◯ dot-agent-claude-folder-support (current)
◯ base-branch
◉ main
```
