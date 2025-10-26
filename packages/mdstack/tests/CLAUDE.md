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

# mdstack Test Suite

## Overview

Comprehensive test suite for the mdstack package, covering all core functionality including scope discovery, generation, validation, and CLI commands.

## Test Organization

Tests are organized by module and functionality:

- Discovery tests - Scope and file discovery logic
- Generation tests - Documentation generation workflows
- Validation tests - Tampering detection and integrity
- CLI tests - Command-line interface behavior
- Generator tests - TESTS.md and LOOKUP.md generation
- Manifest tests - Manifest creation and persistence

## Testing Patterns

1. **In-memory fakes** - No I/O in unit tests
2. **Parametrized tests** - Test multiple scenarios efficiently
3. **Fixture-based setup** - Reusable test infrastructure
4. **Explicit assertions** - Clear failure messages
5. **Fast execution** - All tests run in < 1 second

## Key Test Files

Tests mirror the source structure under `packages/mdstack/src/mdstack/`.
