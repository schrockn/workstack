# .agent Directory Structure

This directory contains curated documentation and context for AI agents.

## Directory Layout

```
.agent/
  packages/               # Installed documentation packages
    tools/               # CLI tool documentation
      {tool-name}/       # Package for CLI tool {tool-name}
        *.md            # Documentation files
    {package-name}/      # Other documentation packages
      *.md              # Documentation files

  # Project-specific files (root level)
  CUSTOM_RULES.md        # Your project-specific guidelines
  PROJECT_STANDARDS.md   # Your coding standards
  *.md                  # Any other project documentation
```

## Package System

### Installed Packages (`packages/`)

All directories under `packages/` are installed by `dot-agent-kit` and should not be edited directly:

- **Bundled packages** are synced from dot-agent-kit releases
- **Local packages** are copied from other locations
- **Git packages** are pulled from external repositories

To update installed packages, use `dot-agent sync`.

### Tool Packages (`packages/tools/`)

The `tools/` namespace has special meaning:

- **Convention**: `packages/tools/{name}/` contains documentation for CLI tool `{name}`
- **Example**: `packages/tools/gt/` contains documentation for the `gt` (Graphite) CLI
- **Purpose**: Enables agents to discover tool documentation automatically

When an agent detects mention of a CLI tool (like `gt`, `gh`, `workstack`), it can load the corresponding package from `packages/tools/{tool-name}/` for context.

### Other Packages

Non-tool packages provide general curated documentation:

- `packages/agentic_programming_guide/` - Best practices for working with AI agents
- `packages/{custom-package}/` - Any other curated content

## Project-Specific Files (Root Level)

Files at the root of `.agent/` are **project-specific** and **never touched by sync**:

- Create your own guidelines: `CUSTOM_RULES.md`
- Document your standards: `PROJECT_STANDARDS.md`
- Add any project context as markdown files

These files persist across package updates and are meant for your project's unique context.

## For AI Agents

When working in a repository with a `.agent/` directory:

1. **Read this README** first to understand the structure
2. **Check for project-specific files** at the root (CUSTOM_RULES.md, etc.)
3. **Load tool packages** from `packages/tools/{name}/` when using that CLI tool
4. **Reference other packages** as needed for general guidance

The package system helps you find relevant, curated documentation without cluttering your context with everything at once.
