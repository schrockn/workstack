---
name: gh
description: This skill should be used when working with GitHub CLI (gh) for pull requests, issues, releases, and GitHub automation. Use when users mention gh commands, GitHub workflows, PR operations, issue management, or GitHub API access. Essential for understanding gh's mental model, command structure, and integration with git workflows.
---

# GitHub CLI (gh)

## Overview

GitHub CLI (`gh`) is the official command-line tool for GitHub that brings pull requests, issues, releases, and other GitHub concepts to the terminal. This skill provides comprehensive guidance for using `gh` to streamline GitHub workflows, including PR management, issue tracking, repository operations, and API access.

## When to Use This Skill

Invoke this skill when users:

- Mention GitHub CLI (`gh`) commands or workflows
- Ask about creating, viewing, or managing pull requests from the command line
- Need help with GitHub issue management via CLI
- Want to understand gh's mental model or command structure
- Request guidance on GitHub automation or scripting
- Ask about GitHub API access through gh
- Need help with gh authentication or configuration
- Request integration patterns between gh, git, and other tools (like workstack)

## Core Concepts

Before providing guidance, understand these key concepts:

**Three-Layer Architecture:**

1. **High-Level Commands** (porcelain): `gh pr`, `gh issue`, `gh repo` - user-friendly workflows
2. **API Access**: `gh api` - direct REST/GraphQL access with built-in auth
3. **Git Integration**: Smart repo detection from git remotes and current branch

**Context Resolution:**

- `gh` automatically detects repository from git remotes
- Uses current branch to infer PR context
- Falls back to interactive selection when ambiguous

**Mental Model:**
Think of `gh` as "GitHub workflows made CLI-native" - each command maps to a common GitHub workflow optimized for terminal use.

## Using the Reference Documentation

When providing gh guidance, load the comprehensive reference documentation:

```
references/gh.md
```

This reference contains:

- Complete mental model and terminology
- Full command reference for PRs, issues, repos, releases, and more
- Authentication and configuration patterns
- Workflow patterns for common scenarios
- Integration details (workstack, git, CI/CD)
- GitHub API access patterns
- Practical examples for daily development

**Loading Strategy:**

- Always load `references/gh.md` when user asks gh-related questions
- The reference is comprehensive (~1480 lines) but optimized for progressive reading
- Use grep patterns to find specific sections when needed:
  - `gh pr` - Pull request commands
  - `gh issue` - Issue management commands
  - `gh repo` - Repository operations
  - `gh api` - API access patterns
  - `Pattern [0-9]:` - Workflow patterns
  - `Authentication` - Auth setup
  - `workstack Integration` - Integration with workstack

## Common Operations

When users ask for help with gh, guide them using these patterns:

### First-Time Setup

1. Check if gh is installed: `gh --version`
2. Authenticate: `gh auth login` (interactive) or `gh auth status` (check current)
3. Configure defaults: `gh config set <key> <value>`
4. Test connection: `gh repo view` (in a git repo)

### Pull Request Operations

Load `references/gh.md` and search for "gh pr" section to provide:

- Creating PRs: `gh pr create` (interactive or with flags)
- Viewing PRs: `gh pr view`, `gh pr list`
- Checking out PRs: `gh pr checkout <number>`
- Reviewing PRs: `gh pr review`, `gh pr diff`
- Merging PRs: `gh pr merge`
- PR status checks: `gh pr checks`

### Issue Management

Load `references/gh.md` and search for "gh issue" section to provide:

- Creating issues: `gh issue create`
- Listing issues: `gh issue list` (with filters)
- Viewing issues: `gh issue view <number>`
- Updating issues: `gh issue edit`, `gh issue close`
- Issue assignment and labels

### Repository Operations

Load `references/gh.md` and search for "gh repo" section to provide:

- Viewing repos: `gh repo view`
- Cloning repos: `gh repo clone`
- Creating repos: `gh repo create`
- Forking repos: `gh repo fork`
- Repository settings and visibility

### API Access

Load `references/gh.md` and search for "gh api" section to provide:

- REST API calls: `gh api <endpoint>`
- GraphQL queries: `gh api graphql -f query='...'`
- Pagination handling
- JSON processing with `--jq`
- Authentication details

### Release Management

Load `references/gh.md` and search for "gh release" section to provide:

- Creating releases: `gh release create`
- Listing releases: `gh release list`
- Downloading assets: `gh release download`
- Uploading assets: `gh release upload`

## Workflow Guidance

When users describe their workflow needs, map them to patterns in the reference:

**Pattern 1: Daily PR Workflow** - Create, review, merge PRs
**Pattern 2: Issue Triage** - List, filter, and manage issues
**Pattern 3: Release Automation** - Script release creation and asset management
**Pattern 4: PR Checks and Status** - Monitor CI/CD and review status
**Pattern 5: Multi-Repo Operations** - Work across multiple repositories
**Pattern 6: GitHub API Scripting** - Automate complex GitHub workflows
**Pattern 7: Code Review Workflow** - Review PRs from command line

Load the appropriate pattern sections from `references/gh.md` based on user needs.

## Output Formatting

When users need to parse or format gh output:

1. Load the Output Formatting section from `references/gh.md`
2. Explain format options: `--json`, `--jq`, `--template`
3. Show JSON field selection: `gh pr list --json number,title,state`
4. Demonstrate jq filtering: `gh api /repos/{owner}/{repo}/pulls | jq '.[] | select(.draft==false)'`
5. Provide template examples for custom output

## Authentication and Configuration

When users need auth or config help:

1. Load the Authentication & Configuration section from `references/gh.md`
2. Distinguish between:
   - Authentication: `gh auth login`, token management
   - Configuration: `gh config set`, per-command defaults
3. Explain authentication methods: browser, token, SSH
4. Show common config settings: `git_protocol`, `editor`, `pager`
5. Handle multiple accounts and enterprise instances

## Integration Guidance

### Workstack Integration

When users mention workstack or worktree workflows:

- Load the Workstack Integration section from `references/gh.md`
- Explain how gh detects repos in worktrees
- Show PR operations across multiple worktrees
- Guide on using `--repo` flag when needed
- Reference workstack documentation for worktree-specific patterns

### Git Integration

When users need to understand gh + git workflows:

- Load the Git Integration section from `references/gh.md`
- Explain repo detection from git remotes
- Show how current branch affects PR commands
- Demonstrate combined git + gh workflows
- Clarify when to use git vs gh commands

### CI/CD Integration

When users want to integrate gh with CI/CD:

- Load the CI/CD patterns from `references/gh.md`
- Show authentication in CI environments: `GH_TOKEN`
- Provide examples of automated PR creation/merging
- Demonstrate status check monitoring
- Guide on release automation

## Scripting and Automation

When users want to script GitHub workflows:

1. Load the Scripting section from `references/gh.md`
2. Show how to use `gh` in shell scripts
3. Demonstrate error handling: `--jq`, exit codes
4. Explain pagination for large datasets
5. Provide examples of common automation patterns:
   - Bulk operations across PRs/issues
   - Custom notifications
   - Release workflows
   - Repository management

## Advanced Features

When users need advanced capabilities:

1. **Aliases**: Custom commands via `gh alias set`
2. **Extensions**: Third-party gh extensions
3. **GraphQL**: Complex queries beyond REST API
4. **Webhooks**: Trigger workflows (via API)
5. **GitHub Actions**: Interact with workflows via `gh workflow`

Load the relevant sections from `references/gh.md` for each advanced feature.

## Troubleshooting

When users encounter issues:

1. Check authentication: `gh auth status`
2. Verify repository detection: `gh repo view`
3. Test API access: `gh api user`
4. Review configuration: `gh config list`
5. Check rate limits: `gh api rate_limit`
6. Enable debug mode: `GH_DEBUG=api gh <command>`

Load the Troubleshooting section from `references/gh.md` for specific error patterns.

## Command Discovery

When users ask "what can gh do?":

- Start with overview of main commands: `pr`, `issue`, `repo`, `release`, `workflow`
- Show command help: `gh <command> --help`
- Demonstrate interactive mode: most commands work interactively
- Point to `gh api` for anything not covered by porcelain commands
- Reference the full command reference in `references/gh.md`

## Resources

### references/

- `gh.md` - Comprehensive GitHub CLI mental model and command reference (~1480 lines)

This reference should be loaded whenever providing gh guidance to ensure accurate, detailed information.
