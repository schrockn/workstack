from mdstack.generators.base import DocumentGenerator, GenerationResult
from mdstack.models import Scope
from mdstack.paths import find_repo_root, make_scope_relative


class ArchitectureGenerator(DocumentGenerator):
    """Generate OBSERVED_ARCHITECTURE.md using LLM analysis."""

    def get_filename(self) -> str:
        return "OBSERVED_ARCHITECTURE.md"

    def generate(self, scope: Scope, all_scopes: list[Scope] | None = None) -> GenerationResult:
        """Generate OBSERVED_ARCHITECTURE.md for scope."""
        # Load shared content (Block 2) - same for all generators
        source_files = self._load_all_source_files(scope)
        claude_md = self._load_claude_md(scope)
        subpackages = self._find_subpackages(scope)
        all_child_docs = self._load_all_child_docs(scope, all_scopes)

        # Extract ARCHITECTURE-specific child docs for early-exit check
        child_architecture_docs = all_child_docs["OBSERVED_ARCHITECTURE.md"]

        # If no Python files, no subpackages, and no children, return simple message
        if not source_files and not subpackages and not child_architecture_docs:
            return GenerationResult(
                content="# Observed Architecture\n\nNo Python code found in this scope.\n",
                llm_response=None,
            )

        # Build Block 2: Shared content (identical for TESTS, LOOKUP, ARCHITECTURE)
        shared_content_block = self._build_shared_content_block(
            scope, claude_md, source_files, subpackages, all_child_docs
        )

        # Build system blocks (no generator-specific content for ARCHITECTURE)
        static_instructions = self._get_static_instructions()
        system_blocks = self._build_system_blocks(
            static_instructions,
            shared_content_block=shared_content_block,
            generator_specific_content=None,  # ARCHITECTURE doesn't need Block 3
        )

        # Build list of input files for logging
        # Use scope-relative paths for files within the scope, repo-relative for others
        find_repo_root(scope.path)
        input_files = []

        # CLAUDE.md in scope - use scope-relative
        if scope.claude_md_path.exists():
            input_files.append(make_scope_relative(scope.claude_md_path, scope.path))

        # Source files in scope - use scope-relative
        for py_file in source_files.keys():
            input_files.append(make_scope_relative(py_file, scope.path))

        # Add ALL child docs - these are under scope so use scope-relative
        for doc_type, child_docs in all_child_docs.items():
            for child_path in child_docs.keys():
                doc_file_path = child_path / ".mdstack" / doc_type
                input_files.append(make_scope_relative(doc_file_path, scope.path))

        # Enhanced dynamic prompt
        dynamic_prompt = f"""Generate OBSERVED_ARCHITECTURE.md documentation for scope: {scope.path}

Follow the format and guidelines specified in the "Document Type Instructions" section above.
Focus on architectural patterns, module organization, and how AI agents can understand the code."""

        response = self.llm.generate(
            dynamic_prompt,
            max_tokens=4000,
            context="OBSERVED_ARCHITECTURE.md",
            input_files=input_files,
            verbose=self.verbose,
            system_blocks=system_blocks,
        )

        return GenerationResult(content=response.content, llm_response=response)

    def _get_static_instructions(self) -> str:
        """Get generator-specific instructions for OBSERVED_ARCHITECTURE.md."""
        return """Document Type: OBSERVED_ARCHITECTURE.md

Your task is to analyze code files and generate architectural documentation that helps AI agents \
understand how to work with the codebase.

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
- Use scope-relative paths (relative to the scope being documented), not full repository paths

Output format:
# Observed Architecture

## Overview
[High-level purpose of this scope]

[Include only relevant sections from the list above based on actual content]

For each section you include, follow these patterns:

## Module Organization
### module.py
**Responsibility**: ...
**Key exports**: ...

## Core Abstractions
### ClassName
**Location**: filename.py (scope-relative)
**Purpose**: ...
**Type**: ABC/frozen dataclass/etc.

## Critical Functions
### function_name
**Location**: filename.py (scope-relative)
**Purpose**: ...

[Continue with other relevant sections]"""
