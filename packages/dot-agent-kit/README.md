# dot-agent-kit

dot-agent-kit helps you create and manage AI-optimized documentation in your projects, making AI assistants more effective at understanding your codebase and development environment.

The `.agent/` directory contains documentation specifically written for AI consumption - structured knowledge about your tools, patterns, conventions, and architectural decisions. Unlike traditional documentation written for humans, these documents are optimized for how AI agents process and apply information.

When an AI agent works with your codebase, it needs to understand not just your code but also your development tools, project conventions, and architectural patterns. Without this context, agents waste time rediscovering the same information in every session. The `.agent/` directory serves as a token cache - pre-computed understanding that agents can load immediately instead of deriving from scratch. This makes AI interactions faster, more consistent, and capable of handling more complex tasks.

dot-agent-kit installs dot-agent, which manages the .agent directory. It has a package system, which installs existing curated docuemnts into your local .agent file, adn then CLI utilities for inspecting those files.

## CLIs > MCPs for Local Development

dot-agent also seeks to provide an improved experience for agentic use of CLIs. For local development, CLIs are simply more effective than Model Context Protocol (MCP) servers. CLIs are battle-tested, immediately available, require zero setup, and work exactly the same way whether a human or AI is using them. Even Anthropic acknowledges MCP's overhead - their documentation notes that MCP is designed for "persistent services" and "stateful connections," while simpler integrations often don't need this complexity.

The real challenge with CLIs isn't execution - it's comprehension. Without proper context, agents waste dozens of turns discovering command patterns, understanding flags, and learning tool-specific workflows. This is where dot-agent-kit shines: instead of building complex server infrastructure, we provide agents with pre-computed, agent-optimized documentation of CLIs. A single markdown file containing command patterns, common workflows, and tool philosophy turns an agent from a confused beginner into an expert user instantly.

## Installation

Getting started takes about 30 seconds. You'll need Python 3.13 or later:

```bash
pip install dot-agent-kit
# or if you're using uv
uv add dot-agent-kit
```

## Your First Setup

Let's create your `.agent` directory. Navigate to your project root and run:

```bash
dot-agent init
```

This creates a new `.agent/` directory with AI-optimized documentation for development tools, architectural patterns, and programming best practices. Want to see what documentation is now available?

```bash
dot-agent list
```

You'll see all the documentation files that AI agents can reference. Each file includes a description showing what knowledge it provides - from tool mental models like Graphite and GitHub CLI to broader patterns for agentic programming.

As tools evolve and best practices improve, you can update your documentation:

```bash
dot-agent sync
```

Not sure what would change? Run `dot-agent sync --dry-run` first to preview updates without applying them.

## How It Works

The `.agent/` directory provides AI agents with structured, optimized documentation about your project. This includes both curated knowledge from dot-agent-kit and your own project-specific documentation.

### AI-Optimized Documentation

Unlike traditional documentation written for humans, `.agent` documents are structured for AI consumption. They emphasize patterns over prose, use clear hierarchies for rapid scanning, and include rich examples that agents can pattern-match against. This optimization means agents can quickly extract and apply knowledge without parsing through conversational text.

The directory structure looks like this:

```
.agent/
  packages/                    # Curated AI documentation from dot-agent-kit
    tools/                     # Tool mental models
      gt/                      # Graphite CLI patterns and concepts
        gt.md
      gh/                      # GitHub CLI workflows
        gh.md
    agentic_programming_guide/ # Best practices for AI-assisted development
      AGENTIC_PROGRAMMING.md
  ARCHITECTURE.md              # Your project's architectural decisions
  PATTERNS.md                  # Your coding patterns and conventions
  EXCEPTION_HANDLING.md        # Your error handling philosophy
```

### Installed vs Local Documentation

The `packages/` directory contains curated documentation that dot-agent-kit maintains. These include tool mental models, programming patterns, and best practices that apply across projects. When you run `dot-agent sync`, these files update to incorporate improvements and new knowledge.

Your local documentation lives in the `.agent/` root directory. These files capture your project's unique patterns, architectural decisions, and conventions. They're never modified by dot-agent-kit, giving you full control over your project-specific knowledge.

### Your Configuration

When you run `dot-agent check`, you can see the status of everything: what's up to date, what's been modified, and what updates are available. It's a good idea to run this before syncing to understand what will change.

## Writing Effective AI Documentation

AI-optimized documentation differs from traditional human-focused docs. Here are the key principles:

### Structure Over Narrative

Instead of explanatory paragraphs, use clear hierarchies and bullet points:

```markdown
## API Authentication

- Method: Bearer token in Authorization header
- Token lifetime: 24 hours
- Refresh endpoint: POST /auth/refresh
- Rate limits: 100 requests/minute
```

### Rich Examples Over Descriptions

Show patterns through contrasting examples:

````markdown
## State Management

✅ GOOD: Check state before operations

```python
if self.connection.is_open():
    self.connection.send(data)
```
````

❌ BAD: Assume state is valid

```python
self.connection.send(data)  # May fail if closed
```

````

### Patterns and Anti-Patterns
Document both what to do and what to avoid, with clear reasoning:
```markdown
## Testing Philosophy

PATTERN: Use in-memory fakes for fast tests
- Reason: Millisecond execution, no external dependencies
- Example: FakeDatabase with injectable state

ANTI-PATTERN: Mock individual methods
- Problem: Brittle tests that break with refactoring
- Problem: Requires deep implementation knowledge
````

## Common Workflows

### Starting Fresh

When setting up a new project:

```bash
cd my-project
dot-agent init
```

This creates your initial `.agent/` directory with curated documentation for tools and development patterns. Your AI assistant immediately gains understanding of common tools and best practices.

### Evolving Your Knowledge Base

As your project grows, continuously capture important patterns and decisions:

1. **When you discover a pattern** - Document it immediately in `.agent/PATTERNS.md`
2. **When you make architectural decisions** - Add rationale to `.agent/ARCHITECTURE.md`
3. **When you establish conventions** - Codify them in appropriate documentation
4. **When AI agents struggle** - Create documentation to prevent future confusion

### Keeping Documentation Current

Both curated and local documentation need maintenance:

```bash
dot-agent check        # Review status of all documentation
dot-agent sync         # Update curated packages to latest versions
```

The sync command only updates files in `packages/`. Your local documentation evolves through deliberate curation as your project grows.

### Building Your Knowledge Base

Beyond tool documentation, the `.agent/` directory should capture your project's unique patterns and decisions. This is where AI-optimized documentation really shines:

```bash
# Architectural decisions and rationale
echo "# Architecture Decisions" > .agent/ARCHITECTURE.md

# Project-specific patterns with examples
echo "# Code Patterns" > .agent/PATTERNS.md

# Exception handling philosophy
echo "# Error Handling Conventions" > .agent/EXCEPTION_HANDLING.md

# Testing strategies and examples
echo "# Testing Guide" > .agent/TESTING.md
```

These documents should be written for AI consumption - emphasizing patterns over prose, including rich examples, and using clear hierarchical structure. For instance, your PATTERNS.md might contain:

````markdown
## Database Operations

### Pattern: Always check existence before operations

```python
# ✅ CORRECT
if user_id in database:
    user = database[user_id]

# ❌ WRONG - may raise KeyError
user = database[user_id]
```
````

This format helps AI agents quickly understand and apply your project's conventions.

### Working with Front Matter

Documentation files can include metadata using YAML front matter. This helps both you and the AI understand what each document contains:

```markdown
---
description: "Mental model and command reference for Graphite (gt) CLI"
url: "https://graphite.dev/docs"
---

# Graphite (gt) Documentation

...
```

The description appears when you run `dot-agent list`, making it easy to understand what knowledge is available. The URL provides a reference to the original documentation source.

## Command Reference

Here are all the commands at a glance:

- `dot-agent init` - Create a new `.agent/` directory with default packages
- `dot-agent sync` - Update packages to their latest versions
- `dot-agent sync --dry-run` - Preview what would change without applying updates
- `dot-agent list` - Show all available documentation files
- `dot-agent check` - Review the status of all files and pending updates

## Development Setup

If you're contributing to dot-agent-kit itself, here's how to get set up:

```bash
uv run pytest packages/dot-agent-kit/tests
uv run ruff format packages/dot-agent-kit
uv run pyright packages/dot-agent-kit/src
```

The codebase follows Workstack coding standards, using LBYL exception handling, absolute imports, and Click for CLI output.

### Contributing Documentation to Resources

When adding or modifying documentation in `src/dot_agent_kit/resources/`, follow these rules:

#### Internal Link Consistency

All internal links must use relative paths within the resources directory:

```markdown
✅ CORRECT: See `../../agentic_programming_guide/AGENTIC_PROGRAMMING.md`
❌ WRONG: See `.agent/packages/agentic_programming_guide/AGENTIC_PROGRAMMING.md`
```

Links should reflect the actual directory structure in `src/dot_agent_kit/resources/`, not the installed structure in user projects.

#### Package Independence

Packages should not reference other packages except for first-party packages:

- **Tool packages** (tools/gh/, tools/gt/, tools/workstack/) - Must be independent, no cross-references
- **First-party packages** (tools/dot_agent/, agentic_programming_guide/) - Can reference each other

```markdown
✅ ALLOWED: dot_agent can reference agentic_programming_guide
✅ ALLOWED: agentic_programming_guide can reference dot_agent
❌ FORBIDDEN: workstack cannot reference gt
❌ FORBIDDEN: agentic_programming_guide cannot reference gt
```

This ensures packages remain decoupled and can be installed independently without creating dependency chains.

## Getting Help

If something isn't working as expected, start by running `dot-agent check` to validate your setup. This will identify any issues with file structure or configuration.
