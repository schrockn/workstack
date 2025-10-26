# Semantic Lookup Index

## Child Packages

- **generators** (.mdstack/LOOKUP.md): Document generation infrastructure with pluggable generators for TESTS.md, LOOKUP.md, and OBSERVED_ARCHITECTURE.md
- **llm** (.mdstack/LOOKUP.md): LLM client abstraction and configuration management for Anthropic API integration

## Command-Line Interface and User Interaction

**Search phrases**: CLI, command line, user commands, mdstack commands, generate command, init command, check command, lookup command, rehash command, terminal interface, argument parsing

**Files**: packages/mdstack/src/mdstack/cli.py

**Description**: Click-based command-line interface providing user-facing commands for initialization, documentation generation, validation, semantic search, and hash recomputation. Handles configuration loading, scope discovery, and user feedback with styled output.

## Scope Discovery and Hierarchy

**Search phrases**: find scopes, discover scopes, CLAUDE.md files, scope hierarchy, parent scope, child scope, scope relationships, directory hierarchy, scope detection

**Files**: packages/mdstack/src/mdstack/discovery.py

**Description**: Discovers all CLAUDE.md files in a repository and builds the scope hierarchy by establishing parent-child relationships. Enables finding scopes by path and discovering descendant scopes.

## Documentation Generation and Propagation

**Search phrases**: generate documentation, bottom-up generation, propagation, hierarchical generation, scope generation, documentation workflow, generation order, leaf-first processing

**Files**: packages/mdstack/src/mdstack/propagation.py

**Description**: Orchestrates documentation generation for scopes in bottom-up order (leaf scopes first). Handles manifest creation, file writing, frontmatter updates, and generation statistics tracking. Supports both full repository generation and targeted scope generation.

## Manifest and State Management

**Search phrases**: manifest, state tracking, generation metadata, hash storage, manifest loading, manifest saving, stale detection, documentation state

**Files**: packages/mdstack/src/mdstack/manifest.py

**Description**: Manages manifest files that track generation metadata including content hashes, timestamps, LLM provider/model information, and individual file hashes. Enables staleness detection and selective regeneration.

## Content Hashing and Integrity

**Search phrases**: hash, content hash, SHA-256, integrity checking, hash computation, combined hash, file hashing, content verification

**Files**: packages/mdstack/src/mdstack/hashing.py

**Description**: Computes SHA-256 hashes of generated content for integrity verification and change detection. Supports both individual file hashing and combined hashing of multiple files.

## Tampering Detection and Validation

**Search phrases**: tampering detection, manual edits, file validation, integrity verification, edit detection, file modification detection, content validation

**Files**: packages/mdstack/src/mdstack/validation.py

**Description**: Detects manual edits to generated .mdstack/ files by comparing current content hashes against manifest hashes. Prevents accidental or intentional modifications to generated documentation.

## Data Models and Core Structures

**Search phrases**: data models, Scope model, Manifest model, dataclasses, frozen dataclasses, immutable objects, core structures, data containers

**Files**: packages/mdstack/src/mdstack/models.py

**Description**: Defines core immutable data structures (Scope and Manifest) using frozen dataclasses. Provides factory methods with validation for safe object creation.

## Frontmatter Management

**Search phrases**: frontmatter, YAML frontmatter, metadata, markdown frontmatter, frontmatter parsing, frontmatter serialization, mdstack metadata, agent instructions

**Files**: packages/mdstack/src/mdstack/frontmatter.py

**Description**: Parses and manages YAML frontmatter in markdown files. Handles mdstack-specific frontmatter with agent instructions and documentation references. Supports merging new frontmatter with existing content while preserving user data.

## Path Utilities and Repository Navigation

**Search phrases**: repository paths, relative paths, path utilities, repo root detection, git detection, path normalization, file path handling, repository-relative paths

**Files**: packages/mdstack/src/mdstack/paths.py

**Description**: Utilities for finding repository root via .git detection and converting absolute paths to repository-relative paths. Enables consistent path representation across generated documentation.

## Python Package Detection

**Search phrases**: package detection, Python packages, pyproject.toml, package layout, source directories, test directories, package discovery, package structure, setuptools configuration

**Files**: packages/mdstack/src/mdstack/package_detection.py

**Description**: Detects Python package structure by parsing pyproject.toml. Discovers source and test directories, and recursively finds all Python packages (directories with __init__.py) within a repository.

## Configuration Management

**Search phrases**: configuration, config loading, YAML configuration, environment variables, LLM configuration, API keys, model selection, settings management

**Files**: packages/mdstack/src/mdstack/llm/config.py

**Child packages**: llm

**Description**: Loads and manages LLM configuration from YAML files or environment variables. Supports per-file-type model selection and API credential management.

## LLM Client Abstraction

**Search phrases**: LLM client, language model interface, provider abstraction, text generation, model abstraction, API client, LLM integration

**Files**: packages/mdstack/src/mdstack/llm/client.py

**Child packages**: llm

**Description**: Abstract base class and Anthropic implementation for LLM clients. Handles API communication, token tracking, cost estimation, and cache metrics for language model interactions.

## Initialization and Setup

**Search phrases**: initialize repository, setup, first-time setup, create CLAUDE.md, create configuration, repository initialization, project setup, mdstack setup

**Files**: packages/mdstack/src/mdstack/cli.py

**Description**: Initializes mdstack in a repository by discovering Python packages, creating CLAUDE.md files, establishing .mdstack directories, and generating configuration files with LLM settings.

## Documentation Validation and Health Checks

**Search phrases**: validation, health check, verify documentation, check staleness, check tampering, documentation status, freshness check, integrity check

**Files**: packages/mdstack/src/mdstack/cli.py, packages/mdstack/src/mdstack/manifest.py, packages/mdstack/src/mdstack/validation.py

**Description**: Validates that generated documentation is up-to-date and hasn't been manually edited. Provides status reporting on documentation freshness and integrity.

## Semantic Search and Lookup

**Search phrases**: semantic search, search documentation, find code by concept, lookup functionality, search index, concept mapping, capability discovery

**Files**: packages/mdstack/src/mdstack/cli.py

**Child packages**: generators

**Description**: Searches LOOKUP.md files across scopes for natural language queries, enabling discovery of code by concept or capability rather than specific names.

## Hash Recomputation and Repair

**Search phrases**: rehash, recompute hashes, repair manifests, fix hashes, hash update, manifest repair, integrity repair

**Files**: packages/mdstack/src/mdstack/cli.py, packages/mdstack/src/mdstack/hashing.py

**Description**: Recomputes content hashes for generated files and updates manifests. Useful for recovering from hash mismatches or manual file modifications.

## Dry-Run and Preview Functionality

**Search phrases**: dry run, preview, what-if analysis, preview changes, test generation, simulation, no-write mode

**Files**: packages/mdstack/src/mdstack/cli.py

**Description**: Provides dry-run mode for generation commands that previews what would be generated without writing files. Enables safe testing of generation before committing changes.

## Verbose Logging and Debugging

**Search phrases**: verbose logging, debug output, logging, verbose mode, debug mode, detailed output, request logging, performance metrics

**Files**: packages/mdstack/src/mdstack/cli.py, packages/mdstack/src/mdstack/llm/client.py

**Description**: Comprehensive logging system for debugging and monitoring. Supports verbose mode for detailed output including LLM requests, token usage, cache metrics, and timing information.

## Generation Statistics and Reporting

**Search phrases**: statistics, generation stats, token usage, cost tracking, performance metrics, summary reporting, generation report, token counting

**Files**: packages/mdstack/src/mdstack/propagation.py

**Description**: Tracks and reports comprehensive statistics about documentation generation including scope counts, file counts, token usage, cache performance, and cost estimates.

## Caching and Performance Optimization

**Search phrases**: caching, prompt caching, cache control, performance optimization, token efficiency, cache reuse, cache hits, cache misses, cache TTL

**Files**: packages/mdstack/src/mdstack/generators/base.py, packages/mdstack/src/mdstack/llm/client.py

**Child packages**: generators, llm

**Description**: Implements multi-block LLM prompt caching strategy to maximize cache reuse across multiple document generators. Tracks cache metrics and enables performance optimization.

## File Discovery and Content Loading

**Search phrases**: file discovery, load files, source files, test files, Python files, file content, file loading, file filtering, file organization

**Files**: packages/mdstack/src/mdstack/generators/base.py, packages/mdstack/src/mdstack/generators/tests.py

**Child packages**: generators

**Description**: Discovers and loads Python source files, test files, and related test files from scopes. Handles file filtering, content reading, and organization for documentation generation.

## Child Documentation Integration

**Search phrases**: child packages, subpackages, nested documentation, documentation inheritance, child scope docs, package hierarchy, documentation references, cross-package documentation

**Files**: packages/mdstack/src/mdstack/generators/base.py, packages/mdstack/src/mdstack/propagation.py

**Child packages**: generators

**Description**: Loads and integrates documentation from child packages into parent scope documentation. Enables hierarchical documentation that references and incorporates child package information.

## Scope-Specific File Generation

**Search phrases**: generate for scope, targeted generation, specific scope, scope-specific generation, partial generation, incremental generation

**Files**: packages/mdstack/src/mdstack/cli.py, packages/mdstack/src/mdstack/discovery.py

**Description**: Enables generation of documentation for a specific scope and its descendants rather than the entire repository. Useful for incremental updates and targeted regeneration.

## Auto-Discovery of Python Packages

**Search phrases**: auto-discover packages, automatic package detection, Python package discovery, subpackage detection, package structure detection, automatic CLAUDE.md creation

**Files**: packages/mdstack/src/mdstack/cli.py, packages/mdstack/src/mdstack/package_detection.py

**Description**: Automatically discovers Python packages during initialization and generation, creating CLAUDE.md files for packages that don't have them. Enables zero-configuration setup for multi-package repositories.