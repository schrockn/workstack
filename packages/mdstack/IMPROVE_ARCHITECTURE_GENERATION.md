# Implementation Plan: Improve OBSERVED_ARCHITECTURE.md Generation

## Overview

Enhance the architecture documentation generator to create more useful, task-oriented documentation that helps AI agents understand and navigate codebases more efficiently.

## Current State Analysis

### What Works Well

- Module inventory with responsibilities
- Subpackage discovery and listing
- Extension points documentation
- Data flow descriptions
- Dependency mapping

### Key Gaps

1. **No semantic Q&A** - Doesn't answer "How does X work?" questions
2. **Limited child scope integration** - Child architectures are included but not well-referenced
3. **No cross-package relationships** - Missing inter-package dependencies
4. **No task guidance** - Missing "To do X, start here" instructions
5. **Empty files for test-only scopes** - Generates unhelpful "No Python code" messages

## Implementation Changes

### File: `packages/mdstack/src/mdstack/generators/architecture.py`

#### 1. Enhanced Prompt Sections (Update `_build_prompt` method)

##### A. Add New Section 9: Child Packages

```python
# After line 258, add to prompt:
"""
9. **Child Packages** (if any exist):
   - Summary of each child scope's architecture
   - When to work at parent vs child level
   - How child packages relate to this scope
   - Cross-references to child OBSERVED_ARCHITECTURE.md files
"""
```

**Implementation Notes:**

- Only include if `child_architecture_docs` is not empty
- Summarize key responsibilities from each child
- Indicate delegation patterns

##### B. Add New Section 10: Cross-Package Relationships

```python
"""
10. **Cross-Package Relationships** (if multi-package repository):
    - How this package interacts with sibling packages
    - Shared interfaces and contracts
    - Data flow across package boundaries
    - Import relationships with other packages
"""
```

**Implementation Notes:**

- Detect multi-package repos via multiple pyproject.toml files
- Analyze imports to find cross-package dependencies
- Document API boundaries

##### C. Add New Section 11: Key Concepts Explained

```python
"""
11. **Key Concepts Explained**:
    Answer common semantic questions about this scope:

    ### How does [concept] work?
    For each major concept in this scope, explain:
    - The mechanism/algorithm
    - Key files involved
    - Data flow

    Examples:
    - "How does caching work?" → "Hash-based using manifest.py..."
    - "How does validation work?" → "Tampering detection via SHA256..."
    - "How does generation work?" → "Bottom-up traversal..."
"""
```

**Implementation Notes:**

- Extract concepts from code patterns
- Focus on non-obvious architectural decisions
- Include performance characteristics

##### D. Add New Section 12: Common Agent Tasks

```python
"""
12. **Common Agent Tasks** (include only if clear patterns exist):
    Task-oriented navigation guide:

    ### To add a new [feature type]
    **Start here**: [specific file]
    **Steps**:
    1. [First action with file reference]
    2. [Second action with file reference]
    **Example**: [Reference to existing implementation]

    ### To debug [issue type]
    **Check first**: [specific file/function]
    **Then check**: [fallback locations]
    **Common causes**: [list of typical issues]
"""
```

**Implementation Notes:**

- Only include if there are repeatable patterns
- Must be specific with file references
- Include anti-patterns to avoid

#### 2. Update Existing Sections

##### Module Organization Enhancement

```python
# Update line ~172:
"""
1. **Module Organization**:
   - Responsibility of each module in this directory
   - Key exports and public API
   - Entry points vs internal modules
   - Module dependencies within scope
"""
```

##### Dependencies Enhancement

```python
# Update line ~197:
"""
7. **Dependencies**:
   - Internal: What imports what within this scope
   - External: Third-party package dependencies
   - Cross-package: Dependencies on other packages in repo
   - Circular dependencies (if any) and how they're resolved
"""
```

##### Extension Points Enhancement

```python
# Update line ~202:
"""
8. **Extension Points**:
   - Where to add new features (with specific examples)
   - Step-by-step instructions for common extensions
   - Which patterns to follow (with code references)
   - Anti-patterns to avoid
   - Existing examples to follow
"""
```

#### 3. Improve Child Architecture Integration

##### Update `_format_child_docs` method (line 267)

```python
def _format_child_docs(self, child_architecture_docs: dict[Path, str]) -> str:
    """Format child OBSERVED_ARCHITECTURE.md documents for context."""
    if not child_architecture_docs:
        return ""

    sections = ["Child Package Architecture (for reference and integration):"]
    for child_path, arch_content in child_architecture_docs.items():
        # Extract key sections instead of truncating
        # Parse ## Overview, ## Module Organization, ## Core Abstractions
        overview = self._extract_section(arch_content, "## Overview")
        modules = self._extract_section(arch_content, "## Module Organization")

        sections.append(f"""
## {child_path.name} (child scope)
Path: {child_path}
{overview}

Key Modules:
{modules[:500]}  # Truncate module list if needed

Full details: .mdstack/OBSERVED_ARCHITECTURE.md in {child_path}
""")

    return "\n".join(sections)
```

#### 4. Skip Empty Architecture Files

##### Update generation logic (line 36)

```python
# Instead of "No Python code found", check if it's a test directory
if not python_files and not subpackages and not child_architecture_docs:
    # Check if this is a test-only directory
    test_files = list(scope.path.glob("test_*.py"))
    if test_files:
        # Generate test architecture instead
        return self._generate_test_architecture(scope, test_files)
    else:
        # Skip generation entirely
        return GenerationResult(
            content=None,  # Signal to skip file creation
            llm_response=None,
        )
```

#### 5. Add Helper Methods

##### Add concept extraction helper

```python
def _extract_concepts(self, file_contents: dict[Path, str]) -> list[str]:
    """Extract key concepts that need explanation."""
    concepts = []

    # Look for patterns suggesting important concepts
    patterns = {
        'caching': ['cache', 'memoize', 'store'],
        'validation': ['validate', 'check', 'verify'],
        'generation': ['generate', 'create', 'build'],
        'discovery': ['find', 'discover', 'detect'],
        'propagation': ['propagate', 'bubble', 'cascade'],
    }

    for concept, keywords in patterns.items():
        for content in file_contents.values():
            if any(kw in content.lower() for kw in keywords):
                concepts.append(concept)
                break

    return concepts
```

##### Add section extraction helper

```python
def _extract_section(self, content: str, heading: str) -> str:
    """Extract a section from markdown content."""
    lines = content.split('\n')
    start_idx = None

    for i, line in enumerate(lines):
        if line.strip() == heading:
            start_idx = i + 1
            break

    if start_idx is None:
        return ""

    # Find next section of same level
    heading_level = heading.count('#')
    end_idx = len(lines)

    for i in range(start_idx, len(lines)):
        if lines[i].startswith('#' * heading_level) and not lines[i].startswith('#' * (heading_level + 1)):
            end_idx = i
            break

    return '\n'.join(lines[start_idx:end_idx]).strip()
```

### 6. Update Prompt Template

```python
def _build_prompt(self, ...):
    # Extract concepts for explanation
    concepts = self._extract_concepts(file_contents)

    # Build conditional sections
    child_section = "Include Child Packages section" if child_architecture_docs else ""
    cross_pkg_section = "Include Cross-Package section" if self._is_multi_package() else ""
    tasks_section = "Include Common Tasks section" if self._has_clear_patterns() else ""
    concepts_section = f"Explain these concepts: {', '.join(concepts)}" if concepts else ""

    # Update prompt with conditional sections...
```

## Testing Strategy

### 1. Unit Tests

- Test concept extraction
- Test section parsing
- Test conditional section inclusion

### 2. Integration Tests

- Generate architecture for various scope types
- Verify child scope integration
- Check empty file handling

### 3. Manual Validation

- Generate docs for mdstack itself
- Review with team for completeness
- Test with AI agents for usability

## Success Metrics

1. **Token Reduction**
   - Measure tokens used before/after for common tasks
   - Target: 30-50% reduction for architecture questions

2. **Task Completion Time**
   - Time to complete "add new feature" tasks
   - Target: 2x faster navigation to correct files

3. **Agent Satisfaction**
   - Fewer searches needed
   - Direct answers to "how does X work?"
   - Clear task guidance

## Rollout Plan

### Phase 1: Core Enhancements

- Add Key Concepts section
- Improve child scope integration
- Enhance existing sections

### Phase 2: Task Guidance

- Add Common Agent Tasks section
- Create task templates
- Document patterns

### Phase 3: Cross-Package

- Add cross-package relationships
- Document API boundaries
- Map inter-package dependencies

## Risk Mitigation

1. **Prompt Size**: Monitor token usage, truncate if needed
2. **Quality**: Review generated docs for accuracy
3. **Performance**: Cache aggressively, skip empty scopes
4. **Maintenance**: Auto-regenerate on significant changes

## Example Output

### Before

```markdown
# Observed Architecture

No Python code found in this scope.
```

### After

```markdown
# Observed Architecture

## Overview

Test suite for mdstack validation module...

## Test Organization

- Unit tests for hash computation
- Integration tests for tampering detection
- Fixtures for test data setup

## Test Patterns

- Parametrized tests for multiple scenarios
- Temporary directories for file operations
- Mock LLM client for generation tests

## Coverage Areas

- validation.py: 95% coverage
- hashing.py: 100% coverage
- manifest.py: 88% coverage

## Common Agent Tasks

### To add validation tests

**Start here**: test_validation.py
**Pattern**: Create temp files, compute hashes, verify detection
**Example**: See test_validate_no_tampering_multi_scope

### To debug test failures

**Check first**: Fixture setup in conftest.py
**Then check**: Temp directory permissions
**Common cause**: File system race conditions
```

## Notes

- Consider making prompts configurable via YAML
- Could add user-defined sections via frontmatter
- Might want to version the prompt format
- Consider different prompts for different scope types
