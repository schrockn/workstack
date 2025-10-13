# GitHub CLI (`gh`) Mental Model

**Last Updated**: 2025-10-13

A comprehensive guide to understanding GitHub CLI's mental model, command structure, and integration patterns.

---

## Table of Contents

- [What is GitHub CLI?](#what-is-github-cli)
- [Core Mental Model](#core-mental-model)
- [Terminology](#terminology)
- [Authentication & Configuration](#authentication--configuration)
- [Command Reference](#command-reference)
- [Workflow Patterns](#workflow-patterns)
- [Workstack Integration](#workstack-integration)
- [Practical Examples](#practical-examples)

---

## What is GitHub CLI?

GitHub CLI (`gh`) is the official command-line tool for GitHub. It brings pull requests, issues, releases, and other GitHub concepts to the terminal.

### The Problem It Solves

Without `gh`, working with GitHub requires:

1. Switching to browser for PR operations
2. Manual URL construction
3. Context switching between terminal and web
4. No scriptable GitHub workflows

With `gh`, you can:

- Create, view, and merge PRs from terminal
- Manage issues without leaving your editor
- Script GitHub workflows
- Query GitHub API with built-in authentication

### Core Philosophy

**GitHub in your terminal.** `gh` mirrors GitHub's web interface structure but optimized for CLI workflows and automation.

---

## Core Mental Model

**[TODO: To be expanded with detailed mental model sections]**

---

## Terminology

**[TODO: To be expanded with terminology definitions]**

---

## Authentication & Configuration

**[TODO: To be expanded with auth/config details]**

---

## Command Reference

**[TODO: To be expanded with comprehensive command reference]**

---

## Workflow Patterns

**[TODO: To be expanded with workflow examples]**

---

## Workstack Integration

### How Workstack Uses `gh`

Workstack integrates with GitHub CLI to enhance the worktree workflow:

#### 1. PR Information Retrieval

**File**: `src/workstack/github_ops.py`

```python
def get_prs(self, repo_root: Path) -> dict[str, PullRequestInfo] | None:
    """Fetch all PRs for repository using gh pr list."""
```

**What it does**:

- Runs `gh pr list --state all --json number,headRefName,url,state,isDraft,statusCheckRollup`
- Parses JSON output
- Returns dict mapping branch name → PR info

**Used by**:

- `workstack list`: Shows PR status next to worktrees
- `workstack gc`: Identifies merged PRs for cleanup

**[TODO: To be expanded with more integration details]**

---

## Practical Examples

**[TODO: To be expanded with practical examples]**

---

## Key Insights for AI Agents

**[TODO: To be expanded with AI agent-specific insights]**

---

## Additional Resources

- **Official Docs**: https://cli.github.com/manual/
- **gh API**: https://docs.github.com/en/rest

---

**Note**: This is a work-in-progress document that will be expanded to match the comprehensive style of `gt.md`.
