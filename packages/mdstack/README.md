# mdstack

Hierarchical documentation generator for codebases using LLM-powered semantic understanding.

## Overview

mdstack generates semantic documentation for Python projects by analyzing CLAUDE.md files and their associated scopes. It creates two types of documentation:

- **TESTS.md**: High-level descriptions of test files and their coverage
- **LOOKUP.md**: Semantic index mapping conceptual queries to relevant files

## Installation

```bash
cd packages/mdstack
uv sync
```

## Quick Start

1. **Initialize mdstack in your repository:**

```bash
export ANTHROPIC_API_KEY=your-key-here
uv run mdstack init
```

2. **Generate documentation:**

```bash
uv run mdstack generate
```

3. **Search for code:**

```bash
uv run mdstack lookup "feature creation"
```

4. **Check documentation freshness:**

```bash
uv run mdstack check
```

## Commands

- `mdstack init` - Initialize mdstack configuration
- `mdstack generate [SCOPE_PATH]` - Generate documentation for all or specific scope
- `mdstack check [--strict]` - Verify documentation is up-to-date
- `mdstack lookup QUERY` - Search semantic lookup index

## How It Works

1. **Scope Discovery**: Finds all directories with CLAUDE.md files
2. **Hierarchy Building**: Establishes parent-child relationships between scopes
3. **LLM Analysis**: Uses Claude to analyze code and generate semantic documentation
4. **Propagation**: Updates parent scopes when child scopes change
5. **Tamper Detection**: Prevents manual edits to generated documentation

## Configuration

Create `.mdstack.config.yaml` in your repository root:

```yaml
llm:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  api_key_env: ANTHROPIC_API_KEY
  max_tokens: 4000
  temperature: 0.1
```

## Phase 1 Features

- ✅ LLM-powered semantic documentation
- ✅ Hierarchical propagation
- ✅ Tamper detection
- ✅ Anthropic Claude integration
- ✅ CLI interface
- ✅ Smart caching

## Development

Run tests:

```bash
uv run pytest tests/ -v
```

Type checking:

```bash
uv run pyright
```

## License

Private software - unreleased.
