---
description: Perform a local code review using repository standards and best practices
argument-hint: [base-branch]
---

# Local Code Review with Codex

Perform a comprehensive code review of changes using the `workstack-dev codex-review` command.

```bash
workstack-dev codex-review $PROMPT
```

This command:

- Automatically detects base branch (Graphite parent → main → HEAD~1)
- Analyzes code against repository standards (CLAUDE.md, .agent/ docs)
- Generates detailed markdown review with severity-categorized issues
- Saves to timestamped file: `code-review-<branch>-<timestamp>.md`

## Usage Examples

```bash
# Auto-detect base branch
/codex-review

# Specify base branch explicitly
/codex-review main
/codex-review feature/parent-branch

# Custom output location (via workstack-dev directly)
workstack-dev codex-review --output my-review.md
```

## Review Structure

The generated review includes:

- **Summary**: Overview of changes and overall assessment
- **Statistics**: Files changed, lines added/removed
- **Issues by Severity**: Categorized findings (🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low, ℹ️ Informational)
- **Positive Observations**: Good practices in the code
- **Detailed Findings**: Location, issue, impact, recommendations, examples
- **Recommendations Summary**: Prioritized action items

## Implementation

The command is implemented in `packages/workstack-dev/src/workstack_dev/commands/codex_review/`:

- `command.py`: Click CLI interface
- `script.py`: Core review logic with branch detection
- `prompt.txt`: Codex prompt template
