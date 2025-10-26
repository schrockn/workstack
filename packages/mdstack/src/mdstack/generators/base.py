from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mdstack.discovery import find_child_scopes
from mdstack.llm.client import LLMClient, LLMResponse
from mdstack.models import Scope
from mdstack.paths import make_scope_relative

# Universal base instructions shared across all generators for optimal cache reuse
UNIVERSAL_BASE_INSTRUCTIONS = """You are a technical documentation expert analyzing \
Python codebases.

Core principles:
- Focus on helping AI agents understand and work with the codebase
- Provide conceptual understanding over implementation details
- Use full repository-relative paths for all file references
- Never use just filenames or partial paths
- Output only markdown content without preamble or explanation

You will be provided with:
1. Context from CLAUDE.md (if available)
2. Source code files and/or test files
3. Child package documentation (if applicable)
4. Specific generation instructions for the document type

Analyze the provided content and generate the requested documentation following the specific \
instructions provided."""


@dataclass
class GenerationResult:
    """Result of document generation."""

    content: str
    llm_response: LLMResponse | None = None


class DocumentGenerator(ABC):
    """Base class for document generators."""

    def __init__(
        self,
        llm_client: LLMClient,
        verbose: bool = False,
        enable_caching: bool = True,
        cache_ttl: str = "5m",
    ):
        self.llm = llm_client
        self.verbose = verbose
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl

    @abstractmethod
    def generate(self, scope: Scope) -> GenerationResult:
        """Generate document content for scope."""
        pass

    @abstractmethod
    def get_filename(self) -> str:
        """Get the output filename (e.g., 'TESTS.md')."""
        pass

    def _load_all_source_files(self, scope: Scope) -> dict[Path, str]:
        """
        Load all Python source files in scope (excluding tests).

        This is used to build Block 2 which is shared across all generators.
        """
        source_files = {}
        for file in scope.path.glob("*.py"):
            if file.is_file() and not file.name.startswith("test_"):
                try:
                    content = file.read_text(encoding="utf-8")
                    source_files[file] = content
                except Exception:
                    continue
        return source_files

    def _load_claude_md(self, scope: Scope) -> str:
        """Load CLAUDE.md if it exists."""
        if scope.claude_md_path.exists():
            return scope.claude_md_path.read_text(encoding="utf-8")
        return ""

    def _load_child_docs(
        self, scope: Scope, all_scopes: list[Scope] | None, doc_filename: str
    ) -> dict[Path, str]:
        """Load child documentation for a specific doc type."""
        child_docs = {}
        if all_scopes:
            children = find_child_scopes(scope, all_scopes)
            for child in children:
                child_doc_file = child.mdstack_dir / doc_filename
                if child_doc_file.exists():
                    child_docs[child.path] = child_doc_file.read_text(encoding="utf-8")
        return child_docs

    def _load_all_child_docs(
        self, scope: Scope, all_scopes: list[Scope] | None
    ) -> dict[str, dict[Path, str]]:
        """
        Load ALL child documentation (LOOKUP, ARCHITECTURE, TESTS) for cache sharing.

        Returns dict mapping doc type to child docs:
        {
            "LOOKUP.md": {child_path: content, ...},
            "OBSERVED_ARCHITECTURE.md": {child_path: content, ...},
            "TESTS.md": {child_path: content, ...}
        }
        """
        all_child_docs = {
            "LOOKUP.md": self._load_child_docs(scope, all_scopes, "LOOKUP.md"),
            "OBSERVED_ARCHITECTURE.md": self._load_child_docs(
                scope, all_scopes, "OBSERVED_ARCHITECTURE.md"
            ),
            "TESTS.md": self._load_child_docs(scope, all_scopes, "TESTS.md"),
        }
        return all_child_docs

    def _build_shared_content_block(
        self,
        scope: Scope,
        claude_md: str,
        source_files: dict[Path, str],
        subpackages: dict[Path, list[Path]],
        all_child_docs: dict[str, dict[Path, str]],
    ) -> str | None:
        """
        Build Block 2: Shared content (identical across all 3 generators).

        Includes:
        - CLAUDE.md
        - Source files and subpackages
        - ALL child documentation (LOOKUP, ARCHITECTURE, TESTS)

        This ensures the block is identical regardless of which generator is running,
        maximizing cache hits.
        """
        shared_content_parts = []

        # Add CLAUDE.md
        if claude_md:
            shared_content_parts.append(f"# Context from CLAUDE.md\n\n{claude_md}")

        # Add source files and subpackages
        if source_files or subpackages:
            source_block = self._format_source_files_block(scope, source_files, subpackages)
            shared_content_parts.append(f"# Source Code\n\n{source_block}")

        # Add ALL child documentation
        for doc_type, child_docs in all_child_docs.items():
            if child_docs:
                children_section = self._format_all_child_docs(scope, child_docs, doc_type)
                shared_content_parts.append(
                    f"# Child Package {doc_type} Documentation\n\n{children_section}"
                )

        return "\n\n".join(shared_content_parts) if shared_content_parts else None

    def _format_all_child_docs(
        self, scope: Scope, child_docs: dict[Path, str], doc_type: str
    ) -> str:
        """Format child docs of a specific type for inclusion in shared block."""
        if not child_docs:
            return ""

        sections = [f"Child Package {doc_type} Documentation:"]
        for child_path, doc_content in child_docs.items():
            # Use scope-relative path for child directories
            relative_child_path = make_scope_relative(child_path, scope.path)
            sections.append(f"\n## {child_path.name} ({relative_child_path})\n{doc_content}")

        return "\n".join(sections)

    def _find_subpackages(self, scope: Scope) -> dict[Path, list[Path]]:
        """
        Find immediate subdirectories containing Python modules.

        Returns dict mapping subdirectory paths to their Python files.
        """
        subpackages = {}
        for item in scope.path.iterdir():
            if not item.is_dir():
                continue
            if item.name.startswith(".") or item.name == "__pycache__":
                continue
            py_files = [f for f in item.glob("*.py") if f.is_file()]
            if py_files:
                subpackages[item] = sorted(py_files)
        return subpackages

    def _format_source_files_block(
        self, scope: Scope, source_files: dict[Path, str], subpackages: dict[Path, list[Path]]
    ) -> str:
        """Format source files and subpackages for Block 2 (shared cache)."""
        sections = []

        # Add Python files
        if source_files:
            sections.append("Python Files in This Directory:")
            for file_path, content in source_files.items():
                # Use scope-relative path for files in the scope
                relative_path = make_scope_relative(file_path, scope.path)
                sections.append(f"\n## {relative_path}\n```python\n{content}\n```")

        # Add subpackages
        if subpackages:
            sections.append("\n\nSubpackages/Subdirectories:")
            for subpkg_path, py_files in subpackages.items():
                module_names = [f.name for f in py_files]
                modules_str = ", ".join(module_names)
                sections.append(f"\n## {subpkg_path.name}/\n**Modules**: {modules_str}")

        return "\n".join(sections)

    def _build_system_blocks(
        self,
        generator_specific_instructions: str,
        shared_content_block: str | None = None,
        generator_specific_content: str | None = None,
    ) -> list[dict[str, Any]] | None:
        """
        Build system message blocks with cache control for optimal reuse.

        Uses 4-block structure (maximum 4 cache_control blocks allowed by Anthropic API):
        - Block 1: Universal base instructions (shared across ALL generators)
        - Block 2: Source files + CLAUDE.md + child docs (shared across all 3 generators in scope)
        - Block 3: Generator-specific content (e.g., test files for TESTS.md)
        - Block 4: Generator-specific instructions

        This structure maximizes cache hits:
        - Within a scope: Blocks 1-2 cache across all 3 generators (~90% reuse)
        - LOOKUP and ARCHITECTURE get cache HIT on Block 2
        - TESTS writes Block 3 (test files), but still gets Block 1-2 cache hits

        Cache invalidation happens naturally: file content changes → different hash → cache miss.

        Args:
            generator_specific_instructions: Instructions specific to this generator type
            shared_content_block: Content shared across all generators (source files, CLAUDE.md)
            generator_specific_content: Content only needed by this generator (e.g., test files)

        Returns:
            List of system message blocks with cache_control, or None if caching disabled
        """
        if not self.enable_caching:
            return None

        blocks = []

        # Block 1: Universal base instructions (cacheable across ALL generators and scopes)
        blocks.append(
            {
                "type": "text",
                "text": UNIVERSAL_BASE_INSTRUCTIONS,
                "cache_control": {"type": "ephemeral"},
            }
        )

        # Block 2: Shared content (source files, CLAUDE.md, child docs)
        # This block is IDENTICAL across all 3 generators in a scope → cache hit!
        if shared_content_block:
            blocks.append(
                {
                    "type": "text",
                    "text": shared_content_block,
                    "cache_control": {"type": "ephemeral"},
                }
            )

        # Block 3: Generator-specific content (optional, e.g., test files for TESTS.md)
        if generator_specific_content:
            blocks.append(
                {
                    "type": "text",
                    "text": generator_specific_content,
                    "cache_control": {"type": "ephemeral"},
                }
            )

        # Block 4: Generator-specific instructions (last block)
        blocks.append(
            {
                "type": "text",
                "text": f"# Document Type Instructions\n\n{generator_specific_instructions}",
                "cache_control": {"type": "ephemeral"},
            }
        )

        return blocks
