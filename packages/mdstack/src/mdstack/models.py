from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Scope:
    """A directory with CLAUDE.md that gets .mdstack/ documentation."""

    path: Path
    claude_md_path: Path
    mdstack_dir: Path
    parent_scope: "Scope | None" = None

    @staticmethod
    def create(
        path: Path,
        claude_md_path: Path,
        mdstack_dir: Path,
        parent_scope: "Scope | None" = None,
    ) -> "Scope":
        """
        Factory method to create a Scope with validation.

        Raises ValueError if paths don't exist.
        """
        if not path.exists():
            raise ValueError(f"Scope path does not exist: {path}")
        if not claude_md_path.exists():
            raise ValueError(f"CLAUDE.md does not exist: {claude_md_path}")

        return Scope(
            path=path,
            claude_md_path=claude_md_path,
            mdstack_dir=mdstack_dir,
            parent_scope=parent_scope,
        )


@dataclass(frozen=True)
class Manifest:
    """Metadata about generated documentation."""

    content_hash: str  # Combined hash of all generated docs
    generated_at: str  # ISO timestamp
    llm_provider: str  # 'anthropic'
    llm_model: str  # e.g., 'claude-3-5-sonnet-20241022'
    generator_version: str  # mdstack version

    # Individual doc hashes for selective regeneration
    tests_hash: str
    lookup_hash: str
    architecture_hash: str

    @staticmethod
    def create(
        content_hash: str,
        llm_provider: str,
        llm_model: str,
        generator_version: str,
        tests_hash: str,
        lookup_hash: str,
        architecture_hash: str,
        generated_at: str | None = None,
    ) -> "Manifest":
        """Factory method to create a Manifest."""
        if generated_at is None:
            generated_at = datetime.now().isoformat()

        return Manifest(
            content_hash=content_hash,
            generated_at=generated_at,
            llm_provider=llm_provider,
            llm_model=llm_model,
            generator_version=generator_version,
            tests_hash=tests_hash,
            lookup_hash=lookup_hash,
            architecture_hash=architecture_hash,
        )
