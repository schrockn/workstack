# Tests

## Related Tests

Tests for code in this scope are located in `packages/mdstack/tests/`.

### packages/mdstack/tests/test_validation.py
**Exercises**: `validation.py`
**Purpose**: Validates the tampering detection system that ensures generated documentation files haven't been manually edited
**Scope**: Tests the integrity checking mechanism that compares file hashes against stored manifest hashes
**Coverage**: 
- Happy path: Files matching manifest hashes pass validation
- Error cases: Detection of manual edits in TESTS.md, LOOKUP.md, and OBSERVED_ARCHITECTURE.md
- Batch operations: Checking multiple scopes and collecting tampered results

### packages/mdstack/tests/test_models.py
**Exercises**: `models.py`
**Purpose**: Validates the core data structures (Scope and Manifest) used throughout the system
**Scope**: Tests frozen dataclass creation, factory methods, and validation logic
**Coverage**:
- Happy path: Creating valid Scope and Manifest instances
- Error cases: Validation failures when required paths don't exist
- Factory methods: Proper initialization with default values (e.g., generated_at timestamp)

### packages/mdstack/tests/test_package_detection.py
**Exercises**: `package_detection.py`
**Purpose**: Validates Python package detection and layout discovery from pyproject.toml configuration
**Scope**: Tests package root detection, source/test directory discovery, and configuration parsing
**Coverage**:
- Happy path: Detecting packages with properly configured pyproject.toml
- Configuration parsing: Extracting source and test directories from TOML
- Defaults: Fallback to src/ and tests/ when not explicitly configured
- Edge cases: Missing pyproject.toml, non-existent directories, multiple source directories, only source or only test directories existing

### packages/mdstack/tests/test_manifest.py
**Exercises**: `manifest.py`
**Purpose**: Validates manifest persistence and staleness detection for generated documentation
**Scope**: Tests manifest serialization, loading, and cache invalidation logic
**Coverage**:
- Happy path: Saving and loading manifests with all metadata preserved
- Staleness detection: Identifying when documentation needs regeneration (no manifest, missing files)
- Backward compatibility: Handling manifests missing architecture_hash field

### packages/mdstack/tests/test_discovery.py
**Exercises**: `discovery.py`
**Purpose**: Validates scope discovery and hierarchy building from CLAUDE.md files
**Scope**: Tests recursive file discovery, parent-child relationship establishment, and scope lookup
**Coverage**:
- Happy path: Finding all CLAUDE.md files in directory tree
- Hierarchy: Correctly identifying parent scopes and establishing relationships
- Lookup: Finding the most specific scope for a given file path
- Edge cases: Multiple nesting levels, sibling scopes

### packages/mdstack/tests/test_frontmatter.py
**Exercises**: `frontmatter.py`
**Purpose**: Validates YAML frontmatter parsing, merging, and serialization for CLAUDE.md files
**Scope**: Tests frontmatter extraction, mdstack metadata injection, and content preservation
**Coverage**:
- Parsing: Valid YAML frontmatter extraction, handling missing frontmatter, invalid YAML gracefully
- Building: Creating mdstack frontmatter with correct structure and instructions
- Merging: Preserving existing frontmatter while updating mdstack section
- Serialization: Converting frontmatter and body back to markdown format
- Updates: Updating CLAUDE.md with frontmatter while preserving user content and existing metadata

### packages/mdstack/tests/test_hashing.py
**Exercises**: `hashing.py`
**Purpose**: Validates content hashing utilities used for change detection and tampering verification
**Scope**: Tests hash computation and combination for integrity checking
**Coverage**:
- Determinism: Same content produces same hash
- Differentiation: Different content produces different hashes
- Combination: Multiple contents can be hashed together consistently