# Semantic Lookup Index

## Document Generation and LLM Integration

**Search phrases**: document generation, generate documentation, LLM-based documentation, AI-powered docs, markdown generation, automated documentation, content generation

**Files**: packages/mdstack/src/mdstack/generators/base.py, packages/mdstack/src/mdstack/generators/tests.py, packages/mdstack/src/mdstack/generators/lookup.py, packages/mdstack/src/mdstack/generators/architecture.py

**Description**: Core infrastructure for generating documentation using LLM analysis. Handles communication with language models, prompt construction, and caching strategies for efficient document generation.

## Test Coverage Documentation

**Search phrases**: test documentation, test coverage analysis, testing patterns, test file analysis, validation documentation, test scope, test purpose

**Files**: packages/mdstack/src/mdstack/generators/tests.py

**Description**: Generates TESTS.md documentation by analyzing test files to describe coverage areas, testing patterns, and validation scope. Identifies both local test files and related tests in sibling directories.

## Semantic Search and Concept Mapping

**Search phrases**: semantic lookup, concept mapping, search index, natural language search, capability discovery, code search, find functionality

**Files**: packages/mdstack/src/mdstack/generators/lookup.py

**Description**: Generates LOOKUP.md documentation that maps natural language concepts and search phrases to relevant code files, enabling semantic discovery of functionality without requiring knowledge of specific class or function names.

## Architecture and Module Organization

**Search phrases**: architecture documentation, module organization, code structure, design patterns, architectural patterns, system design, component relationships

**Files**: packages/mdstack/src/mdstack/generators/architecture.py

**Description**: Generates OBSERVED_ARCHITECTURE.md documentation describing module organization, core abstractions, data flow, extension points, and architectural patterns to help AI agents understand code structure and relationships.

## LLM Caching and Performance Optimization

**Search phrases**: LLM caching, prompt caching, cache control, performance optimization, token efficiency, cache reuse, cache invalidation

**Files**: packages/mdstack/src/mdstack/generators/base.py

**Description**: Implements multi-block caching strategy for LLM prompts to maximize cache hits across multiple document generators. Uses ephemeral cache control with universal base instructions and shared content blocks to reduce token usage and improve performance.

## Child Package Documentation Integration

**Search phrases**: child packages, subpackages, nested documentation, documentation inheritance, child scope docs, package hierarchy

**Files**: packages/mdstack/src/mdstack/generators/base.py, packages/mdstack/src/mdstack/generators/tests.py, packages/mdstack/src/mdstack/generators/lookup.py, packages/mdstack/src/mdstack/generators/architecture.py

**Description**: Loads and integrates documentation from child packages into parent scope documentation, enabling hierarchical documentation that references and incorporates child package information.

## Source File Discovery and Loading

**Search phrases**: file discovery, source file loading, Python file detection, test file detection, file content reading, scope analysis

**Files**: packages/mdstack/src/mdstack/generators/base.py, packages/mdstack/src/mdstack/generators/tests.py

**Description**: Discovers and loads Python source files, test files, and related test files from scopes. Handles file filtering, content reading, and organization of files for documentation generation.

## Prompt Construction and System Messages

**Search phrases**: prompt engineering, system messages, prompt blocks, dynamic prompts, instruction formatting, LLM instructions

**Files**: packages/mdstack/src/mdstack/generators/base.py, packages/mdstack/src/mdstack/generators/tests.py, packages/mdstack/src/mdstack/generators/lookup.py, packages/mdstack/src/mdstack/generators/architecture.py

**Description**: Constructs multi-block system messages with generator-specific instructions, shared content, and dynamic prompts. Organizes instructions into reusable blocks for optimal LLM cache utilization.

## Repository Path Management

**Search phrases**: repository paths, relative paths, path normalization, file path handling, repo-relative paths, path utilities

**Files**: packages/mdstack/src/mdstack/generators/base.py, packages/mdstack/src/mdstack/generators/tests.py

**Description**: Manages repository-relative paths for all file references in documentation, ensuring consistent and navigable file paths across generated documents.

## Generator Abstraction and Extensibility

**Search phrases**: generator pattern, abstract base class, generator interface, extensible generators, document generator framework, generator implementation

**Files**: packages/mdstack/src/mdstack/generators/base.py

**Description**: Provides abstract base class for document generators with common functionality for loading files, building prompts, and managing LLM communication. Enables creation of new generator types by implementing abstract methods.

## Related Test File Discovery

**Search phrases**: related tests, test file matching, test conventions, test location discovery, sibling test directories, test-source mapping

**Files**: packages/mdstack/src/mdstack/generators/tests.py

**Description**: Discovers test files in sibling test directories that exercise code in the current scope, using naming conventions to match source files with their corresponding tests.