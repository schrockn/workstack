# Observed Architecture

## Overview

The `generators` package provides a pluggable architecture for generating three types of documentation (TESTS.md, LOOKUP.md, OBSERVED_ARCHITECTURE.md) from Python codebases using LLM analysis. It implements a template method pattern where a base class defines the common generation workflow, and specialized subclasses handle document-type-specific logic. The architecture is designed to maximize LLM cache efficiency through a carefully structured 4-block system message format.

## Module Organization

### packages/mdstack/src/mdstack/generators/base.py
**Responsibility**: Defines the abstract base class and shared infrastructure for all document generators. Implements the core generation workflow, content loading, and system message block construction with LLM cache optimization.
**Key exports**: `DocumentGenerator` (abstract base), `GenerationResult` (dataclass), `UNIVERSAL_BASE_INSTRUCTIONS` (shared prompt)

### packages/mdstack/src/mdstack/generators/tests.py
**Responsibility**: Generates TESTS.md documentation by analyzing test files and their relationship to source code. Implements test file discovery (both local and related tests in sibling directories) and formats test coverage information.
**Key exports**: `TestsGenerator` (concrete implementation)

### packages/mdstack/src/mdstack/generators/lookup.py
**Responsibility**: Generates LOOKUP.md semantic index documentation that maps natural language concepts to file paths. Provides searchable documentation for finding code by capability or concept.
**Key exports**: `LookupGenerator` (concrete implementation)

### packages/mdstack/src/mdstack/generators/architecture.py
**Responsibility**: Generates OBSERVED_ARCHITECTURE.md documentation describing module organization, architectural patterns, and how to work with the codebase. Focuses on helping AI agents understand code structure and extension points.
**Key exports**: `ArchitectureGenerator` (concrete implementation)

## Core Abstractions

### DocumentGenerator
**Location**: packages/mdstack/src/mdstack/generators/base.py
**Purpose**: Abstract base class defining the interface and shared implementation for all document generators
**Type**: ABC (Abstract Base Class)
**Key responsibilities**:
- Define abstract methods `generate()` and `get_filename()` that subclasses must implement
- Implement shared content loading methods (`_load_all_source_files()`, `_load_claude_md()`, `_load_all_child_docs()`)
- Build system message blocks with cache control for LLM optimization
- Format source files and child documentation for inclusion in prompts

### GenerationResult
**Location**: packages/mdstack/src/mdstack/generators/base.py
**Purpose**: Data container for generator output
**Type**: Frozen dataclass
**Fields**: `content` (str), `llm_response` (LLMResponse | None)

## Architectural Patterns

### Template Method Pattern
The base class defines the overall generation workflow:
1. Load shared content (source files, CLAUDE.md, child docs)
2. Load generator-specific content (e.g., test files for TestsGenerator)
3. Build system message blocks with cache control
4. Call LLM with dynamic prompt and system blocks
5. Return GenerationResult

Subclasses override `_get_static_instructions()` to provide document-type-specific guidance and implement generator-specific content loading in `generate()`.

### LLM Cache Optimization Strategy
The architecture uses a 4-block system message structure to maximize cache reuse:

**Block 1 (Universal)**: `UNIVERSAL_BASE_INSTRUCTIONS` - Shared across ALL generators and scopes. Contains core principles for documentation generation.

**Block 2 (Scope-shared)**: Source files, CLAUDE.md, and ALL child documentation (LOOKUP.md, OBSERVED_ARCHITECTURE.md, TESTS.md). This block is identical across all 3 generators within a scope, enabling cache hits when generating multiple document types.

**Block 3 (Generator-specific)**: Optional content only needed by specific generators (e.g., test files for TESTS.md). LOOKUP and ARCHITECTURE generators skip this block.

**Block 4 (Instructions)**: Generator-specific instructions and document format guidelines.

This structure achieves ~90% cache reuse within a scope: when generating TESTS.md after LOOKUP.md, Blocks 1-2 are cache hits, only Block 3-4 are new.

### Child Documentation Integration
All generators load ALL child documentation types (not just their own) into Block 2. This ensures:
- Identical Block 2 across generators → cache hits
- Child documentation is available for cross-referencing
- Generators can reference related documentation from child packages

### Content Loading Hierarchy
- `_load_all_source_files()`: Loads Python files (excluding tests) from scope directory
- `_find_subpackages()`: Discovers immediate subdirectories with Python modules
- `_load_all_child_docs()`: Loads documentation from child scopes for all doc types
- Generator-specific methods: `_find_test_files()`, `_find_related_test_files()` (TestsGenerator only)

## Critical Functions

### generate()
**Location**: packages/mdstack/src/mdstack/generators/base.py (abstract), implemented in subclasses
**Purpose**: Main entry point for document generation. Orchestrates content loading, system block construction, LLM invocation, and result formatting.
**Parameters**: `scope` (Scope), `all_scopes` (list[Scope] | None)
**Returns**: GenerationResult with generated content and optional LLM response

### _build_system_blocks()
**Location**: packages/mdstack/src/mdstack/generators/base.py
**Purpose**: Constructs the 4-block system message with cache control directives for optimal LLM cache reuse
**Parameters**: generator_specific_instructions, shared_content_block, generator_specific_content
**Returns**: list[dict] with cache_control metadata or None if caching disabled

### _build_shared_content_block()
**Location**: packages/mdstack/src/mdstack/generators/base.py
**Purpose**: Assembles Block 2 (shared content) by combining CLAUDE.md, source files, subpackages, and all child documentation
**Returns**: Formatted string or None if no content

### _find_test_files()
**Location**: packages/mdstack/src/mdstack/generators/tests.py
**Purpose**: Discovers test files in the immediate scope directory (test_*.py and *_test.py patterns)
**Returns**: Sorted list of Path objects

### _find_related_test_files()
**Location**: packages/mdstack/src/mdstack/generators/tests.py
**Purpose**: Finds test files in sibling tests/ directories that exercise code in this scope. Uses naming convention matching (src/package/module.py → tests/test_module.py)
**Returns**: Sorted list of Path objects

## Data Flow

1. **Initialization**: Generator instance created with LLMClient and cache settings
2. **Generation Request**: `generate(scope, all_scopes)` called with target scope
3. **Content Loading**: 
   - Load source files from scope directory
   - Load CLAUDE.md if present
   - Discover subpackages
   - Load all child documentation (LOOKUP, ARCHITECTURE, TESTS)
   - Load generator-specific content (e.g., test files)
4. **Block Construction**:
   - Build Block 2 (shared content) from loaded files
   - Build Block 3 (generator-specific) if applicable
   - Combine with Blocks 1 and 4 (instructions)
5. **LLM Invocation**: Send dynamic prompt + system blocks to LLM with cache control
6. **Result Return**: GenerationResult with content and optional LLM response metadata

## Dependencies

**Internal**:
- `mdstack.models.Scope`: Scope definition and metadata
- `mdstack.discovery.find_child_scopes()`: Child scope discovery
- `mdstack.paths`: Path utilities (find_repo_root, make_repo_relative)
- `mdstack.package_detection.detect_package_root()`: Package structure detection (TestsGenerator only)
- `mdstack.llm.client.LLMClient`: LLM communication interface

**External**:
- `pathlib.Path`: File system operations
- `abc.ABC, abstractmethod`: Abstract base class support
- `dataclasses.dataclass`: Data container definition

## Extension Points

### Adding a New Document Type
1. Create new generator class inheriting from `DocumentGenerator`
2. Implement `get_filename()` returning the output filename
3. Implement `generate()` with document-type-specific logic
4. Implement `_get_static_instructions()` with format guidelines
5. Load generator-specific content in `generate()` if needed
6. The base class handles system block construction and LLM invocation

### Customizing Cache Strategy
- Modify `_build_system_blocks()` to adjust block structure
- Change `enable_caching` parameter in constructor to disable caching
- Adjust `cache_ttl` parameter for different cache lifetimes

### Extending Content Loading
- Override `_load_all_source_files()` to include/exclude different file types
- Override `_find_subpackages()` to change subdirectory discovery logic
- Add new `_load_*()` methods for additional content types

## Common Agent Tasks

### Generating Documentation for a Scope
```python
generator = TestsGenerator(llm_client)
result = generator.generate(scope, all_scopes)
# result.content contains the generated markdown
```

### Adding Support for a New Documentation Type
1. Create new file `packages/mdstack/src/mdstack/generators/newtype.py`
2. Implement `NewTypeGenerator(DocumentGenerator)` with specific instructions
3. Register in generator factory/registry
4. Update `_load_all_child_docs()` to include new type in Block 2

### Debugging Cache Efficiency
- Enable verbose logging: `generator = TestsGenerator(llm_client, verbose=True)`
- Check `input_files` list in LLM call to verify what content is being sent
- Monitor LLM response metadata for cache hit/miss indicators
- Verify Block 2 is identical across consecutive generator runs

### Modifying Generation Instructions
- Edit `_get_static_instructions()` in specific generator class
- Instructions are in Block 4, changes don't affect cache of Blocks 1-3
- Test with verbose=True to see full system message sent to LLM