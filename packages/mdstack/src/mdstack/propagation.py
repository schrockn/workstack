import logging
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from mdstack.frontmatter import update_claude_md_frontmatter
from mdstack.generators.architecture import ArchitectureGenerator
from mdstack.generators.lookup import LookupGenerator
from mdstack.generators.tests import TestsGenerator
from mdstack.hashing import compute_combined_hash, compute_hash
from mdstack.llm.client import LLMClient
from mdstack.manifest import load_manifest, save_manifest
from mdstack.models import Manifest, Scope
from mdstack.paths import find_repo_root

logger = logging.getLogger(__name__)

VERSION = "0.1.0"  # mdstack version


@dataclass
class GenerationStats:
    """Aggregate statistics for documentation generation."""

    total_scopes: int = 0
    scopes_generated: int = 0
    scopes_skipped: int = 0
    total_files: int = 0
    total_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_read_tokens: int = 0
    total_cache_write_tokens: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_cost: float = 0.0
    total_duration: float = 0.0
    file_stats: list[dict[str, str | int | float]] = field(default_factory=list)

    def add_file(
        self,
        scope_path: str,
        filename: str,
        tokens: int,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
    ) -> None:
        """Add statistics for a single generated file."""
        self.total_files += 1
        self.total_tokens += tokens
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cache_read_tokens += cache_read_tokens
        self.total_cache_write_tokens += cache_write_tokens
        self.total_cost += cost

        # Track cache hits/misses
        if cache_read_tokens > 0:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        self.file_stats.append(
            {
                "scope": scope_path,
                "file": filename,
                "tokens": tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_tokens": cache_read_tokens,
                "cache_write_tokens": cache_write_tokens,
                "cost": cost,
            }
        )


def log_generation_summary(stats: GenerationStats, total_duration: float) -> None:
    """Log summary of documentation generation."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 GENERATION SUMMARY")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Scopes processed: {stats.total_scopes}")
    logger.info(f"  • Generated: {stats.scopes_generated}")
    logger.info(f"  • Skipped (no changes): {stats.scopes_skipped}")
    logger.info("")
    logger.info(f"Files generated: {stats.total_files}")
    logger.info("")
    logger.info("Token usage:")
    logger.info(f"  • Input tokens: {stats.total_input_tokens:,}")
    logger.info(f"  • Output tokens: {stats.total_output_tokens:,}")
    logger.info(f"  • Total tokens: {stats.total_tokens:,}")
    logger.info("")

    # Cache statistics
    if stats.total_cache_read_tokens > 0 or stats.total_cache_write_tokens > 0:
        logger.info("Cache performance:")
        logger.info(f"  • Cache hits: {stats.cache_hits}/{stats.total_files}")

        if stats.cache_hits > 0:
            hit_rate = int(stats.cache_hits / stats.total_files * 100)
            logger.info(f"  • Hit rate: {hit_rate}%")

        if stats.total_cache_read_tokens > 0:
            logger.info(f"  • Tokens read from cache: {stats.total_cache_read_tokens:,}")
            total_potential_input = stats.total_input_tokens + stats.total_cache_read_tokens
            if total_potential_input > 0:
                savings_pct = int(stats.total_cache_read_tokens / total_potential_input * 100)
                logger.info(f"  • Cache savings: {savings_pct}% of input tokens")

        if stats.total_cache_write_tokens > 0:
            logger.info(f"  • Tokens written to cache: {stats.total_cache_write_tokens:,}")

        logger.info("")

    logger.info(f"Cost: ${stats.total_cost:.4f}")
    logger.info("")
    logger.info(f"Total time: {total_duration:.2f}s")
    logger.info("")
    logger.info("=" * 80)


def _check_prettier_available() -> bool:
    """Check if prettier command is available."""
    return shutil.which("prettier") is not None


def _run_prettier_formatting(repo_root: Path) -> None:
    """
    Run prettier to format all markdown files.

    If prettier is not available, logs an info message but does not fail.
    If prettier fails, logs a warning but does not fail.
    """
    if not _check_prettier_available():
        logger.info("")
        logger.info("ℹ️  Prettier not found. Install prettier to auto-format markdown files.")
        logger.info("   Run: npm install -g prettier")
        return

    logger.info("")
    logger.info("🎨 Running prettier to format markdown files...")

    try:
        result = subprocess.run(
            ["prettier", "--write", "**/*.md", "--ignore-path", ".gitignore"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info("✅ Markdown files formatted with prettier")
        else:
            logger.warning(f"⚠️  Prettier finished with warnings or errors: {result.stderr}")
    except Exception as e:
        logger.warning(f"⚠️  Failed to run prettier: {e}")


def ensure_scope_files(scope: Scope) -> None:
    """
    Ensure CLAUDE.md and AGENTS.md exist with proper frontmatter.

    Creates CLAUDE.md with mdstack frontmatter if it doesn't exist.
    Updates frontmatter in existing CLAUDE.md, preserving user content.
    Creates AGENTS.md as a symlink to CLAUDE.md.
    """
    claude_md = scope.claude_md_path
    agents_md = scope.path / "AGENTS.md"

    # Create or update CLAUDE.md with frontmatter
    if not claude_md.exists():
        # Create new CLAUDE.md with frontmatter only (no user content)
        initial_content = "\n# AI Agent Instructions\n\n"
        updated_content = update_claude_md_frontmatter(initial_content, version=VERSION)
        claude_md.write_text(updated_content, encoding="utf-8")
        logger.info(f"Created CLAUDE.md with mdstack frontmatter at {scope.path}")
    else:
        # Update existing CLAUDE.md frontmatter, preserve user content
        existing_content = claude_md.read_text(encoding="utf-8")
        updated_content = update_claude_md_frontmatter(existing_content, version=VERSION)

        # Only write if content changed (avoid unnecessary file modifications)
        if updated_content != existing_content:
            claude_md.write_text(updated_content, encoding="utf-8")
            logger.info(f"  Updated mdstack frontmatter in CLAUDE.md at {scope.path}")

    # Create AGENTS.md symlink if it doesn't exist
    if not agents_md.exists():
        agents_md.symlink_to("CLAUDE.md")
        logger.info(f"Created AGENTS.md symlink at {scope.path}")


def propagate_generate(
    scope: Scope,
    llm_client: LLMClient,
    visited: set[str] | None = None,
    config=None,
) -> None:
    """
    Generate documentation for scope and propagate to parent if changed.

    Uses hierarchical propagation: only updates parent if this scope changed.

    Args:
        scope: Scope to generate documentation for
        llm_client: LLM client for generation
        visited: Set of already visited scope paths
        config: LLM configuration
    """
    if visited is None:
        visited = set()

    scope_key = str(scope.path.resolve())

    if scope_key in visited:
        logger.debug(f"Already visited {scope.path}, skipping")
        return

    visited.add(scope_key)

    logger.info(f"🤖 Generating md for {scope.path}")
    logger.info("")
    start_time = time.time()

    # Load existing manifest
    old_manifest = load_manifest(scope)

    # Generate new documentation with per-file-type models
    from mdstack.llm.config import create_llm_client

    # If config is provided, create specialized clients for each file type
    if config:
        tests_client = create_llm_client(config, "tests")
        lookup_client = create_llm_client(config, "lookup")
        architecture_client = create_llm_client(config, "architecture")

        verbose = getattr(config, "verbose", False)
        enable_caching = getattr(config, "enable_caching", True)
        cache_ttl = getattr(config, "cache_ttl", "5m")
        tests_gen = TestsGenerator(
            tests_client,
            verbose=verbose,
            enable_caching=enable_caching,
            cache_ttl=cache_ttl,
        )
        lookup_gen = LookupGenerator(
            lookup_client,
            verbose=verbose,
            enable_caching=enable_caching,
            cache_ttl=cache_ttl,
        )
        architecture_gen = ArchitectureGenerator(
            architecture_client,
            verbose=verbose,
            enable_caching=enable_caching,
            cache_ttl=cache_ttl,
        )
    else:
        # Fallback to using same client for all (original behavior)
        verbose = getattr(config, "verbose", False) if config else False
        tests_gen = TestsGenerator(llm_client, verbose=verbose)
        lookup_gen = LookupGenerator(llm_client, verbose=verbose)
        architecture_gen = ArchitectureGenerator(llm_client, verbose=verbose)

    tests_result = tests_gen.generate(scope)
    lookup_result = lookup_gen.generate(scope)
    architecture_result = architecture_gen.generate(scope)

    # Extract content
    tests_md = tests_result.content
    lookup_md = lookup_result.content
    architecture_md = architecture_result.content

    # Compute hashes
    tests_hash = compute_hash(tests_md)
    lookup_hash = compute_hash(lookup_md)
    architecture_hash = compute_hash(architecture_md)
    combined_hash = compute_combined_hash(tests_md, lookup_md, architecture_md)

    # Check if anything changed
    if old_manifest and old_manifest.content_hash == combined_hash:
        logger.info(f"⏭️  No changes for {scope.path}, stopping propagation")
        return

    # Ensure CLAUDE.md and AGENTS.md exist
    ensure_scope_files(scope)

    # Write files
    scope.mdstack_dir.mkdir(parents=True, exist_ok=True)

    (scope.mdstack_dir / "TESTS.md").write_text(tests_md, encoding="utf-8")
    (scope.mdstack_dir / "LOOKUP.md").write_text(lookup_md, encoding="utf-8")
    (scope.mdstack_dir / "OBSERVED_ARCHITECTURE.md").write_text(architecture_md, encoding="utf-8")

    # Save manifest
    new_manifest = Manifest.create(
        content_hash=combined_hash,
        llm_provider="anthropic",
        llm_model=llm_client.get_model_name(),
        generator_version=VERSION,
        tests_hash=tests_hash,
        lookup_hash=lookup_hash,
        architecture_hash=architecture_hash,
    )

    save_manifest(scope, new_manifest)

    total_duration = time.time() - start_time
    logger.info("")
    logger.info(f"✅ Generated md for {scope.path} (Total: {total_duration:.2f}s)")
    logger.info("")

    # Propagate to parent
    if scope.parent_scope:
        logger.debug(f"Propagating to parent: {scope.parent_scope.path}")
        propagate_generate(scope.parent_scope, llm_client, visited, config)
    else:
        logger.debug("No parent scope, propagation complete")


def generate_bottom_up(scopes: list[Scope], llm_client: LLMClient, config=None) -> None:
    """
    Generate documentation for all scopes in bottom-up order.

    Processes leaf scopes first, then works up to root scopes.
    This ensures parent scopes can include child .mdstack content.
    """
    # Initialize statistics tracking
    stats = GenerationStats()
    stats.total_scopes = len(scopes)
    overall_start_time = time.time()

    # Sort scopes by depth (deepest first = leaf nodes first)
    scopes_by_depth = sorted(scopes, key=lambda s: len(s.path.parts), reverse=True)

    for scope in scopes_by_depth:
        logger.info(f"🤖 Generating md for {scope.path}")
        logger.info("")
        start_time = time.time()

        # Load existing manifest
        old_manifest = load_manifest(scope)

        # Generate new documentation with per-file-type models
        from mdstack.llm.config import create_llm_client

        # If config is provided, create specialized clients for each file type
        if config:
            tests_client = create_llm_client(config, "tests")
            lookup_client = create_llm_client(config, "lookup")
            architecture_client = create_llm_client(config, "architecture")

            verbose = getattr(config, "verbose", False)
            enable_caching = getattr(config, "enable_caching", True)
            cache_ttl = getattr(config, "cache_ttl", "5m")
            tests_gen = TestsGenerator(
                tests_client,
                verbose=verbose,
                enable_caching=enable_caching,
                cache_ttl=cache_ttl,
            )
            lookup_gen = LookupGenerator(
                lookup_client,
                verbose=verbose,
                enable_caching=enable_caching,
                cache_ttl=cache_ttl,
            )
            architecture_gen = ArchitectureGenerator(
                architecture_client,
                verbose=verbose,
                enable_caching=enable_caching,
                cache_ttl=cache_ttl,
            )
        else:
            # Fallback to using same client for all (original behavior)
            verbose = getattr(config, "verbose", False) if config else False
            tests_gen = TestsGenerator(llm_client, verbose=verbose)
            lookup_gen = LookupGenerator(llm_client, verbose=verbose)
            architecture_gen = ArchitectureGenerator(llm_client, verbose=verbose)

        # Pass all scopes so generators can find children
        tests_result = tests_gen.generate(scope, all_scopes=scopes)
        lookup_result = lookup_gen.generate(scope, all_scopes=scopes)
        architecture_result = architecture_gen.generate(scope, all_scopes=scopes)

        # Extract content
        tests_md = tests_result.content
        lookup_md = lookup_result.content
        architecture_md = architecture_result.content

        # Track statistics
        scope_path = str(scope.path)
        if tests_result.llm_response:
            stats.add_file(
                scope_path,
                "TESTS.md",
                tests_result.llm_response.tokens_used,
                tests_result.llm_response.input_tokens,
                tests_result.llm_response.output_tokens,
                tests_result.llm_response.cost_estimate,
                tests_result.llm_response.cache_read_input_tokens,
                tests_result.llm_response.cache_creation_input_tokens,
            )

        if lookup_result.llm_response:
            stats.add_file(
                scope_path,
                "LOOKUP.md",
                lookup_result.llm_response.tokens_used,
                lookup_result.llm_response.input_tokens,
                lookup_result.llm_response.output_tokens,
                lookup_result.llm_response.cost_estimate,
                lookup_result.llm_response.cache_read_input_tokens,
                lookup_result.llm_response.cache_creation_input_tokens,
            )

        if architecture_result.llm_response:
            stats.add_file(
                scope_path,
                "OBSERVED_ARCHITECTURE.md",
                architecture_result.llm_response.tokens_used,
                architecture_result.llm_response.input_tokens,
                architecture_result.llm_response.output_tokens,
                architecture_result.llm_response.cost_estimate,
                architecture_result.llm_response.cache_read_input_tokens,
                architecture_result.llm_response.cache_creation_input_tokens,
            )

        # Compute hashes
        tests_hash = compute_hash(tests_md)
        lookup_hash = compute_hash(lookup_md)
        architecture_hash = compute_hash(architecture_md)
        combined_hash = compute_combined_hash(tests_md, lookup_md, architecture_md)

        # Only skip if manifest exists AND hash unchanged
        # This ensures initial generation always creates .mdstack folders
        if old_manifest and old_manifest.content_hash == combined_hash:
            logger.info("")
            logger.info(f"⏭️  No changes for {scope.path}")
            logger.info("")
            stats.scopes_skipped += 1
            continue

        # Ensure CLAUDE.md and AGENTS.md exist
        ensure_scope_files(scope)

        # Write files
        scope.mdstack_dir.mkdir(parents=True, exist_ok=True)

        (scope.mdstack_dir / "TESTS.md").write_text(tests_md, encoding="utf-8")
        (scope.mdstack_dir / "LOOKUP.md").write_text(lookup_md, encoding="utf-8")
        architecture_file = scope.mdstack_dir / "OBSERVED_ARCHITECTURE.md"
        architecture_file.write_text(architecture_md, encoding="utf-8")

        # Save manifest
        new_manifest = Manifest.create(
            content_hash=combined_hash,
            llm_provider="anthropic",
            llm_model=llm_client.get_model_name(),
            generator_version=VERSION,
            tests_hash=tests_hash,
            lookup_hash=lookup_hash,
            architecture_hash=architecture_hash,
        )

        save_manifest(scope, new_manifest)

        total_duration = time.time() - start_time
        stats.scopes_generated += 1
        logger.info("")
        logger.info(f"✅ Generated md for {scope.path} (Total: {total_duration:.2f}s)")
        logger.info("")

    # Log summary after all scopes are processed
    stats.total_duration = time.time() - overall_start_time
    log_generation_summary(stats, stats.total_duration)

    # Format markdown files with prettier
    repo_root = find_repo_root(Path.cwd())
    if repo_root:
        _run_prettier_formatting(repo_root)
    else:
        logger.debug("Could not determine repository root, skipping prettier formatting")
