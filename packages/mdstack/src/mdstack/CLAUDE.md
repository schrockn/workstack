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

# mdstack Core Package

## Overview

This is the main Python package for mdstack, containing all implementation code for documentation generation.

## Module Organization

### Core Modules

- `cli.py` - Click-based command-line interface
- `models.py` - Core data structures (Scope, Manifest)
- `discovery.py` - Scope and file discovery logic
- `propagation.py` - Bottom-up and propagating generation
- `validation.py` - Tampering detection and integrity checks
- `manifest.py` - Manifest creation and persistence
- `hashing.py` - Content hashing utilities
- `config.py` - Configuration loading and management

### Generators

- `generators/tests.py` - TestsGenerator for TESTS.md
- `generators/lookup.py` - LookupGenerator for LOOKUP.md
- `generators/base.py` - Base generator interface

### LLM Integration

- `llm/client.py` - LLM client abstraction
- `llm/anthropic_client.py` - Anthropic Claude implementation

## Key Patterns

1. **Frozen Dataclasses**: All models are immutable for safety
2. **LBYL Error Handling**: Check conditions before acting
3. **Bottom-Up Generation**: Process leaf scopes first, then parents
4. **Hash-Based Caching**: Skip regeneration when content unchanged
5. **ABC-Based Interfaces**: Use abstract base classes for extensibility

## Dependencies

- `anthropic` - Claude AI client
- `click` - CLI framework
- Standard library: `pathlib`, `hashlib`, `json`, `dataclasses`
