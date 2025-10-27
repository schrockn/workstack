# dev-runners-da-kit

Development runner agents for Claude Code, providing cost-optimized execution of common development tools.

## Included Agents

This kit provides specialized runner agents for:

- **pytest-runner**: Execute pytest commands and parse test results
- **ruff-runner**: Run ruff linting and formatting with auto-fix
- **pyright-runner**: Execute pyright type checking
- **prettier-runner**: Run prettier formatting checks

All runners use the Haiku model for cost-efficient execution while delegating analysis to the main agent.

## Installation

### Via pip (from GitHub)

```bash
pip install git+https://github.com/workstack/workstack#subdirectory=packages/dev-runners-da-kit
```

### Via uv (from GitHub)

```bash
uv pip install git+https://github.com/workstack/workstack#subdirectory=packages/dev-runners-da-kit
```

## Usage with dot-agent

After installing the package:

```bash
# Initialize the kit in your project
dot-agent init --package dev-runners-da-kit

# This will install agents to .claude/agents/:
# - pytest-runner.md
# - ruff-runner.md
# - pyright-runner.md
# - prettier-runner.md
```

## How It Works

Each runner agent:

1. Executes the specified command using the Bash tool
2. Parses the output for key information (errors, warnings, counts)
3. Reports results back to the parent agent concisely
4. Uses Haiku model for cost optimization

The parent agent (using Sonnet) handles decision-making and analysis, while runners handle pure execution.

## Development

This kit is maintained as part of the workstack monorepo. The source of truth is in `.claude/agents/` and synced to this package using:

```bash
make sync-dev-runners-kit
```

## License

MIT
