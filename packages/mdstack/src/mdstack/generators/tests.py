from pathlib import Path

from mdstack.generators.base import DocumentGenerator, GenerationResult
from mdstack.models import Scope
from mdstack.package_detection import detect_package_root
from mdstack.paths import find_repo_root, make_repo_relative, make_scope_relative


class TestsGenerator(DocumentGenerator):
    """Generate TESTS.md using LLM analysis."""

    def get_filename(self) -> str:
        return "TESTS.md"

    def generate(self, scope: Scope, all_scopes: list[Scope] | None = None) -> GenerationResult:
        """Generate TESTS.md for scope."""
        # Load shared content (Block 2) - same for all generators
        source_files = self._load_all_source_files(scope)
        claude_md = self._load_claude_md(scope)
        subpackages = self._find_subpackages(scope)
        all_child_docs = self._load_all_child_docs(scope, all_scopes)

        # Extract TESTS-specific child docs for early-exit check
        child_tests_docs = all_child_docs["TESTS.md"]

        # Find test files (Block 3 - specific to TESTS generator)
        test_files = self._find_test_files(scope)
        related_test_files = self._find_related_test_files(scope)
        all_test_files = list(set(test_files + related_test_files))

        # If no test files and no children, return simple message
        if not all_test_files and not child_tests_docs:
            return GenerationResult(
                content="# Tests\n\nNo test files found in this scope.\n",
                llm_response=None,
            )

        # Build Block 2: Shared content (identical for TESTS, LOOKUP, ARCHITECTURE)
        shared_content_block = self._build_shared_content_block(
            scope, claude_md, source_files, subpackages, all_child_docs
        )

        # Build Block 3: Test files (specific to TESTS generator)
        test_content_parts = []

        # Load test file contents
        local_test_contents = {}
        related_test_contents = {}
        for test_file in all_test_files:
            try:
                content = test_file.read_text(encoding="utf-8")
                if test_file in test_files:
                    local_test_contents[test_file] = content
                else:
                    related_test_contents[test_file] = content
            except Exception:
                continue

        if local_test_contents:
            local_section = self._format_files(
                scope, local_test_contents, "Tests in this scope", use_scope_relative=True
            )
            test_content_parts.append(f"# Tests in this scope\n\n{local_section}")

        if related_test_contents:
            related_section = self._format_files(
                scope,
                related_test_contents,
                "Related tests (for code in this scope)",
                use_scope_relative=False,
            )
            test_content_parts.append(f"# Related tests\n\n{related_section}")

        test_specific_content = "\n\n".join(test_content_parts) if test_content_parts else None

        # Build system blocks with test files in Block 3
        static_instructions = self._get_static_instructions()
        system_blocks = self._build_system_blocks(
            static_instructions,
            shared_content_block=shared_content_block,
            generator_specific_content=test_specific_content,  # Block 3: test files
        )

        # Build list of input files for logging
        # Use scope-relative paths for files within the scope, repo-relative for others
        repo_root = find_repo_root(scope.path)
        input_files = []

        # CLAUDE.md in scope - use scope-relative
        if scope.claude_md_path.exists():
            input_files.append(make_scope_relative(scope.claude_md_path, scope.path))

        # Source files in scope - use scope-relative
        for py_file in source_files.keys():
            input_files.append(make_scope_relative(py_file, scope.path))

        # Test files - check if they're under the scope directory
        for test_file in all_test_files:
            try:
                # Try to make it scope-relative (will fail if not under scope)
                test_file.resolve().relative_to(scope.path.resolve())
                input_files.append(make_scope_relative(test_file, scope.path))
            except ValueError:
                # File is outside scope, use repo-relative
                input_files.append(make_repo_relative(test_file, repo_root))

        # Add ALL child docs - these are under scope so use scope-relative
        for doc_type, child_docs in all_child_docs.items():
            for child_path in child_docs.keys():
                doc_file_path = child_path / ".mdstack" / doc_type
                input_files.append(make_scope_relative(doc_file_path, scope.path))

        # Enhanced dynamic prompt
        dynamic_prompt = f"""Generate TESTS.md documentation for scope: {scope.path}

Follow the format and guidelines specified in the "Document Type Instructions" section above.
Focus on test coverage, validation patterns, and the conceptual purpose of test files."""

        response = self.llm.generate(
            dynamic_prompt,
            max_tokens=4000,
            context="TESTS.md",
            input_files=input_files,
            verbose=self.verbose,
            system_blocks=system_blocks,
        )

        return GenerationResult(content=response.content, llm_response=response)

    def _find_test_files(self, scope: Scope) -> list[Path]:
        """
        Find test files in immediate scope directory only.

        Relies on child scopes' .mdstack files for subdirectory content.
        """
        test_files = []
        path = scope.path

        # Look for test_*.py files
        for file in path.glob("test_*.py"):
            if file.is_file():
                test_files.append(file)

        # Look for *_test.py files
        for file in path.glob("*_test.py"):
            if file.is_file() and file not in test_files:
                test_files.append(file)

        return sorted(test_files)

    def _find_related_test_files(self, scope: Scope) -> list[Path]:
        """
        Find test files that exercise code in this scope.

        For source code scopes (containing /src/), looks for corresponding
        test files in a sibling tests/ directory following naming conventions:
        - src/package/module.py → tests/test_module.py

        Returns empty list if scope is a package root, since all tests are
        already found via _find_test_files().
        """
        # Don't search for related tests if this is a package root
        package_layout = detect_package_root(scope.path)
        if package_layout:
            return []

        # Only search for related tests if this is a source code scope
        if "/src/" not in str(scope.path):
            return []

        # Find source files in this scope
        source_files = [f for f in scope.path.glob("*.py") if f.is_file()]
        if not source_files:
            return []

        # Navigate up to find package root and tests directory
        # From src/mdstack → src → packages/mdstack
        try:
            # Try to find tests/ directory at package level
            current = scope.path
            tests_dir = None

            # Walk up the directory tree looking for tests/
            while current != current.parent:
                potential_tests = current.parent / "tests"
                if potential_tests.exists() and potential_tests.is_dir():
                    tests_dir = potential_tests
                    break
                current = current.parent

            if not tests_dir:
                return []

        except Exception:
            return []

        # Match test files by convention
        test_files = []
        for src_file in source_files:
            if src_file.name == "__init__.py":
                continue

            # module.py → test_module.py
            test_name = f"test_{src_file.stem}.py"
            test_path = tests_dir / test_name

            if test_path.exists():
                test_files.append(test_path)

        return sorted(test_files)

    def _get_static_instructions(self) -> str:
        """Get generator-specific instructions for TESTS.md."""
        return """Document Type: TESTS.md

Your task is to analyze test files and generate comprehensive documentation about test coverage.

Create a markdown document that describes:
1. The overall purpose of each test file (what functionality it validates)
2. The scope of testing (integration vs unit, what components are tested)
3. General test coverage areas (happy path, error cases, edge cases)
4. Any notable patterns or approaches used in the tests
5. If child packages have test documentation, provide a brief summary referencing them
6. For related test files (found in ../tests/), explain which modules in the scope they \
exercise

DO NOT list individual test function names or get too specific about implementation details.
Focus on the conceptual purpose and scope of each test file.

IMPORTANT: For test files in the scope, use scope-relative paths. For related test files \
outside the scope, repository-relative paths are provided for clarity.

Output format:
# Tests

## Child Packages (if applicable)
Briefly list child packages and their test coverage:
- **[child_package_name]**: Brief summary

## Tests in This Scope

### test_example.py (scope-relative)
**Purpose**: High-level description of what this file tests
**Scope**: What components/functionality this covers
**Coverage**: General areas covered (happy path, errors, etc.)

## Related Tests (if applicable)
Tests for code artifacts in this scope, located in a separate tests/ directory.

### packages/mdstack/tests/test_example.py (repo-relative for context)
**Exercises**: Which module(s) in this scope it tests (e.g., discovery.py, manifest.py)
**Purpose**: High-level description of what this file tests
**Scope**: What components/functionality this covers
**Coverage**: General areas covered (happy path, errors, etc.)"""

    def _format_files(
        self,
        scope: Scope,
        file_contents: dict[Path, str],
        section_header: str = "Test Files",
        use_scope_relative: bool = True,
    ) -> str:
        """
        Format file contents for prompt.

        Args:
            scope: The scope being documented
            file_contents: Dictionary of file paths to their contents
            section_header: Header for this section
            use_scope_relative: If True, use scope-relative paths. If False, use
                              repo-relative paths. Set to False for test files outside
                              the scope (e.g., in ../tests/)
        """
        if not file_contents:
            return ""

        sections = [f"{section_header}:"]

        for file_path, content in file_contents.items():
            if use_scope_relative:
                # Use scope-relative path for files in the scope
                relative_path = make_scope_relative(file_path, scope.path)
            else:
                # Use repo-relative path for files outside the scope
                repo_root = find_repo_root(file_path)
                relative_path = make_repo_relative(file_path, repo_root)

            file_section = f"\n## {relative_path}\n```python\n{content}\n```"
            sections.append(file_section)

        return "\n".join(sections)
