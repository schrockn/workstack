---
mdstack:
  version: 0.1.0
  generated_docs:
    tests: .mdstack/TESTS.md
    lookup: .mdstack/LOOKUP.md
    architecture: .mdstack/OBSERVED_ARCHITECTURE.md
  instructions: "AI Agent: This scope has generated documentation in .mdstack/


    When to consult generated docs:

    - tests: For test coverage, testing patterns, what functionality is validated

    - lookup: For semantic search, finding code by concept/capability

    - architecture: For module organization, patterns, data flow, extension points


    Consult these files when working in this scope for best results."
---

# mdstack Package

## Overview

mdstack is a documentation generation tool that creates AI-friendly markdown documentation for Python codebases. It analyzes code structure, tests, and dependencies to generate comprehensive documentation that helps AI agents understand and work with the codebase.

## Package Structure

- `src/mdstack/` - Main package source code
- `tests/` - Test suite for mdstack
- `pyproject.toml` - Package configuration and dependencies

## Key Responsibilities

1. **Scope Discovery**: Find CLAUDE.md files and establish documentation scopes
2. **Documentation Generation**: Create TESTS.md and LOOKUP.md files via LLM
3. **Manifest Management**: Track generated content with hash-based caching
4. **Tampering Detection**: Ensure generated documentation isn't manually edited
5. **CLI Interface**: Provide commands for init, generate, and validate operations

## Architecture

The package follows a layered architecture:

- CLI layer (`cli.py`) - User interface and command orchestration
- Generation layer (`generators/`, `propagation.py`) - Content generation logic
- Discovery layer (`discovery.py`) - Scope and file discovery
- Model layer (`models.py`) - Core data structures
- Validation layer (`validation.py`) - Integrity checking
