# Fix Architecture Generator Caching Issue

## Problem Statement

The architecture generator's `_get_static_instructions()` method generates **unique instructions for every scope**, preventing cache reuse across generations. This happens because:

1. **Dynamic concept extraction**: The `_extract_concepts()` method analyzes file content and embeds discovered concepts directly into the instructions
2. **Conditional sections**: Instructions change based on whether subpackages or child docs exist
3. **Dynamic formatting**: The instruction template itself varies per scope

Result: Every generation gets different Block 3 (generator instructions), causing cache misses and increased costs.

## Root Cause Analysis

Cache blocks are structured as:

- **Block 1**: Universal base instructions (shared by all generators)
- **Block 2**: Content (files, CLAUDE.md, child docs) - _expected to vary_
- **Block 3**: Generator-specific instructions - _should be static but isn't_

Current behavior:

- First TESTS.md generation: Cache WRITE (all blocks)
- First LOOKUP.md generation: Cache HIT Block 1, Cache WRITE Blocks 2-3
- First OBSERVED_ARCHITECTURE.md generation: Cache WRITE all blocks (wrong!)

Expected behavior with fix:

- First TESTS.md generation: Cache WRITE (all blocks)
- First LOOKUP.md generation: Cache HIT Block 1, Cache WRITE Blocks 2-3
- First OBSERVED_ARCHITECTURE.md generation: Cache HIT Blocks 1-2, Cache WRITE Block 3 only

## Implementation Plan

### 1. Remove Dynamic Concept Extraction

**Delete the `_extract_concepts` method entirely** (lines 302-321 in architecture.py)

- This method scans file content looking for keywords to determine "concepts"
- This analysis should be done by the LLM, not pre-computed
- Prevents instructions from being truly static

### 2. Make `_get_static_instructions` Truly Static

**Remove all parameters** from the method signature:

- Current: `_get_static_instructions(self, file_contents, subpackages, child_architecture_docs)`
- New: `_get_static_instructions(self)`

**Remove all conditional logic** from instruction generation:

- No `has_subpackages` checks
- No `has_children` checks
- No `concepts` extraction

### 3. Update Generator Instructions (EXACT TEXT)

Replace the current dynamic instruction template with this EXACT static text:

```markdown
Document Type: OBSERVED_ARCHITECTURE.md

Your task is to analyze code files and generate architectural documentation that helps AI agents understand how to work with the codebase.

Create comprehensive architectural documentation covering:

1. **Module Organization** - Describe the purpose and responsibility of each Python module
2. **Subpackages** - If subdirectories with Python files exist, describe their organization
3. **Core Abstractions** - Key classes, their purposes, and relationships
4. **Critical Functions** - Essential functions that are central to the architecture
5. **Architectural Patterns** - Design patterns, coding conventions, and structural choices
6. **Data Flow** - How data moves through the components
7. **Dependencies** - Import relationships and external dependencies
8. **Extension Points** - Where and how to add new features
9. **Child Packages** - If child scope documentation exists, reference and integrate it
10. **Key Concepts Explained** - Important domain concepts or technical terms that need explanation
11. **Common Agent Tasks** - How an AI agent would typically modify or extend this code

IMPORTANT INSTRUCTIONS:

- Only include sections that are relevant based on the provided content
- Skip sections if the corresponding content doesn't exist (e.g., skip "Subpackages" if none exist)
- Determine key concepts by analyzing the code semantics, not by keyword matching
- DO NOT list every single method or function - focus on architecture, patterns, and navigation
- Focus on helping an LLM understand how to work with this code, add features, or debug issues

Output format:

# Observed Architecture

## Overview

[High-level purpose of this scope]

[Include only relevant sections from the list above based on actual content]

For each section you include, follow these patterns:

## Module Organization

### packages/mdstack/src/mdstack/module.py

**Responsibility**: ...
**Key exports**: ...

## Core Abstractions

### ClassName

**Location**: packages/mdstack/src/mdstack/filename.py
**Purpose**: ...
**Type**: ABC/frozen dataclass/etc.

## Critical Functions

### function_name

**Location**: packages/mdstack/src/mdstack/filename.py
**Purpose**: ...

[Continue with other relevant sections]
```

### 4. Update the `generate` Method

**Remove dynamic parameters** when calling `_get_static_instructions`:

- Current: `static_instructions = self._get_static_instructions(file_contents, subpackages, child_architecture_docs)` (line 73-74)
- New: `static_instructions = self._get_static_instructions()`

### 5. Verification Steps

After implementation:

1. Run `uv run mdstack generate` on a multi-scope project
2. Check logs for cache behavior:
   - First scope: All blocks show "Cache WRITE"
   - Second scope with same generator: Blocks 1 & 3 show "Cache HIT", Block 2 shows "Cache WRITE"
   - Third scope: Same pattern continues
3. Verify that generated OBSERVED_ARCHITECTURE.md files still contain appropriate sections
4. Confirm the LLM correctly identifies concepts without explicit extraction

## Expected Outcomes

### Performance Improvements

- **Cache hit rate**: From ~33% to ~66% for blocks across generators within a scope
- **Cost reduction**: ~40-50% reduction in API costs for multi-scope generation
- **Speed**: Faster generation due to cached content reuse

### Quality Maintenance

- Generated documentation quality remains unchanged
- LLM determines relevant sections from actual content
- More flexible - LLM can identify concepts we didn't anticipate

## Implementation Sequence

1. Delete `_extract_concepts` method
2. Update `_get_static_instructions` signature and body
3. Update `generate` method to call without parameters
4. Test with single scope first
5. Test with multi-scope project
6. Verify cache hits in logs
7. Review generated documentation quality

## Risk Mitigation

- **Risk**: LLM might include irrelevant sections
  - **Mitigation**: Clear instructions to "only include sections that are relevant"

- **Risk**: Missing important concepts without extraction
  - **Mitigation**: LLM is better at semantic analysis than keyword matching

- **Risk**: Inconsistent section inclusion across runs
  - **Mitigation**: Strong instruction guidance on when to include each section
