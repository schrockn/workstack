# Tests

## Child Packages

- **generators** (.mdstack/TESTS.md): Tests for document generation infrastructure including architecture, lookup, and tests document generators
- **llm** (.mdstack/TESTS.md): Tests for LLM client abstraction and configuration management

## Tests in This Scope

### packages/mdstack/tests/test_discovery.py
**Purpose**: Validates the scope discovery mechanism that locates all CLAUDE.md files in a directory tree and establishes parent-child relationships between scopes.

**Scope**: Tests the core discovery system that identifies scope boundaries and hierarchical relationships. Covers the mechanism for finding all scopes in a repository and determining scope containment and nesting.

**Coverage**: 
- Happy path: Finding multiple CLAUDE.md files at different directory levels and correctly building the scope hierarchy
- Relationships: Establishing and verifying parent-child scope relationships through directory traversal
- Lookup operations: Finding the most specific scope for a given file path
- Edge cases: Nested scope hierarchies, scope boundary determination, and sibling scope relationships

### packages/mdstack/tests/test_models.py
**Purpose**: Validates the core data models (Scope and Manifest) that represent scopes and their metadata throughout the system.

**Scope**: Tests the creation, validation, and behavior of immutable frozen dataclass models. Covers model initialization, path validation, factory methods, and field assignment.

**Coverage**:
- Happy path: Creating valid Scope and Manifest instances with all required fields and default values
- Error cases: Validation failures when required files (CLAUDE.md) don't exist or paths are invalid
- Factory methods: Proper initialization through factory methods with automatic timestamp generation
- Field validation: Ensuring paths are properly validated and stored as expected types

### packages/mdstack/tests/test_package_detection.py
**Purpose**: Validates the package layout detection system that reads pyproject.toml to identify source and test directories for automatic scope creation.

**Scope**: Tests the package structure detection mechanism that determines where source code and tests are located within a scope. Covers parsing of pyproject.toml configuration, directory validation, and recursive package discovery.

**Coverage**:
- Happy path: Detecting source and test directories from properly configured pyproject.toml files
- Configuration parsing: Extracting setuptools configuration including source directories and test paths
- Defaults: Falling back to standard src/ and tests/ directories when not explicitly configured
- Edge cases: Multiple source directories, missing directories, missing pyproject.toml, non-existent configured directories
- Filtering: Excluding directories that don't actually exist on the filesystem
- Recursive discovery: Finding all Python packages (directories with __init__.py) within a repository

### packages/mdstack/tests/test_manifest.py
**Purpose**: Validates the manifest persistence system that saves and loads scope metadata including content hashes and generation timestamps.

**Scope**: Tests manifest serialization, deserialization, and staleness detection. Covers the mechanism for tracking generated documentation state and detecting when regeneration is needed.

**Coverage**:
- Happy path: Saving and loading manifests with all metadata preserved including hashes and timestamps
- Staleness detection: Identifying when manifests are missing, outdated, or generated files are absent
- File system operations: Creating and reading manifest files from the .mdstack directory
- Backward compatibility: Handling manifests missing newer fields (e.g., architecture_hash) gracefully
- Hash tracking: Verifying that individual file hashes and combined hashes are stored and retrieved correctly

### packages/mdstack/tests/test_validation.py
**Purpose**: Validates the tampering detection system that verifies generated documentation hasn't been manually edited by comparing file hashes against stored manifest values.

**Scope**: Tests the integrity checking mechanism that ensures generated files remain unmodified. Covers hash-based validation, error reporting, and batch validation across multiple scopes.

**Coverage**:
- Happy path: Validation passes when file hashes match manifest values
- Error cases: Detection of manually edited TESTS.md, LOOKUP.md, and OBSERVED_ARCHITECTURE.md files
- Batch operations: Checking multiple scopes and identifying which ones have been tampered with
- Hash comparison: Verifying that content changes are reliably detected
- Error reporting: Proper exception raising and error message generation for tampered files

### packages/mdstack/tests/test_hashing.py
**Purpose**: Validates the hashing utility functions used for content integrity verification and change detection.

**Scope**: Tests the cryptographic hashing mechanism that generates deterministic hashes of file content. Covers hash computation, combination, and consistency.

**Coverage**:
- Determinism: Same content always produces the same hash across multiple invocations
- Differentiation: Different content produces different hashes reliably
- Combination: Multiple strings can be hashed together consistently and deterministically
- Encoding: Proper handling of string encoding for consistent hash computation

### packages/mdstack/tests/test_frontmatter.py
**Purpose**: Validates the YAML frontmatter parsing and serialization system used to embed mdstack metadata in CLAUDE.md files.

**Scope**: Tests frontmatter extraction, merging, and serialization. Covers the mechanism for maintaining mdstack configuration and instructions within CLAUDE.md files while preserving user content.

**Coverage**:
- Parsing: Extracting valid YAML frontmatter from markdown files and handling invalid YAML gracefully
- Building: Creating mdstack-specific frontmatter sections with version information and documentation references
- Merging: Combining existing frontmatter with mdstack sections while preserving user data and existing metadata
- Serialization: Converting frontmatter and body back to markdown format with proper formatting
- Updates: Updating CLAUDE.md files with mdstack metadata while preserving user content and existing sections
- Edge cases: Files without frontmatter, invalid YAML, existing mdstack sections, empty files

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

- **Temporary file systems**: Tests use `tempfile.TemporaryDirectory()` to create isolated file system environments without side effects or pollution of the actual repository
- **In-memory models**: Core data models are tested without I/O, using direct instantiation to verify logic in isolation
- **Fake implementations**: LLM client interactions are tested with a `FakeLLMClient` that captures calls without making actual API requests, enabling fast and reliable testing
- **Explicit assertions**: Tests use clear, specific assertions with descriptive failure messages for easy debugging
- **Parametrized scenarios**: Multiple related test cases cover happy paths, error cases, and edge cases systematically
- **Fixture-based setup**: Common test infrastructure (scopes, manifests, files) is created consistently across tests to reduce duplication
- **Path normalization**: Tests account for platform-specific path handling and use repository-relative paths consistently