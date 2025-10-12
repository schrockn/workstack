---
description: Perform a local code review using repository standards and best practices
argument-hint: [base-branch]
---

# Local Code Review with Codex

Perform a comprehensive code review of changes between the current branch and a base branch.

## Determine Base Branch

First, determine what to compare against:

```bash
# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# Determine base branch for comparison
if [ -z "$PROMPT" ] || [ "$PROMPT" = "" ]; then
    # No argument provided - auto-detect base
    if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
        # On trunk - compare with previous commit
        BASE_BRANCH="HEAD~1"
        echo "On trunk branch - comparing with HEAD~1"
    else
        # Try to get parent from Graphite
        PARENT=$(gt parent 2>/dev/null || echo "")
        if [ -n "$PARENT" ]; then
            BASE_BRANCH="$PARENT"
            echo "Using Graphite parent branch: $BASE_BRANCH"
        else
            # Fallback to main
            BASE_BRANCH="main"
            echo "Using default base: main"
        fi
    fi
else
    # Use provided argument as base
    BASE_BRANCH="$PROMPT"
    echo "Using specified base: $BASE_BRANCH"
fi

# Generate timestamp and output filename
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
OUTPUT_FILE="code-review-${CURRENT_BRANCH}-${TIMESTAMP}.md"
```

## Execute Code Review

Run the following command using Codex to perform the review:

```bash
codex exec "
# Context Loading Phase

First, read and understand the repository's coding standards and conventions:

1. Read CLAUDE.md in the root directory - this contains the core coding standards
2. Read all .md files in the .agent/ directory - these contain additional patterns, guidelines, and conventions
3. Pay special attention to:
   - Exception handling patterns
   - Type annotation requirements
   - Import conventions
   - Testing patterns
   - CLI development guidelines

# Review Generation Phase

Now perform a comprehensive code review:

1. Get the git diff between $BASE_BRANCH and $CURRENT_BRANCH:
   \`\`\`
   git diff $BASE_BRANCH...$CURRENT_BRANCH
   \`\`\`

2. Analyze each changed file against:
   - The repository-specific standards you just read
   - General software engineering best practices
   - Code quality, readability, and maintainability
   - Security considerations
   - Performance implications
   - Test coverage

3. Generate a detailed review in markdown format with the following structure:

   # Code Review: $CURRENT_BRANCH

   **Date**: $(date)
   **Base Branch**: $BASE_BRANCH
   **Current Branch**: $CURRENT_BRANCH

   ## Summary
   Brief overview of the changes and overall assessment

   ## Statistics
   - Files changed: X
   - Lines added: Y
   - Lines removed: Z

   ## Issues by Severity

   ### 🔴 Critical Issues
   Issues that must be fixed before merging (bugs, security issues, broken standards)

   ### 🟠 High Priority
   Important issues that should be addressed (performance, major style violations)

   ### 🟡 Medium Priority
   Issues that would improve code quality (minor violations, suggestions)

   ### 🟢 Low Priority
   Nice-to-have improvements (formatting, documentation)

   ### ℹ️ Informational
   Notes and observations (not issues)

   ## Positive Observations
   Good practices observed in the code

   ## Detailed Findings

   For each issue, provide:
   - **Location**: file:line
   - **Issue**: What's wrong
   - **Why it matters**: Impact/consequences
   - **Recommendation**: How to fix it
   - **Example**: Code snippet if helpful

   ## Recommendations Summary
   Prioritized list of actions to take

4. Save the review to $OUTPUT_FILE

5. Display a summary message:
   'Review complete! Full report saved to $OUTPUT_FILE'

   Then show just the Summary and Issues by Severity sections for quick reference.

Remember to:
- Apply BOTH repository-specific standards AND general best practices
- Be constructive and specific in feedback
- Acknowledge good practices, not just problems
- Provide actionable recommendations
- Consider that the code may have been written by any developer or AI model
"
```

## Notes

- The review combines repository-specific standards with general code review best practices
- Automatically detects the appropriate base branch using Graphite or git
- Saves detailed review to a timestamped file with branch name
- Shows a quick summary in the terminal while saving full details to file