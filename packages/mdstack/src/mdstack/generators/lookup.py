from mdstack.generators.base import DocumentGenerator, GenerationResult
from mdstack.models import Scope
from mdstack.paths import find_repo_root, make_scope_relative


class LookupGenerator(DocumentGenerator):
    """Generate LOOKUP.md using LLM semantic analysis."""

    def get_filename(self) -> str:
        return "LOOKUP.md"

    def generate(self, scope: Scope, all_scopes: list[Scope] | None = None) -> GenerationResult:
        """Generate LOOKUP.md for scope."""
        # Load shared content (Block 2) - same for all generators
        source_files = self._load_all_source_files(scope)
        claude_md = self._load_claude_md(scope)
        subpackages = self._find_subpackages(scope)
        all_child_docs = self._load_all_child_docs(scope, all_scopes)

        # Extract LOOKUP-specific child docs for early-exit check and logging
        child_lookup_docs = all_child_docs["LOOKUP.md"]

        # If no Python files and no children, return simple message
        if not source_files and not subpackages and not child_lookup_docs:
            return GenerationResult(
                content="# Semantic Lookup Index\n\nNo Python files found in this scope.\n",
                llm_response=None,
            )

        # Build Block 2: Shared content (identical for TESTS, LOOKUP, ARCHITECTURE)
        shared_content_block = self._build_shared_content_block(
            scope, claude_md, source_files, subpackages, all_child_docs
        )

        # Build system blocks (no generator-specific content for LOOKUP)
        static_instructions = self._get_static_instructions()
        system_blocks = self._build_system_blocks(
            static_instructions,
            shared_content_block=shared_content_block,
            generator_specific_content=None,  # LOOKUP doesn't need Block 3
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
        dynamic_prompt = f"""Generate LOOKUP.md documentation for scope: {scope.path}

Follow the format and guidelines specified in the "Document Type Instructions" section above.
Focus on semantic concepts, search phrases, and mapping natural language to file paths."""

        response = self.llm.generate(
            dynamic_prompt,
            max_tokens=4000,
            context="LOOKUP.md",
            input_files=input_files,
            verbose=self.verbose,
            system_blocks=system_blocks,
        )

        return GenerationResult(content=response.content, llm_response=response)

    def _get_static_instructions(self) -> str:
        """Get generator-specific instructions for LOOKUP.md."""
        return """Document Type: LOOKUP.md

Your task is to analyze code files and generate a searchable index that maps natural language \
concepts to file paths.

For each conceptual area or functionality:
1. Generate natural language search phrases a developer might use
2. Include synonyms and common variations
3. Map to relevant files using scope-relative paths
4. Focus on concepts and capabilities, not implementation details
5. If child packages have lookup documentation, provide references to them for relevant \
concepts

IMPORTANT: Use scope-relative paths (relative to the scope being documented), not full \
repository paths. For example, if documenting the generators/ directory, use "lookup.py" \
instead of "packages/mdstack/src/mdstack/generators/lookup.py".

DO NOT include specific class names or function names unless explicitly necessary for clarity.
Focus on what the code DOES conceptually, not the specific names used.

Output format:
# Semantic Lookup Index

## Child Packages (if applicable)
List child packages with links to their documentation:
- **[child_package_name]** (relative/path): Brief description

## [Concept/Capability]
**Search phrases**: phrase1, phrase2, phrase3, ...
**Files**: file1.py, file2.py (scope-relative paths)
**Child packages**: Relevant child package names if applicable
**Description**: Brief description of this concept"""
