# Observed Architecture

## Overview

The mdstack core package provides a hierarchical documentation generation system for Python codebases. It orchestrates the discovery of documentation scopes (directories with CLAUDE.md files), generates three types of documentation (TESTS.md, LOOKUP.md, OBSERVED_ARCHITECTURE.md) using LLM analysis, and manages documentation integrity through hashing and tampering detection. The architecture emphasizes bottom-up generation (leaf scopes first), immutable data structures, and extensible generator patterns.

## Module Organization

### packages/mdstack/src/mdstack/cli.py
**Responsibility**: Command-line interface providing user-facing commands for initialization, generation, validation, and search operations. Handles configuration loading, scope discovery, and orchestration of generation workflows.
**Key exports**: `cli` (Click group), `init`, `generate`, `check`, `lookup`, `rehash` (subcommands)
**Key patterns**: Click decorators for command definition, context passing for configuration, error handling with styled output

### packages/mdstack/src/mdstack/models.py
**Responsibility**: Core data structures representing scopes and manifests. Provides immutable, frozen dataclasses with factory methods for safe object creation.
**Key exports**: `Scope` (frozen dataclass), `Manifest` (frozen dataclass)
**Key patterns**: Frozen dataclasses for immutability, factory methods with validation

### packages/mdstack/src/mdstack/discovery.py
**Responsibility**: Discovers CLAUDE.md files in the repository and builds the scope hierarchy by establishing parent-child relationships between scopes.
**Key exports**: `discover_scopes()`, `find_parent_scope()`, `find_scope_by_path()`, `find_child_scopes()`, `find_scope_and_descendants()`
**Key patterns**: Depth-first directory traversal, two-pass scope building (create scopes, then establish relationships)

### packages/mdstack/src/mdstack/propagation.py
**Responsibility**: Orchestrates bottom-up documentation generation across scopes. Manages generation workflow, statistics tracking, and frontmatter updates.
**Key exports**: `generate_bottom_up()`, `propagate_generate()`, `ensure_scope_files()`, `GenerationStats` (dataclass)
**Key patterns**: Bottom-up processing (deepest scopes first), statistics aggregation, frontmatter management

### packages/mdstack/src/mdstack/manifest.py
**Responsibility**: Manages manifest persistence and staleness detection. Manifests store content hashes and metadata for change detection and tampering validation.
**Key exports**: `load_manifest()`, `save_manifest()`, `is_stale()`
**Key patterns**: JSON-based persistence, backward compatibility for missing fields

### packages/mdstack/src/mdstack/validation.py
**Responsibility**: Detects manual edits to generated files by comparing current content hashes against manifest hashes. Prevents accidental overwriting of user modifications.
**Key exports**: `validate_no_tampering()`, `check_all_scopes()`, `TamperDetectionError` (exception)
**Key patterns**: Hash-based integrity checking, exception-based error signaling

### packages/mdstack/src/mdstack/hashing.py
**Responsibility**: Provides cryptographic hashing utilities for content integrity verification and change detection.
**Key exports**: `compute_hash()`, `compute_combined_hash()`
**Key patterns**: SHA-256 hashing, string encoding normalization

### packages/mdstack/src/mdstack/frontmatter.py
**Responsibility**: Parses and manages YAML frontmatter in markdown files. Handles mdstack metadata injection while preserving user content.
**Key exports**: `parse_frontmatter()`, `build_mdstack_frontmatter()`, `merge_frontmatter()`, `serialize_frontmatter()`, `update_claude_md_frontmatter()`
**Key patterns**: YAML parsing with error recovery, frontmatter preservation, metadata versioning

### packages/mdstack/src/mdstack/paths.py
**Responsibility**: Utilities for repository-relative path handling. Converts absolute paths to repository-relative paths for consistent documentation references.
**Key exports**: `find_repo_root()`, `make_repo_relative()`
**Key patterns**: Git-based repository detection, fallback to filename-only paths

### packages/mdstack/src/mdstack/package_detection.py
**Responsibility**: Detects Python package structure by parsing pyproject.toml. Discovers source and test directories for automatic CLAUDE.md creation.
**Key exports**: `detect_package_root()`, `discover_python_packages()`, `PackageLayout` (dataclass)
**Key patterns**: TOML parsing with fallback defaults, recursive package discovery

### packages/mdstack/src/mdstack/__init__.py
**Responsibility**: Package initialization and namespace marker.

## Subpackages

### packages/mdstack/src/mdstack/generators/
**Purpose**: Document generation infrastructure with pluggable generators for different documentation types. Implements template method pattern with LLM cache optimization.
**Organization**: Abstract base class (`base.py`) defines common workflow; concrete implementations (`tests.py`, `lookup.py`, `architecture.py`) provide document-type-specific logic.
**Key responsibility**: Load source files, construct system message blocks with cache control, invoke LLM, return formatted documentation.

### packages/mdstack/src/mdstack/llm/
**Purpose**: LLM client abstraction and configuration management. Supports multiple providers and per-file-type model selection.
**Organization**: Abstract client interface (`client.py`), configuration management (`config.py`), provider implementations.
**Key responsibility**: Handle API communication, token tracking, cost estimation, and cache metrics.

## Core Abstractions

### Scope
**Location**: packages/mdstack/src/mdstack/models.py
**Purpose**: Represents a documentation scope - a directory with CLAUDE.md that gets .mdstack/ documentation generated.
**Type**: Frozen dataclass
**Key attributes**:
- `path` - Directory containing CLAUDE.md
- `claude_md_path` - Path to CLAUDE.md file
- `mdstack_dir` - Path to .mdstack/ directory
- `parent_scope` - Reference to parent scope (if nested)

**Key method**: `create()` - Factory method with validation

**Design rationale**: Immutability ensures scope objects can be safely shared and cached. Parent-child relationships enable hierarchical documentation.

### Manifest
**Location**: packages/mdstack/src/mdstack/models.py
**Purpose**: Metadata about generated documentation including content hashes and generation parameters.
**Type**: Frozen dataclass
**Key attributes**:
- `content_hash` - Combined hash of all generated docs
- `tests_hash`, `lookup_hash`, `architecture_hash` - Individual file hashes
- `generated_at` - ISO timestamp
- `llm_provider`, `llm_model` - Generation metadata
- `generator_version` - mdstack version

**Design rationale**: Enables change detection (skip regeneration if hash unchanged) and tampering detection (verify files match hashes).

### GenerationStats
**Location**: packages/mdstack/src/mdstack/propagation.py
**Purpose**: Aggregates statistics across all scopes during generation (token usage, costs, cache metrics).
**Type**: Dataclass with mutable fields
**Key attributes**: `total_scopes`, `scopes_generated`, `scopes_skipped`, `total_tokens`, `total_cost`, `cache_hits`, `file_stats`

**Design rationale**: Enables comprehensive reporting of generation results and cost tracking.

### TamperDetectionError
**Location**: packages/mdstack/src/mdstack/validation.py
**Purpose**: Exception raised when manual edits are detected in generated files.
**Type**: Custom exception class

**Design rationale**: Explicit exception type enables specific error handling and clear error messages.

## Critical Functions

### discover_scopes()
**Location**: packages/mdstack/src/mdstack/discovery.py
**Purpose**: Finds all CLAUDE.md files in repository and builds scope hierarchy with parent-child relationships.
**Key behavior**:
- Recursively searches for CLAUDE.md files
- Creates Scope objects for each file
- Establishes parent-child relationships by walking up directory tree
- Returns scopes in dependency order (parents before children)

**Design rationale**: Two-pass approach (create scopes, then establish relationships) ensures all scopes exist before linking.

### generate_bottom_up()
**Location**: packages/mdstack/src/mdstack/propagation.py
**Purpose**: Main entry point for documentation generation. Processes all scopes in bottom-up order (deepest first).
**Key behavior**:
- Sorts scopes by depth (leaf scopes first)
- For each scope: loads existing manifest, generates three doc types, computes hashes
- Skips regeneration if content hash unchanged
- Saves manifest with new hashes
- Aggregates statistics across all scopes
- Logs comprehensive summary

**Design rationale**: Bottom-up processing ensures parent scopes can reference child documentation. Hash-based caching avoids unnecessary regeneration.

### ensure_scope_files()
**Location**: packages/mdstack/src/mdstack/propagation.py
**Purpose**: Ensures CLAUDE.md exists with mdstack frontmatter and creates AGENTS.md symlink.
**Key behavior**:
- Creates CLAUDE.md if missing
- Updates frontmatter in existing CLAUDE.md while preserving user content
- Creates AGENTS.md as symlink to CLAUDE.md
- Only writes if content changed

**Design rationale**: Frontmatter injection enables AI agents to discover generated documentation. Symlink provides alternative access path.

### validate_no_tampering()
**Location**: packages/mdstack/src/mdstack/validation.py
**Purpose**: Verifies that generated files match manifest hashes, detecting manual edits.
**Key behavior**:
- Loads manifest for scope
- Computes current hash of each generated file
- Compares against manifest hashes
- Raises TamperDetectionError if mismatch detected

**Design rationale**: Hash-based validation is fast and reliable. Prevents accidental overwriting of user modifications.

### update_claude_md_frontmatter()
**Location**: packages/mdstack/src/mdstack/frontmatter.py
**Purpose**: Updates CLAUDE.md with mdstack frontmatter while preserving user content.
**Key behavior**:
- Parses existing frontmatter and body
- Builds mdstack metadata section
- Merges with existing frontmatter
- Serializes back to markdown format

**Design rationale**: Preserves user content while injecting agent instructions. Enables documentation discovery.

### detect_package_root()
**Location**: packages/mdstack/src/mdstack/package_detection.py
**Purpose**: Detects Python package structure by parsing pyproject.toml.
**Key behavior**:
- Searches for pyproject.toml in directory
- Parses tool.setuptools.packages.find.where for source directories
- Parses tool.pytest.ini_options.testpaths for test directories
- Falls back to ["src"] and ["tests"] if not specified
- Returns None if no pyproject.toml or no directories exist

**Design rationale**: Enables automatic CLAUDE.md creation for Python subpackages without manual configuration.

### discover_python_packages()
**Location**: packages/mdstack/src/mdstack/package_detection.py
**Purpose**: Recursively discovers all Python packages (directories with __init__.py) under a root directory.
**Key behavior**:
- Finds all __init__.py files recursively
- Filters out __pycache__ and .egg-info directories
- Sorts by depth (deepest first)
- Returns list of package directory paths

**Design rationale**: Enables automatic scope creation for all Python subpackages in a project.

## Architectural Patterns

### Bottom-Up Generation
Documentation is generated from leaf scopes upward to root scopes. This enables:
- Parent scopes to reference and include child documentation
- Efficient caching (child docs generated once, reused by parents)
- Clear dependency ordering (no circular dependencies)

Implementation: `generate_bottom_up()` sorts scopes by depth (deepest first) before generation.

### Immutable Data Structures
Core models (Scope, Manifest) are frozen dataclasses, providing:
- Thread-safety guarantees
- Predictable behavior (no hidden mutations)
- Safe sharing across functions
- Clear intent (immutability signals these are value objects)

### Hash-Based Caching and Change Detection
Content hashes enable:
- Skip regeneration when content unchanged (performance optimization)
- Detect manual edits to generated files (tampering detection)
- Verify documentation integrity

Implementation: Manifest stores individual file hashes and combined hash. Generation compares new hash against old manifest.

### Factory Methods with Validation
Scope and Manifest use factory methods (`create()`) instead of direct instantiation:
- Validates inputs before object creation
- Centralizes validation logic
- Enables future extensibility (e.g., logging, metrics)

### Two-Pass Scope Discovery
Scope hierarchy is built in two passes:
1. First pass: Create Scope objects for each CLAUDE.md
2. Second pass: Establish parent-child relationships

This ensures all scopes exist before linking, avoiding incomplete relationships.

### Pluggable Generator Architecture
Generators inherit from abstract base class and implement document-type-specific logic:
- Template method pattern: base class defines workflow, subclasses override specific steps
- Enables adding new documentation types without modifying core code
- Shared infrastructure (file loading, LLM communication) in base class

### Configuration-Driven LLM Selection
LLM configuration supports per-file-type model selection:
- Different models can be used for lookup, tests, architecture
- Enables cost optimization (cheaper models for simpler tasks)
- Centralized configuration management

## Data Flow

### Generation Workflow
1. **Discovery**: `discover_scopes()` finds all CLAUDE.md files and builds hierarchy
2. **Sorting**: Scopes sorted by depth (deepest first)
3. **Per-Scope Generation**:
   - Load existing manifest (if any)
   - Create specialized LLM clients for each doc type
   - Invoke generators (TestsGenerator, LookupGenerator, ArchitectureGenerator)
   - Compute hashes of generated content
   - Compare against old manifest hash
   - If unchanged, skip file writing (optimization)
   - If changed: write files, save new manifest
4. **Statistics**: Aggregate token usage, costs, cache metrics
5. **Reporting**: Log comprehensive summary

### Scope Hierarchy Discovery
1. **Recursive Search**: Find all CLAUDE.md files using `rglob()`
2. **Scope Creation**: Create Scope object for each file
3. **Parent Linking**: For each scope, walk up directory tree to find parent scope
4. **Relationship Establishment**: Set parent_scope reference

### Tampering Detection
1. **Manifest Load**: Load manifest from .mdstack/.manifest.json
2. **Hash Computation**: Compute SHA-256 hash of each generated file
3. **Comparison**: Compare current hash against manifest hash
4. **Error Reporting**: Raise TamperDetectionError if mismatch

## Dependencies

**Internal**:
- `mdstack.models` - Core data structures
- `mdstack.discovery` - Scope discovery
- `mdstack.generators` - Document generation
- `mdstack.llm` - LLM client and configuration
- `mdstack.manifest` - Manifest persistence
- `mdstack.validation` - Tampering detection
- `mdstack.hashing` - Content hashing
- `mdstack.frontmatter` - Markdown frontmatter handling
- `mdstack.paths` - Path utilities
- `mdstack.package_detection` - Package structure detection

**External**:
- `anthropic` - Claude API client
- `click` - CLI framework
- `pyyaml` - YAML parsing
- `tomllib` - TOML parsing (Python 3.11+)
- Standard library: `pathlib`, `hashlib`, `json`, `dataclasses`, `abc`, `logging`, `time`, `typing`

## Extension Points

### Adding New Documentation Types
1. Create new generator class in `packages/mdstack/src/mdstack/generators/newtype.py`
2. Inherit from `DocumentGenerator` base class
3. Implement `get_filename()` returning output filename
4. Implement `generate()` with document-type-specific logic
5. Implement `_get_static_instructions()` with format guidelines
6. Update `_load_all_child_docs()` in base class to include new type
7. Register generator in propagation workflow

### Adding New LLM Providers
1. Create new client class in `packages/mdstack/src/mdstack/llm/client.py`
2. Inherit from `LLMClient` abstract base class
3. Implement `generate()` and `get_model_name()` methods