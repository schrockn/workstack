# Tests

## Overview

Comprehensive test suite for the mdstack package, covering core functionality including scope discovery, model validation, package detection, documentation generation, manifest management, and tampering detection.

## Tests in This Scope

### packages/mdstack/tests/test_discovery.py
**Purpose**: Validates the scope discovery mechanism that locates all CLAUDE.md files in a directory tree and establishes parent-child relationships between scopes.

**Scope**: Tests the discovery system that identifies scope boundaries and hierarchical relationships. Covers the core mechanism for finding all scopes in a repository and determining scope containment.

**Coverage**: 
- Happy path: Finding multiple CLAUDE.md files at different directory levels
- Relationships: Correctly identifying parent-child scope relationships
- Lookup: Finding the most specific scope for a given file path
- Edge cases: Nested scope hierarchies and scope boundary determination

### packages/mdstack/tests/test_models.py
**Purpose**: Validates the core data models (Scope and Manifest) that represent scopes and their metadata.

**Scope**: Tests the creation and validation of Scope and Manifest objects. Covers model initialization, path validation, and field assignment.

**Coverage**:
- Happy path: Creating valid Scope and Manifest instances with all required fields
- Error cases: Validation failures when required files (CLAUDE.md) don't exist
- Field validation: Ensuring paths are properly validated and stored

### packages/mdstack/tests/test_package_detection.py
**Purpose**: Validates the package layout detection system that reads pyproject.toml to identify source and test directories.

**Scope**: Tests the package structure detection mechanism that determines where source code and tests are located within a scope. Covers parsing of pyproject.toml configuration and directory validation.

**Coverage**:
- Happy path: Detecting source and test directories from pyproject.toml configuration
- Defaults: Falling back to standard src/ and tests/ directories when not explicitly configured
- Edge cases: Multiple source directories, missing directories, missing pyproject.toml, non-existent configured directories
- Filtering: Excluding directories that don't actually exist on the filesystem

### packages/mdstack/tests/test_manifest.py
**Purpose**: Validates the manifest persistence system that saves and loads scope metadata including content hashes and generation timestamps.

**Scope**: Tests manifest serialization, deserialization, and staleness detection. Covers the mechanism for tracking generated documentation state.

**Coverage**:
- Happy path: Saving and loading manifests with all metadata preserved
- Staleness detection: Identifying when manifests are missing or generated files are absent
- File system operations: Creating and reading manifest files from the .mdstack directory

### packages/mdstack/tests/test_validation.py
**Purpose**: Validates the tampering detection system that verifies generated documentation hasn't been manually edited by comparing file hashes against stored manifest values.

**Scope**: Tests the integrity checking mechanism that ensures generated files remain unmodified. Covers hash-based validation and error reporting for tampered files.

**Coverage**:
- Happy path: Validation passes when file hashes match manifest values
- Error cases: Detection of manually edited TESTS.md and LOOKUP.md files
- Batch operations: Checking multiple scopes and identifying which ones have been tampered with
- Hash comparison: Verifying that content changes are detected

### packages/mdstack/tests/test_hashing.py
**Purpose**: Validates the hashing utility functions used for content integrity verification.

**Scope**: Tests the cryptographic hashing mechanism that generates deterministic hashes of file content. Covers hash computation and combination.

**Coverage**:
- Determinism: Same content always produces the same hash
- Differentiation: Different content produces different hashes
- Combination: Multiple strings can be hashed together consistently

### packages/mdstack/tests/test_frontmatter.py
**Purpose**: Validates the YAML frontmatter parsing and serialization system used to embed mdstack metadata in CLAUDE.md files.

**Scope**: Tests frontmatter extraction, merging, and serialization. Covers the mechanism for maintaining mdstack configuration and instructions within CLAUDE.md files.

**Coverage**:
- Parsing: Extracting valid YAML frontmatter and handling invalid YAML gracefully
- Building: Creating mdstack-specific frontmatter sections with version and documentation paths
- Merging: Combining existing frontmatter with mdstack sections while preserving user data
- Serialization: Converting frontmatter and body back to markdown format
- Updates: Updating CLAUDE.md files with mdstack metadata while preserving user content
- Edge cases: Files without frontmatter, invalid YAML, existing mdstack sections

### packages/mdstack/tests/test_architecture_generator.py
**Purpose**: Validates the architecture documentation generator that analyzes scope structure and generates OBSERVED_ARCHITECTURE.md files.

**Scope**: Tests the architecture generation workflow including subpackage detection, file collection, and LLM integration. Covers the mechanism for analyzing scope organization and generating architectural documentation.

**Coverage**:
- Subpackage detection: Finding immediate subdirectories with Python files (one level deep only)
- File collection: Gathering top-level Python files and CLAUDE.md for analysis
- Nesting behavior: Correctly excluding nested subdirectory files from input
- Input file tracking: Verifying which files are included in LLM prompts for logging and debugging
- LLM integration: Capturing prompts and responses from the language model
- Edge cases: Nested directory structures, multiple subpackages, mixed file types

## Testing Patterns

The test suite employs several consistent patterns:

- **Temporary file systems**: Tests use `tempfile.TemporaryDirectory()` to create isolated file system environments without side effects
- **In-memory models**: Core data models are tested without I/O, using direct instantiation
- **Fake implementations**: LLM client interactions are tested with a `FakeLLMClient` that captures calls without making actual API requests
- **Explicit assertions**: Tests use clear, specific assertions with descriptive failure messages
- **Parametrized scenarios**: Multiple related test cases cover happy paths, error cases, and edge cases
- **Fixture-based setup**: Common test infrastructure (scopes, manifests, files) is created consistently across tests